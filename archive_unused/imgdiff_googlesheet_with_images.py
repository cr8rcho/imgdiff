#!/usr/bin/env python3
"""
구글 시트 URL 기반 이미지 비교 도구 - 결과 이미지를 구글 드라이브에 업로드하여 시트에 표시
IMAGE 함수의 URL을 추출하여 이미지를 다운로드하고 비교한 후, 결과를 구글 드라이브에 업로드합니다.
"""

import os
import sys
import csv
import pickle
import re
import requests
import tempfile
import io
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import argparse
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# Google APIs
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseUpload
except ImportError:
    print("구글 API 라이브러리를 설치해주세요:")
    print("pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

from imgdiff import ImageComparator
from PIL import Image


class GoogleSheetImageUploader:
    """구글 시트와 드라이브를 연동한 이미지 비교 클래스"""

    # 구글 API 권한 범위 (시트 + 드라이브)
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file'
    ]

    def __init__(self, spreadsheet_id: str, range_name: str = 'B3:C',
                 output_dir: str = 'googlesheet_results_with_images'):
        self.spreadsheet_id = spreadsheet_id
        self.range_name = range_name
        self.output_dir = output_dir
        self.sheet_service = None
        self.drive_service = None
        self.results = []
        self.temp_dir = None
        self.drive_folder_id = None

    def authenticate(self, credentials_file: str = 'credentials.json'):
        """구글 API 인증 (시트 + 드라이브)"""
        creds = None

        # 토큰 파일 이름을 변경 (드라이브 권한 포함)
        token_file = 'token_with_drive.pickle'

        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_file):
                    print(f"❌ 인증 파일을 찾을 수 없습니다: {credentials_file}")
                    sys.exit(1)

                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)

            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)

        # 서비스 객체 생성
        self.sheet_service = build('sheets', 'v4', credentials=creds)
        self.drive_service = build('drive', 'v3', credentials=creds)
        print("✅ 구글 시트 & 드라이브 API 인증 성공")

    def create_drive_folder(self, folder_name: str = "ImageDiff_Results"):
        """구글 드라이브에 결과 폴더 생성"""
        try:
            # 폴더 메타데이터
            file_metadata = {
                'name': f'{folder_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'mimeType': 'application/vnd.google-apps.folder'
            }

            # 폴더 생성
            folder = self.drive_service.files().create(
                body=file_metadata,
                fields='id, webViewLink'
            ).execute()

            self.drive_folder_id = folder.get('id')

            # 폴더를 공개 설정 (링크가 있는 사용자 누구나)
            self.drive_service.permissions().create(
                fileId=self.drive_folder_id,
                body={
                    'type': 'anyone',
                    'role': 'reader'
                }
            ).execute()

            print(f"✅ 구글 드라이브 폴더 생성: {folder.get('webViewLink')}")
            return self.drive_folder_id

        except Exception as e:
            print(f"❌ 폴더 생성 실패: {e}")
            return None

    def upload_image_to_drive(self, image_path: str, image_name: str) -> Optional[str]:
        """이미지를 구글 드라이브에 업로드하고 공유 링크 반환"""
        try:
            # 파일 메타데이터
            file_metadata = {
                'name': image_name,
                'parents': [self.drive_folder_id] if self.drive_folder_id else []
            }

            # 파일 업로드
            with open(image_path, 'rb') as f:
                media = MediaIoBaseUpload(
                    io.BytesIO(f.read()),
                    mimetype='image/png',
                    resumable=True
                )

                file = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webContentLink'
                ).execute()

            file_id = file.get('id')

            # 파일을 공개 설정
            self.drive_service.permissions().create(
                fileId=file_id,
                body={
                    'type': 'anyone',
                    'role': 'reader'
                }
            ).execute()

            # 직접 액세스 가능한 URL 생성
            # webContentLink는 다운로드 링크이므로, 이미지 표시용 링크로 변환
            direct_link = f"https://drive.google.com/uc?export=view&id={file_id}"

            return direct_link

        except Exception as e:
            print(f"  ❌ 업로드 실패: {e}")
            return None

    def extract_url_from_image(self, cell_value: str) -> Optional[str]:
        """IMAGE 함수에서 URL 추출"""
        if not cell_value:
            return None

        patterns = [
            r'=IMAGE\s*\(\s*"([^"]+)"\s*\)',
            r"=IMAGE\s*\(\s*'([^']+)'\s*\)"
        ]

        for pattern in patterns:
            match = re.match(pattern, str(cell_value), re.IGNORECASE)
            if match:
                return match.group(1)

        if cell_value.startswith('http'):
            return cell_value

        return None

    def download_image(self, url: str, filename: str) -> Optional[str]:
        """URL에서 이미지 다운로드"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            if not self.temp_dir:
                self.temp_dir = tempfile.mkdtemp(prefix='imgdiff_')

            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)

            return filepath

        except requests.RequestException as e:
            print(f"  ❌ 다운로드 실패: {e}")
            return None

    def read_sheet_urls(self) -> List[Dict]:
        """구글 시트에서 IMAGE 함수의 URL 읽기"""
        if not self.sheet_service:
            raise Exception("먼저 authenticate() 메서드를 실행하세요.")

        try:
            result = self.sheet_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=self.range_name,
                valueRenderOption='FORMULA'
            ).execute()

            values = result.get('values', [])

            if not values:
                print('⚠️  시트에 데이터가 없습니다.')
                return []

            print(f"✅ {len(values)}개의 행을 읽었습니다.")

            # 처리할 행 수 제한 (테스트용)
            max_rows = 10  # 처음 10개만 처리
            url_pairs = []

            for idx, row in enumerate(values[:max_rows], 3):  # B3부터 시작
                if len(row) >= 2:
                    url1 = self.extract_url_from_image(row[0])
                    url2 = self.extract_url_from_image(row[1])

                    if url1 and url2:
                        url_pairs.append({
                            'row': idx,
                            'url1': url1,
                            'url2': url2,
                            'name': f"row_{idx}"
                        })

            print(f"🔗 {len(url_pairs)}개의 URL 쌍을 처리합니다.")
            return url_pairs

        except HttpError as err:
            print(f"❌ 오류 발생: {err}")
            return []

    def compare_and_upload(self, url_pairs: List[Dict]) -> List[Dict]:
        """URL 이미지 비교 후 구글 드라이브에 업로드"""
        results = []
        total = len(url_pairs)

        os.makedirs(self.output_dir, exist_ok=True)

        # 구글 드라이브 폴더 생성
        if not self.drive_folder_id:
            self.create_drive_folder()

        for idx, pair in enumerate(url_pairs, 1):
            print(f"\n[{idx}/{total}] 처리 중: 행 {pair['row']}")

            result = {
                'row': pair['row'],
                'name': pair['name'],
                'status': 'pending'
            }

            try:
                # 이미지 다운로드
                print(f"  📥 이미지 다운로드 중...")
                img1_path = self.download_image(pair['url1'], f"{pair['name']}_img1.png")
                img2_path = self.download_image(pair['url2'], f"{pair['name']}_img2.png")

                if not img1_path or not img2_path:
                    raise Exception("이미지 다운로드 실패")

                # 이미지 비교
                print(f"  🔍 이미지 비교 중...")
                comparator = ImageComparator(img1_path, img2_path)
                stats = comparator.get_statistics()

                # 차이 이미지 생성
                row_dir = os.path.join(self.output_dir, pair['name'])
                os.makedirs(row_dir, exist_ok=True)

                # 차이 강조 이미지
                diff_img = comparator.create_diff_image('highlight')
                diff_path = os.path.join(row_dir, 'diff_highlight.png')
                diff_img.save(diff_path)

                # 나란히 비교 이미지
                side_by_side_path = os.path.join(row_dir, 'side_by_side.png')
                comparator.create_side_by_side_comparison(side_by_side_path)

                # 구글 드라이브에 업로드
                print(f"  ☁️  구글 드라이브에 업로드 중...")
                diff_url = self.upload_image_to_drive(
                    diff_path,
                    f"row_{pair['row']}_diff.png"
                )

                side_by_side_url = self.upload_image_to_drive(
                    side_by_side_path,
                    f"row_{pair['row']}_comparison.png"
                )

                result.update({
                    'status': 'success',
                    'diff_percentage': stats['diff_percentage'],
                    'changed_percentage': stats['changed_percentage'],
                    'diff_image_url': diff_url,
                    'comparison_image_url': side_by_side_url
                })

                print(f"  ✅ 완료: 차이율 {stats['diff_percentage']:.2f}%")

            except Exception as e:
                result.update({
                    'status': 'error',
                    'error_message': str(e)
                })
                print(f"  ❌ 실패: {e}")

            results.append(result)

        self.results = results
        return results

    def update_sheet_with_images(self, start_column: str = 'D'):
        """구글 시트에 결과와 이미지 링크 업데이트"""
        if not self.sheet_service or not self.results:
            return

        update_values = []
        for result in self.results:
            if result['status'] == 'success':
                # IMAGE 함수로 이미지 표시
                diff_image_formula = f'=IMAGE("{result["diff_image_url"]}", 1)' if result.get('diff_image_url') else ''
                comparison_image_formula = f'=IMAGE("{result["comparison_image_url"]}", 1)' if result.get('comparison_image_url') else ''

                row_data = [
                    '성공',
                    f"{result['diff_percentage']:.2f}%",
                    f"{result['changed_percentage']:.2f}%",
                    diff_image_formula,  # 차이 이미지
                    comparison_image_formula,  # 비교 이미지
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            else:
                row_data = [
                    '실패',
                    '',
                    '',
                    '',
                    '',
                    result.get('error_message', '')
                ]
            update_values.append(row_data)

        if self.results:
            first_row = self.results[0]['row']
            last_row = first_row + len(self.results) - 1
            update_range = f"{start_column}{first_row}:{chr(ord(start_column)+5)}{last_row}"

            try:
                body = {'values': update_values}
                result = self.sheet_service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=update_range,
                    valueInputOption='USER_ENTERED',  # 수식으로 입력
                    body=body
                ).execute()

                print(f"✅ 구글 시트 업데이트 완료: {result.get('updatedCells')}개 셀")

                # 헤더 추가
                if first_row > 1:
                    header_range = f"{start_column}{first_row-1}:{chr(ord(start_column)+5)}{first_row-1}"
                    header_body = {
                        'values': [['상태', '차이율', '변경픽셀', '차이 이미지', '비교 이미지', '처리시간']]
                    }
                    self.sheet_service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=header_range,
                        valueInputOption='USER_ENTERED',
                        body=header_body
                    ).execute()

                # 행 높이 조정 (이미지를 위해)
                requests_body = {
                    'requests': [
                        {
                            'updateDimensionProperties': {
                                'range': {
                                    'sheetId': 0,
                                    'dimension': 'ROWS',
                                    'startIndex': first_row - 1,
                                    'endIndex': last_row
                                },
                                'properties': {
                                    'pixelSize': 200  # 행 높이를 200px로 설정
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

                print("✅ 행 높이 조정 완료 (이미지 표시를 위해)")

            except HttpError as err:
                print(f"❌ 시트 업데이트 실패: {err}")

    def cleanup_temp_files(self):
        """임시 파일 정리"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            print("🧹 임시 파일 정리 완료")


