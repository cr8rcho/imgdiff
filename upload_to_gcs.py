#!/usr/bin/env python3
"""
이미지를 Google Cloud Storage에 업로드하고 구글 시트 업데이트
(Google Drive보다 훨씬 빠른 병렬 업로드)
"""

import os
import sys
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Google APIs
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.cloud import storage
except ImportError:
    print("구글 API 라이브러리를 설치해주세요:")
    print("pip install google-cloud-storage google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)


class GCSImageUploader:
    """이미지를 Google Cloud Storage에 업로드하고 시트 업데이트"""

    # 시트 + Cloud Storage 권한 필요
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/devstorage.full_control'
    ]

    def __init__(self, spreadsheet_id: str, bucket_name: str):
        self.spreadsheet_id = spreadsheet_id
        self.bucket_name = bucket_name
        self.folder_prefix = f"imgdiff_{spreadsheet_id}"
        self.sheet_service = None
        self.storage_client = None
        self.bucket = None
        self.creds = None

    def calculate_image_stats(self, row_num: int) -> Dict:
        """이미지 비교 통계 로드"""
        try:
            import json
            stats_path = f"googlesheet_url_results/row_{row_num}/stats.json"

            if os.path.exists(stats_path):
                with open(stats_path, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                    processed = stats.get('processed', {})
                    return {
                        'diff_percentage': processed.get('diff_percentage', 0),
                        'changed_percentage': processed.get('changed_percentage', 0)
                    }
            else:
                print(f"  ⚠️ stats.json 파일이 없습니다: {stats_path}")
                return {'diff_percentage': 0, 'changed_percentage': 0}
        except Exception as e:
            print(f"  ⚠️ 통계 로드 실패: {e}")
            return {'diff_percentage': 0, 'changed_percentage': 0}

    def authenticate(self):
        """구글 API 인증 (시트 + Cloud Storage)"""
        token_file = 'token_gcs.pickle'

        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                self.creds = flow.run_local_server(port=0)

            with open(token_file, 'wb') as token:
                pickle.dump(self.creds, token)

        # 시트 서비스 초기화
        self.sheet_service = build('sheets', 'v4', credentials=self.creds)
        print("✅ 구글 시트 API 인증 성공")

        # GCS 클라이언트 초기화
        try:
            # OAuth credentials에서 프로젝트 ID 가져오기
            import json
            with open('credentials.json', 'r') as f:
                cred_data = json.load(f)
                if 'installed' in cred_data:
                    project_id = cred_data['installed'].get('project_id')
                elif 'web' in cred_data:
                    project_id = cred_data['web'].get('project_id')
                else:
                    project_id = None

            if not project_id:
                # credentials.json에서 프로젝트 ID를 찾을 수 없으면 사용자에게 입력 요청
                print("\n⚠️ credentials.json에서 프로젝트 ID를 찾을 수 없습니다.")
                print("Google Cloud Console에서 프로젝트 ID를 확인하세요:")
                print("https://console.cloud.google.com/")
                project_id = input("프로젝트 ID를 입력하세요: ").strip()

            self.storage_client = storage.Client(project=project_id, credentials=self.creds)
            self.bucket = self.storage_client.bucket(self.bucket_name)
            print(f"✅ GCS 프로젝트 연결 성공: {project_id}")
            print(f"✅ GCS 버킷 연결 성공: {self.bucket_name}")
        except Exception as e:
            print(f"❌ GCS 인증 실패: {e}")
            print("\n🔧 해결 방법:")
            print("1. Google Cloud Console에서 프로젝트 확인")
            print("2. Cloud Storage API 활성화")
            print("3. 버킷이 존재하지 않으면 자동 생성됩니다")
            sys.exit(1)

    def create_public_bucket(self):
        """공개 버킷 생성 (이미 존재하면 스킵)"""
        try:
            if not self.bucket.exists():
                self.bucket = self.storage_client.create_bucket(
                    self.bucket_name,
                    location='asia-northeast3'  # 서울 리전
                )
                print(f"✅ 버킷 생성: {self.bucket_name}")

            # 버킷을 공개로 설정
            policy = self.bucket.get_iam_policy(requested_policy_version=3)
            policy.bindings.append({
                "role": "roles/storage.objectViewer",
                "members": {"allUsers"}
            })
            self.bucket.set_iam_policy(policy)
            print(f"✅ 버킷 공개 설정 완료")

        except Exception as e:
            print(f"⚠️ 버킷 설정: {e} (이미 존재할 수 있음)")

    def upload_to_gcs(self, file_path: str, blob_name: str) -> Optional[str]:
        """GCS에 파일 업로드 후 공개 URL 반환"""
        try:
            blob = self.bucket.blob(blob_name)
            blob.upload_from_filename(file_path, content_type='image/png')

            # 공개 URL 생성
            public_url = f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"
            return public_url

        except Exception as e:
            print(f"  ❌ 업로드 실패 ({blob_name}): {e}")
            return None

    def process_single_row(self, row_num: int) -> Tuple[int, List]:
        """단일 행 처리 (병렬 처리용)"""
        print(f"\n[행 {row_num}] 처리 중...")

        # 로컬 이미지 파일 경로
        diff_path = f"googlesheet_url_results/row_{row_num}/diff_highlight.png"
        side_path = f"googlesheet_url_results/row_{row_num}/side_by_side.png"

        if not os.path.exists(diff_path) or not os.path.exists(side_path):
            return (row_num, ['파일 없음', '', '', '', ''])

        try:
            # 통계 계산
            stats = self.calculate_image_stats(row_num)
            diff_pct = stats.get('diff_percentage', 0)
            changed_pct = stats.get('changed_percentage', 0)

            # GCS에 업로드 (훨씬 빠름!)
            print(f"  ☁️ GCS 업로드 중...")
            diff_url = self.upload_to_gcs(diff_path, f"{self.folder_prefix}/row{row_num}_diff.png")
            side_url = self.upload_to_gcs(side_path, f"{self.folder_prefix}/row{row_num}_comparison.png")

            if not diff_url or not side_url:
                return (row_num, ['업로드 실패', '', '', '', ''])

            # 판정 결과
            if diff_pct < 1:
                status = "✅ 거의 동일"
            elif diff_pct < 5:
                status = "⚠️ 약간 차이"
            else:
                status = "❌ 큰 차이"

            # IMAGE 함수 + 수치 데이터
            row_data = [
                f'=IMAGE("{diff_url}", 1)',  # D열: 차이 강조 이미지
                f'=IMAGE("{side_url}", 1)',  # E열: 나란히 비교 이미지
                status,                       # F열: 판정 결과
                diff_pct,                     # G열: 차이율 (%)
                changed_pct,                  # H열: 변경된 픽셀 비율 (%)
            ]
            print(f"  ✅ 업로드 완료 (차이율: {diff_pct:.2f}%)")
            return (row_num, row_data)

        except Exception as e:
            print(f"  ❌ 처리 실패: {e}")
            return (row_num, ['처리 실패', '', '', '', ''])

    def update_sheet_with_images(self, start_row: int = 3, end_row: int = 7, max_workers: int = 10):
        """이미지 URL을 구글 시트에 추가 (병렬 처리)"""

        print(f"\n🚀 병렬 업로드 시작 (동시 처리: {max_workers}개)")

        # 병렬로 이미지 업로드
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 모든 행에 대해 작업 제출
            future_to_row = {
                executor.submit(self.process_single_row, row_num): row_num
                for row_num in range(start_row, end_row + 1)
            }

            # 완료된 작업부터 처리
            for future in as_completed(future_to_row):
                row_num, row_data = future.result()
                results[row_num] = row_data

        # 행 번호 순서대로 정렬
        update_data = [results[row_num] for row_num in range(start_row, end_row + 1)]

        # 구글 시트 업데이트
        print(f"\n📝 구글 시트 D{start_row}:H{end_row} 업데이트 중...")
        update_range = f'D{start_row}:H{end_row}'

        try:
            body = {'values': update_data}
            result = self.sheet_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=update_range,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()

            print(f"✅ 시트 업데이트 완료: {result.get('updatedCells')}개 셀")

            # 행 높이 조정 (이미지 표시용)
            requests_body = {
                'requests': [
                    {
                        'updateDimensionProperties': {
                            'range': {
                                'sheetId': 0,
                                'dimension': 'ROWS',
                                'startIndex': start_row - 1,
                                'endIndex': end_row
                            },
                            'properties': {
                                'pixelSize': 150
                            },
                            'fields': 'pixelSize'
                        }
                    }
                ]
            }

            self.sheet_service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=requests_body
            ).execute()

            print("✅ 행 높이 조정 완료")

            # 헤더 추가 (D2:H2)
            if start_row == 3:
                header_body = {
                    'values': [['차이 강조', '나란히 비교', '판정', '차이율 (%)', '변경 픽셀 (%)']]
                }
                self.sheet_service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range='D2:H2',
                    valueInputOption='USER_ENTERED',
                    body=header_body
                ).execute()
                print("✅ 헤더 추가 완료")

        except HttpError as err:
            print(f"❌ 시트 업데이트 실패: {err}")


