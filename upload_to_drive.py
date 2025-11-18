#!/usr/bin/env python3
"""
이미지를 구글 드라이브에 업로드하고 구글 시트 업데이트
"""

import os
import sys
import pickle
import io
from pathlib import Path
from typing import List, Dict, Optional
import argparse
from PIL import Image
import numpy as np

# Google APIs
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("구글 API 라이브러리를 설치해주세요:")
    print("pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)


class DriveImageUploader:
    """이미지를 구글 드라이브에 업로드하고 시트 업데이트"""

    # 시트와 드라이브 권한 모두 필요
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file'
    ]

    def __init__(self, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id
        self.sheet_service = None
        self.drive_service = None
        self.folder_id = None

    def calculate_image_stats(self, row_num: int) -> Dict:
        """이미지 비교 통계 로드"""
        try:
            # JSON 파일에서 통계 정보 읽기
            import json
            stats_path = f"googlesheet_url_results/row_{row_num}/stats.json"

            if os.path.exists(stats_path):
                with open(stats_path, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                    # 'processed' 섹션에서 외곽선 보정이 적용된 통계를 가져옴
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
        """구글 API 인증"""
        creds = None
        token_file = 'token_drive.pickle'

        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)

            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)

        self.sheet_service = build('sheets', 'v4', credentials=creds)
        self.drive_service = build('drive', 'v3', credentials=creds)
        print("✅ 구글 시트 & 드라이브 인증 성공")

    def create_public_folder(self, folder_name: str = "ImageDiff_Public"):
        """공개 폴더 생성"""
        try:
            # 폴더 생성
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            folder = self.drive_service.files().create(
                body=file_metadata,
                fields='id, webViewLink'
            ).execute()

            self.folder_id = folder.get('id')

            # 폴더를 완전 공개로 설정
            self.drive_service.permissions().create(
                fileId=self.folder_id,
                body={
                    'type': 'anyone',
                    'role': 'reader'
                }
            ).execute()

            print(f"✅ 공개 폴더 생성: {folder.get('webViewLink')}")
            return self.folder_id

        except Exception as e:
            print(f"❌ 폴더 생성 실패: {e}")
            return None

    def upload_and_get_url(self, file_path: str, file_name: str) -> Optional[str]:
        """파일 업로드 후 공개 URL 반환"""
        try:
            file_metadata = {
                'name': file_name,
                'parents': [self.folder_id] if self.folder_id else []
            }

            media = MediaFileUpload(file_path, mimetype='image/png')

            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            file_id = file.get('id')

            # 파일 공개 설정
            self.drive_service.permissions().create(
                fileId=file_id,
                body={
                    'type': 'anyone',
                    'role': 'reader'
                }
            ).execute()

            # 직접 이미지 URL (IMAGE 함수용)
            direct_url = f"https://drive.google.com/uc?export=view&id={file_id}"

            return direct_url

        except Exception as e:
            print(f"  ❌ 업로드 실패: {e}")
            return None

    def update_sheet_with_images(self, start_row: int = 3, end_row: int = 7):
        """이미지 URL을 구글 시트에 추가"""

        # 공개 폴더 생성
        if not self.folder_id:
            self.create_public_folder()

        # 이미지 업로드 및 시트 업데이트
        update_data = []

        for row_num in range(start_row, end_row + 1):
            print(f"\n[행 {row_num}] 처리 중...")

            # 로컬 이미지 파일 경로
            diff_path = f"googlesheet_url_results/row_{row_num}/diff_highlight.png"
            side_path = f"googlesheet_url_results/row_{row_num}/side_by_side.png"

            if os.path.exists(diff_path) and os.path.exists(side_path):
                # 통계 계산
                print(f"  📊 통계 계산 중...")
                stats = self.calculate_image_stats(row_num)
                diff_pct = stats.get('diff_percentage', 0)
                changed_pct = stats.get('changed_percentage', 0)

                # 드라이브에 업로드
                print(f"  ☁️ 이미지 업로드 중...")
                diff_url = self.upload_and_get_url(diff_path, f"row{row_num}_diff.png")
                side_url = self.upload_and_get_url(side_path, f"row{row_num}_comparison.png")

                if diff_url and side_url:

                    # 판정 결과
                    if diff_pct < 1:
                        status = "✅ 거의 동일"
                    elif diff_pct < 5:
                        status = "⚠️ 약간 차이"
                    else:
                        status = "❌ 큰 차이"

                    # IMAGE 함수 + 수치 데이터
                    update_data.append([
                        f'=IMAGE("{diff_url}", 1)',  # D열: 차이 강조 이미지
                        f'=IMAGE("{side_url}", 1)',  # E열: 나란히 비교 이미지
                        status,                       # F열: 판정 결과
                        diff_pct,                     # G열: 차이율 (%)
                        changed_pct,                  # H열: 변경된 픽셀 비율 (%)
                    ])
                    print(f"  ✅ 업로드 완료 (차이율: {diff_pct:.2f}%)")
                else:
                    update_data.append(['업로드 실패', '', '', '', ''])
            else:
                update_data.append(['파일 없음', '', '', '', ''])

        # 구글 시트 업데이트
        print(f"\n📝 구글 시트 D{start_row}:H{end_row} 업데이트 중...")
        update_range = f'D{start_row}:H{end_row}'

        try:
            body = {'values': update_data}
            result = self.sheet_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=update_range,
                valueInputOption='USER_ENTERED',  # 수식으로 처리
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
                                'pixelSize': 150  # 행 높이 150px
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
    parser = argparse.ArgumentParser(description='이미지를 구글 드라이브에 업로드하고 시트에 표시')
    parser.add_argument('spreadsheet_id', help='구글 시트 ID')
    parser.add_argument('--start', type=int, default=3, help='시작 행')
    parser.add_argument('--end', type=int, default=7, help='종료 행')

    args = parser.parse_args()

    uploader = DriveImageUploader(args.spreadsheet_id)

    print("🔐 구글 API 인증 중...")
    print("⚠️  처음 실행 시 구글 드라이브 권한을 요청합니다.")
    print("   '권한 허용'을 클릭해주세요.\n")

    uploader.authenticate()
    uploader.update_sheet_with_images(args.start, args.end)

    print(f"\n✨ 완료!")
    print(f"📊 구글 시트 확인: https://docs.google.com/spreadsheets/d/{args.spreadsheet_id}/edit")
    print(f"💡 D, E 열에 이미지가 표시됩니다!")

    return 0


if __name__ == '__main__':
    exit(main())