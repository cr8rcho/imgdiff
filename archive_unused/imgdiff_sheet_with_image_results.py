#!/usr/bin/env python3
"""
구글 시트 URL 이미지 비교 - 결과 이미지를 D, E 열에 표시
B, C 열의 IMAGE 함수 URL을 비교하고, 결과를 D, E 열에 IMAGE 함수로 추가
"""

import os
import sys
import pickle
import re
import requests
import tempfile
import base64
from typing import List, Dict, Optional
import argparse
from datetime import datetime
from PIL import Image
import io

# Google Sheets API
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("구글 시트 API 라이브러리를 설치해주세요:")
    print("pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

from imgdiff import ImageComparator

# 무료 이미지 호스팅 서비스 사용 (imgbb)
IMGBB_API_KEY = "YOUR_API_KEY"  # https://api.imgbb.com/ 에서 무료 키 발급


class GoogleSheetImageResult:
    """구글 시트에 이미지 결과를 표시하는 클래스"""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id
        self.service = None
        self.temp_dir = None

    def authenticate(self, credentials_file: str = 'credentials.json'):
        """구글 시트 API 인증"""
        creds = None

        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)

            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('sheets', 'v4', credentials=creds)
        print("✅ 구글 시트 API 인증 성공")

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

    def download_image(self, url: str) -> Optional[bytes]:
        """URL에서 이미지를 다운로드하여 바이트로 반환"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.content
        except:
            return None

    def upload_to_imgbb(self, image_bytes: bytes, name: str = "image") -> Optional[str]:
        """이미지를 imgbb에 업로드하고 URL 반환"""
        try:
            # imgbb API 엔드포인트
            url = "https://api.imgbb.com/1/upload"

            # 이미지를 base64로 인코딩
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            payload = {
                'key': IMGBB_API_KEY,
                'image': image_base64,
                'name': name
            }

            response = requests.post(url, data=payload)
            response.raise_for_status()

            result = response.json()
            if result['success']:
                return result['data']['url']

        except Exception as e:
            print(f"  ⚠️ imgbb 업로드 실패: {e}")

        return None

    def upload_to_temporary_service(self, image_path: str) -> Optional[str]:
        """임시 이미지 호스팅 서비스 사용 (file.io - 14일 유지)"""
        try:
            with open(image_path, 'rb') as f:
                files = {'file': f}
                response = requests.post('https://file.io', files=files)
                response.raise_for_status()

                result = response.json()
                if result.get('success'):
                    # file.io는 다운로드 링크를 제공하므로 직접 이미지 링크로 변환 필요
                    return result.get('link')
        except Exception as e:
            print(f"  ⚠️ file.io 업로드 실패: {e}")

        return None

    def create_data_url(self, image_path: str) -> str:
        """이미지를 Data URL로 변환 (작은 이미지용)"""
        try:
            with Image.open(image_path) as img:
                # 이미지 크기 축소 (시트 셀에 맞게)
                max_size = (400, 400)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # PNG로 저장
                buffer = io.BytesIO()
                img.save(buffer, format='PNG', optimize=True)
                image_bytes = buffer.getvalue()

                # Base64 인코딩
                base64_str = base64.b64encode(image_bytes).decode('utf-8')
                data_url = f"data:image/png;base64,{base64_str}"

                return data_url
        except Exception as e:
            print(f"  ⚠️ Data URL 생성 실패: {e}")
            return ""

    def process_sheet_with_images(self, start_row: int = 3, end_row: int = 10):
        """구글 시트의 이미지를 처리하고 결과를 D, E 열에 추가"""

        print(f"\n📋 B{start_row}:C{end_row} 범위 처리 중...")

        # B, C 열 데이터 읽기 (수식)
        range_name = f'B{start_row}:C{end_row}'
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueRenderOption='FORMULA'
            ).execute()

            values = result.get('values', [])

            if not values:
                print("⚠️  데이터가 없습니다.")
                return

            # 임시 디렉토리 생성
            self.temp_dir = tempfile.mkdtemp(prefix='imgdiff_')

            # 업데이트할 데이터 준비
            update_data = []

            for idx, row in enumerate(values):
                current_row = start_row + idx
                print(f"\n[행 {current_row}] 처리 중...")

                if len(row) < 2:
                    update_data.append(['', ''])  # 빈 셀
                    continue

                # URL 추출
                url1 = self.extract_url_from_image(row[0])
                url2 = self.extract_url_from_image(row[1])

                if not url1 or not url2:
                    update_data.append(['URL 없음', ''])
                    continue

                try:
                    # 이미지 다운로드
                    print(f"  📥 이미지 다운로드 중...")
                    img1_bytes = self.download_image(url1)
                    img2_bytes = self.download_image(url2)

                    if not img1_bytes or not img2_bytes:
                        update_data.append(['다운로드 실패', ''])
                        continue

                    # 임시 파일로 저장
                    img1_path = os.path.join(self.temp_dir, f'row{current_row}_img1.png')
                    img2_path = os.path.join(self.temp_dir, f'row{current_row}_img2.png')

                    with open(img1_path, 'wb') as f:
                        f.write(img1_bytes)
                    with open(img2_path, 'wb') as f:
                        f.write(img2_bytes)

                    # 이미지 비교
                    print(f"  🔍 이미지 비교 중...")
                    comparator = ImageComparator(img1_path, img2_path)
                    stats = comparator.get_statistics()

                    # 차이 이미지 생성
                    diff_img = comparator.create_diff_image('highlight')
                    diff_path = os.path.join(self.temp_dir, f'row{current_row}_diff.png')
                    diff_img.save(diff_path)

                    # 차이율 텍스트
                    diff_text = f"차이율: {stats['diff_percentage']:.2f}%"

                    # 이미지를 호스팅 서비스에 업로드
                    print(f"  ☁️ 이미지 업로드 중...")

                    # 옵션 1: Data URL 사용 (작은 이미지, 즉시 표시)
                    # 주의: 구글 시트의 IMAGE 함수는 data URL을 지원하지 않을 수 있음

                    # 옵션 2: 결과 저장 위치 생성 (로컬 서버 필요)
                    # 로컬 결과 폴더에 저장하고 나중에 웹 서버로 제공

                    # 일단 차이율과 상태만 표시
                    if stats['diff_percentage'] < 1:
                        status = "✅ 거의 동일"
                    elif stats['diff_percentage'] < 5:
                        status = "⚠️ 약간 차이"
                    else:
                        status = "❌ 큰 차이"

                    # D열: 차이율과 상태, E열: 변경 픽셀 정보
                    update_data.append([
                        f"{status}\n{diff_text}",
                        f"변경 픽셀: {stats['changed_percentage']:.2f}%"
                    ])

                    print(f"  ✅ 완료: {diff_text}")

                except Exception as e:
                    print(f"  ❌ 오류: {e}")
                    update_data.append([f'오류: {str(e)}', ''])

            # 구글 시트 업데이트 (D, E 열)
            print(f"\n📝 구글 시트 D{start_row}:E{end_row} 업데이트 중...")
            update_range = f'D{start_row}:E{end_row}'

            body = {
                'values': update_data
            }

            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=update_range,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()

            print(f"✅ 업데이트 완료: {result.get('updatedCells')}개 셀")

            # 헤더 추가 (D2, E2)
            if start_row == 3:
                header_body = {
                    'values': [['비교 결과', '상세 정보']]
                }
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range='D2:E2',
                    valueInputOption='USER_ENTERED',
                    body=header_body
                ).execute()
                print("✅ 헤더 추가 완료")

        except HttpError as err:
            print(f"❌ 오류: {err}")

        finally:
            # 임시 파일 정리
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
                print("🧹 임시 파일 정리 완료")


def setup_local_server_instruction():
    """로컬 서버 설정 안내"""
    print("""
    💡 이미지를 구글 시트에 표시하려면:

    1. 구글 드라이브 사용 (권장):
       - 구글 드라이브에 업로드 후 공유 링크 사용
       - drive.google.com에서 수동 업로드 후 링크 복사

    2. 로컬 웹 서버 사용:
       python -m http.server 8000 --directory googlesheet_url_results
       그 후 IMAGE("http://your-ip:8000/row_3/diff_highlight.png") 사용

    3. GitHub Pages 또는 Netlify 사용:
       - 결과 이미지를 GitHub에 푸시
       - GitHub Pages로 호스팅

    4. 무료 이미지 호스팅 서비스:
       - imgbb.com (API 키 필요)
       - imgur.com
       - cloudinary.com
    """)


def main():
    parser = argparse.ArgumentParser(description='구글 시트 이미지 비교 - 결과를 D, E 열에 표시')
    parser.add_argument('spreadsheet_id', help='구글 시트 ID')
    parser.add_argument('--start-row', type=int, default=3, help='시작 행 (기본값: 3)')
    parser.add_argument('--end-row', type=int, default=10, help='종료 행 (기본값: 10)')

    args = parser.parse_args()

    processor = GoogleSheetImageResult(args.spreadsheet_id)

    # 인증
    print("🔐 구글 시트 인증 중...")
    processor.authenticate()

    # 이미지 처리 및 시트 업데이트
    processor.process_sheet_with_images(args.start_row, args.end_row)

    print(f"\n✨ 완료!")
    print(f"구글 시트 확인: https://docs.google.com/spreadsheets/d/{args.spreadsheet_id}/edit")

    # 이미지 표시 안내
    print("\n" + "="*60)
    setup_local_server_instruction()

    return 0


if __name__ == '__main__':
    exit(main())