def main():
    parser = argparse.ArgumentParser(description='구글 시트 이미지 비교 - 결과를 시트에 표시')
    parser.add_argument('spreadsheet_id', help='구글 시트 ID')
    parser.add_argument('--range', default='B3:C',
                       help='읽을 범위 (기본값: B3:C)')
    parser.add_argument('--max-rows', type=int, default=10,
                       help='처리할 최대 행 수 (기본값: 10)')

    args = parser.parse_args()

    uploader = GoogleSheetImageUploader(args.spreadsheet_id, args.range)

    try:
        # 인증
        print("🔐 구글 API 인증 중...")
        uploader.authenticate()

        # URL 읽기
        print("\n📋 구글 시트에서 데이터 읽기...")
        url_pairs = uploader.read_sheet_urls()

        if not url_pairs:
            print("⚠️  처리할 URL 쌍이 없습니다.")
            return 1

        # 이미지 비교 및 업로드
        print("\n🚀 이미지 처리 시작...")
        uploader.compare_and_upload(url_pairs)

        # 구글 시트 업데이트
        print("\n📝 구글 시트 업데이트...")
        uploader.update_sheet_with_images()

        print("\n✨ 완료!")
        print(f"구글 시트에서 결과를 확인하세요:")
        print(f"https://docs.google.com/spreadsheets/d/{args.spreadsheet_id}/edit")

    finally:
        # 임시 파일 정리
        uploader.cleanup_temp_files()

    return 0


if __name__ == '__main__':
    exit(main())