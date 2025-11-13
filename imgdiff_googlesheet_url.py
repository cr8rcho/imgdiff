#!/usr/bin/env python3
"""
구글 시트 URL 기반 이미지 비교 도구
IMAGE 함수의 URL을 추출하여 이미지를 다운로드하고 비교합니다.
"""

import os
import sys
import csv
import pickle
import re
import requests
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import argparse
from datetime import datetime
from urllib.parse import urlparse, parse_qs

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


class GoogleSheetURLImageComparator:
    """구글 시트의 IMAGE 함수 URL을 사용한 이미지 비교 클래스"""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, spreadsheet_id: str, range_name: str = 'B3:C',
                 output_dir: str = 'googlesheet_url_results',
                 threshold: int = 20, morphology_kernel_size: int = 3,
                 blur_kernel_size: int = 0):
        self.spreadsheet_id = spreadsheet_id
        self.range_name = range_name
        self.output_dir = output_dir
        self.threshold = threshold
        self.morphology_kernel_size = morphology_kernel_size
        self.blur_kernel_size = blur_kernel_size
        self.service = None
        self.results = []
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
                if not os.path.exists(credentials_file):
                    print(f"❌ 인증 파일을 찾을 수 없습니다: {credentials_file}")
                    sys.exit(1)

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

        # =IMAGE("URL") 또는 =IMAGE('URL') 패턴
        patterns = [
            r'=IMAGE\s*\(\s*"([^"]+)"\s*\)',
            r"=IMAGE\s*\(\s*'([^']+)'\s*\)"
        ]

        for pattern in patterns:
            match = re.match(pattern, str(cell_value), re.IGNORECASE)
            if match:
                return match.group(1)

        # IMAGE 함수가 아니면 일반 텍스트로 처리 (URL인 경우)
        if cell_value.startswith('http'):
            return cell_value

        return None

    def download_image(self, url: str, filename: str) -> Optional[str]:
        """URL에서 이미지 다운로드"""
        try:
            print(f"  📥 다운로드 중: {filename}")

            # 헤더 설정 (User-Agent 추가)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # 임시 디렉토리에 저장
            if not self.temp_dir:
                self.temp_dir = tempfile.mkdtemp(prefix='imgdiff_')

            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)

            print(f"  ✅ 다운로드 완료: {filename}")
            return filepath

        except requests.RequestException as e:
            print(f"  ❌ 다운로드 실패: {e}")
            return None

    def read_sheet_urls(self) -> List[Dict]:
        """구글 시트에서 IMAGE 함수의 URL 읽기"""
        if not self.service:
            raise Exception("먼저 authenticate() 메서드를 실행하세요.")

        try:
            # 수식 가져오기 (IMAGE 함수 포함)
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=self.range_name,
                valueRenderOption='FORMULA'  # 수식 그대로 가져오기
            ).execute()

            values = result.get('values', [])

            if not values:
                print('⚠️  시트에 데이터가 없습니다.')
                return []

            print(f"✅ {len(values)}개의 행을 읽었습니다.")

            url_pairs = []
            for idx, row in enumerate(values, 3):  # B3부터 시작
                if len(row) >= 2:
                    url1 = self.extract_url_from_image(row[0])
                    url2 = self.extract_url_from_image(row[1])

                    if url1 and url2:
                        # URL에서 파일명 추출
                        name1 = self.extract_filename_from_url(url1)
                        name2 = self.extract_filename_from_url(url2)

                        url_pairs.append({
                            'row': idx,
                            'url1': url1,
                            'url2': url2,
                            'name1': name1,
                            'name2': name2,
                            'name': f"{name1}_vs_{name2}"
                        })

            print(f"🔗 {len(url_pairs)}개의 URL 쌍을 발견했습니다.")
            return url_pairs

        except HttpError as err:
            print(f"❌ 오류 발생: {err}")
            return []

    def extract_filename_from_url(self, url: str) -> str:
        """URL에서 파일명 추출"""
        parsed = urlparse(url)
        path = parsed.path
        filename = os.path.basename(path)

        # 파일명이 없으면 URL의 일부를 사용
        if not filename or filename == '/':
            # 경로의 마지막 두 부분을 조합
            parts = [p for p in path.split('/') if p]
            if len(parts) >= 2:
                filename = f"{parts[-2]}_{parts[-1]}"
            else:
                filename = "image"

        # 확장자가 없으면 .png 추가
        if '.' not in filename:
            filename += '.png'

        return filename

    def compare_url_images(self, url_pairs: List[Dict]) -> List[Dict]:
        """URL 이미지 쌍을 다운로드하고 비교"""
        results = []
        total = len(url_pairs)

        os.makedirs(self.output_dir, exist_ok=True)

        for idx, pair in enumerate(url_pairs, 1):
            print(f"\n[{idx}/{total}] 비교 중: 행 {pair['row']}")
            print(f"  URL1: {pair['url1'][:80]}...")
            print(f"  URL2: {pair['url2'][:80]}...")

            result = {
                'row': pair['row'],
                'name': pair['name'],
                'url1': pair['url1'],
                'url2': pair['url2'],
                'status': 'pending'
            }

            try:
                # 이미지 다운로드
                img1_path = self.download_image(pair['url1'], f"row{pair['row']}_img1_{pair['name1']}")
                img2_path = self.download_image(pair['url2'], f"row{pair['row']}_img2_{pair['name2']}")

                if not img1_path or not img2_path:
                    raise Exception("이미지 다운로드 실패")

                # 이미지 비교
                comparator = ImageComparator(img1_path, img2_path)

                # 원본 통계 (필터링 없음)
                stats_original = comparator.get_statistics(threshold=self.threshold)

                # 처리된 통계 (OpenCV 필터링 적용 - 실제 표시되는 것과 일치)
                stats_processed = comparator.get_processed_statistics(
                    threshold=self.threshold,
                    morphology_kernel_size=self.morphology_kernel_size,
                    blur_kernel_size=self.blur_kernel_size
                )

                # result에는 처리된 통계 사용 (실제 이미지와 일치)
                result.update({
                    'status': 'success',
                    'diff_percentage': stats_processed['diff_percentage'],
                    'changed_pixels': stats_processed['changed_pixels'],
                    'changed_percentage': stats_processed['changed_percentage'],
                    'image_size': comparator.img1.size
                })

                # 결과 저장
                row_dir = os.path.join(self.output_dir, f"row_{pair['row']}")
                os.makedirs(row_dir, exist_ok=True)

                # 차이 이미지 저장 (형태학적 연산 적용)
                diff_img = comparator.create_diff_image(
                    'highlight',
                    threshold=self.threshold,
                    morphology_kernel_size=self.morphology_kernel_size,
                    blur_kernel_size=self.blur_kernel_size
                )
                diff_img.save(os.path.join(row_dir, 'diff_highlight.png'))

                # 나란히 비교 이미지 저장 (새로운 파라미터 적용)
                side_by_side_path = os.path.join(row_dir, 'side_by_side.png')
                comparator.create_side_by_side_comparison(
                    side_by_side_path,
                    threshold=self.threshold,
                    morphology_kernel_size=self.morphology_kernel_size,
                    blur_kernel_size=self.blur_kernel_size
                )

                # 통계 정보 JSON으로 저장
                import json
                import numpy as np

                # NumPy 타입을 Python 기본 타입으로 변환
                def convert_numpy(obj):
                    if isinstance(obj, np.integer):
                        return int(obj)
                    elif isinstance(obj, np.floating):
                        return float(obj)
                    elif isinstance(obj, np.ndarray):
                        return obj.tolist()
                    elif isinstance(obj, dict):
                        return {k: convert_numpy(v) for k, v in obj.items()}
                    elif isinstance(obj, (list, tuple)):
                        return [convert_numpy(item) for item in obj]
                    return obj

                # 두 가지 통계를 모두 저장
                combined_stats = {
                    'original': convert_numpy(stats_original),
                    'processed': convert_numpy(stats_processed),
                    'note': 'The "processed" statistics match the red highlighted areas in diff_highlight.png. "original" statistics are based on raw pixel differences without filtering.'
                }

                stats_path = os.path.join(row_dir, 'stats.json')
                with open(stats_path, 'w', encoding='utf-8') as f:
                    json.dump(combined_stats, f, indent=2, ensure_ascii=False)

                print(f"  ✅ 성공: 차이율 {stats_processed['diff_percentage']:.2f}% (처리 후: {stats_processed['changed_percentage']:.2f}%)")

            except Exception as e:
                result.update({
                    'status': 'error',
                    'error_message': str(e)
                })
                print(f"  ❌ 실패: {e}")

            results.append(result)

        self.results = results
        return results

    def update_sheet_results(self, start_column: str = 'D', start_row: int = 3):
        """비교 결과를 구글 시트에 업데이트"""
        if not self.service or not self.results:
            return

        update_values = []
        for result in self.results:
            if result['status'] == 'success':
                row_data = [
                    '성공',
                    f"{result['diff_percentage']:.2f}%",
                    f"{result['changed_percentage']:.2f}%",
                    f"{result.get('image_size', '')}",
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            else:
                row_data = [
                    '실패',
                    '',
                    '',
                    result.get('error_message', ''),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            update_values.append(row_data)

        # 첫 번째 결과의 행 번호 기준으로 업데이트
        if self.results:
            first_row = self.results[0]['row']
            last_row = first_row + len(self.results) - 1
            update_range = f"{start_column}{first_row}:{chr(ord(start_column)+4)}{last_row}"

            try:
                body = {'values': update_values}
                result = self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=update_range,
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()

                print(f"✅ 구글 시트 업데이트 완료: {result.get('updatedCells')}개 셀")

                # 헤더 추가
                if first_row > 1:
                    header_range = f"{start_column}{first_row-1}:{chr(ord(start_column)+4)}{first_row-1}"
                    header_body = {
                        'values': [['상태', '차이율', '변경픽셀', '비고', '처리시간']]
                    }
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=header_range,
                        valueInputOption='USER_ENTERED',
                        body=header_body
                    ).execute()

            except HttpError as err:
                print(f"❌ 시트 업데이트 실패: {err}")

    def cleanup_temp_files(self):
        """임시 파일 정리"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            print("🧹 임시 파일 정리 완료")

    def generate_report(self):
        """결과 리포트 생성"""
        if not self.results:
            return

        print("\n" + "="*60)
        print("비교 완료 요약")
        print("="*60)

        success = sum(1 for r in self.results if r['status'] == 'success')
        error = sum(1 for r in self.results if r['status'] == 'error')

        print(f"전체: {len(self.results)}개")
        print(f"성공: {success}개")
        print(f"실패: {error}개")

        if success > 0:
            avg_diff = sum(r['diff_percentage'] for r in self.results if r['status'] == 'success') / success
            print(f"평균 차이율: {avg_diff:.2f}%")

        # CSV 저장
        csv_path = os.path.join(self.output_dir, 'url_results.csv')
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['row', 'status', 'diff_percentage', 'changed_percentage', 'url1', 'url2']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in self.results:
                writer.writerow({
                    'row': result.get('row'),
                    'status': result.get('status'),
                    'diff_percentage': result.get('diff_percentage', ''),
                    'changed_percentage': result.get('changed_percentage', ''),
                    'url1': result.get('url1', ''),
                    'url2': result.get('url2', '')
                })

        print(f"\n📁 결과 저장 위치: {self.output_dir}")


def main():
    parser = argparse.ArgumentParser(description='구글 시트 URL 기반 이미지 비교')
    parser.add_argument('spreadsheet_id', help='구글 시트 ID')
    parser.add_argument('--range', default='B3:C',
                       help='읽을 범위 (기본값: B3:C)')
    parser.add_argument('--output-dir', default='googlesheet_url_results',
                       help='결과 저장 디렉토리')
    parser.add_argument('--update-sheet', action='store_true',
                       help='결과를 구글 시트에 업데이트')
    parser.add_argument('--threshold', type=int, default=30,
                       help='차이 감지 임계값 (기본값: 30, 높을수록 민감도 낮음)')
    parser.add_argument('--morphology-kernel-size', type=int, default=3,
                       help='형태학적 연산 커널 크기 (기본값: 3, 0이면 비활성화)')
    parser.add_argument('--blur-kernel-size', type=int, default=0,
                       help='가우시안 블러 커널 크기 (기본값: 0, 0이면 비활성화)')

    args = parser.parse_args()

    comparator = GoogleSheetURLImageComparator(
        args.spreadsheet_id,
        args.range,
        args.output_dir,
        threshold=args.threshold,
        morphology_kernel_size=args.morphology_kernel_size,
        blur_kernel_size=args.blur_kernel_size
    )

    try:
        # 인증
        comparator.authenticate()

        # URL 읽기
        url_pairs = comparator.read_sheet_urls()

        if not url_pairs:
            print("⚠️  처리할 URL 쌍이 없습니다.")
            return 1

        # 이미지 다운로드 및 비교
        comparator.compare_url_images(url_pairs)

        # 리포트 생성
        comparator.generate_report()

        # 구글 시트 업데이트
        if args.update_sheet:
            comparator.update_sheet_results()

    finally:
        # 임시 파일 정리
        comparator.cleanup_temp_files()

    return 0


if __name__ == '__main__':
    exit(main())