def main():
    parser = argparse.ArgumentParser(description='이미지를 GCS에 업로드하고 시트에 표시 (고속 병렬 처리)')
    parser.add_argument('spreadsheet_id', help='구글 시트 ID')
    parser.add_argument('--bucket', default='imgdiff-results', help='GCS 버킷 이름 (기본값: imgdiff-results)')
    parser.add_argument('--start', type=int, default=3, help='시작 행')
    parser.add_argument('--end', type=int, default=7, help='종료 행')
    parser.add_argument('--workers', type=int, default=10, help='동시 업로드 수 (기본값: 10)')

    args = parser.parse_args()

    uploader = GCSImageUploader(args.spreadsheet_id, args.bucket)

    print("🔐 인증 중...")
    uploader.authenticate()
    uploader.create_public_bucket()

    uploader.update_sheet_with_images(args.start, args.end, args.workers)

    print(f"\n✨ 완료!")
    print(f"📊 구글 시트 확인: https://docs.google.com/spreadsheets/d/{args.spreadsheet_id}/edit")
    print(f"💡 GCS 버킷: https://console.cloud.google.com/storage/browser/{args.bucket}")
    print(f"📁 GCS 폴더: https://console.cloud.google.com/storage/browser/{args.bucket}/imgdiff_{args.spreadsheet_id}")

    return 0


if __name__ == '__main__':
    exit(main())
