#!/usr/bin/env python3
"""
구글 시트 연동 이미지 비교 도구
구글 시트에서 이미지 경로를 읽어와 자동으로 비교하고 결과를 업데이트합니다.
"""

import os
import sys
import csv
import pickle
from pathlib import Path
from typing import List, Dict, Optional
import argparse
from datetime import datetime

# Google Sheets API를 위한 라이브러리
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


class GoogleSheetImageComparator:
    """구글 시트와 연동하여 이미지를 비교하는 클래스"""

    # 구글 시트 API 권한 범위
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, spreadsheet_id: str, range_name: str = 'B3:C',
                 output_dir: str = 'googlesheet_comparison_results'):
        """
        초기화

        Args:
            spreadsheet_id: 구글 시트 ID
            range_name: 읽을 범위 (기본값: A:B)
            output_dir: 결과 저장 디렉토리
        """
        self.spreadsheet_id = spreadsheet_id
        self.range_name = range_name
        self.output_dir = output_dir
        self.service = None
        self.results = []

    def authenticate(self, credentials_file: str = 'credentials.json'):
        """
        구글 시트 API 인증

        Args:
            credentials_file: 인증 정보 파일 경로
        """
        creds = None

        # 토큰 파일이 있으면 로드
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # 유효한 인증이 없으면 새로 생성
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_file):
                    print(f"❌ 인증 파일을 찾을 수 없습니다: {credentials_file}")
                    print("\n구글 클라우드 콘솔에서 credentials.json 파일을 다운로드하세요:")
                    print("1. https://console.cloud.google.com 접속")
                    print("2. 프로젝트 생성/선택")
                    print("3. API 및 서비스 > 사용자 인증 정보")
                    print("4. OAuth 2.0 클라이언트 ID 생성")
                    print("5. credentials.json 다운로드")
                    sys.exit(1)

                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)

            # 다음 실행을 위해 토큰 저장
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        # 서비스 객체 생성
        self.service = build('sheets', 'v4', credentials=creds)
        print("✅ 구글 시트 API 인증 성공")

    def read_sheet_data(self) -> List[List[str]]:
        """
        구글 시트에서 데이터를 읽어옵니다.

        Returns:
            시트 데이터 (2차원 리스트)
        """
        if not self.service:
            raise Exception("먼저 authenticate() 메서드를 실행하세요.")

        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=self.range_name
            ).execute()

            values = result.get('values', [])

            if not values:
                print('⚠️  시트에 데이터가 없습니다.')
                return []

            print(f"✅ {len(values)}개의 행을 읽었습니다.")
            return values

        except HttpError as err:
            print(f"❌ 오류 발생: {err}")
            return []

    def update_sheet_results(self, start_column: str = 'D', start_row: int = 3):
        """
        비교 결과를 구글 시트에 업데이트합니다.

        Args:
            start_column: 결과를 입력할 시작 열 (기본값: D)
            start_row: 결과를 입력할 시작 행 (기본값: 3)
        """
        if not self.service or not self.results:
            return

        # 결과 데이터 준비
        update_values = []
        for result in self.results:
            row_data = []
            if result['status'] == 'success':
                row_data = [
                    '성공',
                    f"{result['diff_percentage']:.2f}%",
                    f"{result['changed_percentage']:.2f}%",
                    result.get('image_size', ''),
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

        # 업데이트 범위 계산
        update_range = f"{start_column}{start_row}:{chr(ord(start_column)+4)}{len(self.results)+start_row-1}"

        try:
            # 시트 업데이트
            body = {
                'values': update_values
            }
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=update_range,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()

            print(f"✅ 구글 시트 업데이트 완료: {result.get('updatedCells')}개 셀")

            # 헤더 추가 (시작 행의 위 행에 추가)
            if start_row > 1:
                header_range = f"{start_column}{start_row-1}:{chr(ord(start_column)+4)}{start_row-1}"
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

    def compare_from_sheet(self):
        """구글 시트의 데이터를 기반으로 이미지를 비교합니다."""
        # 시트 데이터 읽기
        sheet_data = self.read_sheet_data()

        if not sheet_data:
            return

        # B3:C부터 시작하므로 헤더는 이미 제외됨
        # 헤더가 있는지 확인 (선택사항)
        if sheet_data and len(sheet_data[0]) > 0:
            first_cell = str(sheet_data[0][0]).lower()
            if first_cell in ['image1', 'path1', '이미지1', 'image', 'path']:
                sheet_data = sheet_data[1:]

        # 출력 디렉토리 생성
        os.makedirs(self.output_dir, exist_ok=True)

        # 각 행의 이미지 비교
        total = len(sheet_data)
        for idx, row in enumerate(sheet_data, 1):
            if len(row) < 2:
                print(f"⚠️  Row {idx}: 불완전한 데이터")
                continue

            image1_path = row[0].strip()
            image2_path = row[1].strip()
            name = row[2].strip() if len(row) > 2 else f"Row_{idx}"

            print(f"\n[{idx}/{total}] 비교 중: {name}")
            print(f"  이미지 1: {image1_path}")
            print(f"  이미지 2: {image2_path}")

            result = {
                'row_number': idx,
                'name': name,
                'image1': image1_path,
                'image2': image2_path,
                'status': 'pending'
            }

            try:
                # 이미지 비교
                comparator = ImageComparator(image1_path, image2_path)
                stats = comparator.get_statistics()

                result.update({
                    'status': 'success',
                    'diff_percentage': stats['diff_percentage'],
                    'changed_percentage': stats['changed_percentage'],
                    'image_size': str(comparator.img1.size)
                })

                # 결과 저장
                row_dir = os.path.join(self.output_dir, f"row_{idx}_{name.replace(' ', '_')}")
                os.makedirs(row_dir, exist_ok=True)

                diff_img = comparator.create_diff_image('highlight')
                diff_img.save(os.path.join(row_dir, 'diff.png'))

                print(f"  ✅ 성공: 차이율 {stats['diff_percentage']:.2f}%")

            except Exception as e:
                result.update({
                    'status': 'error',
                    'error_message': str(e)
                })
                print(f"  ❌ 실패: {e}")

            self.results.append(result)

        # 결과 요약
        self._print_summary()

    def _print_summary(self):
        """결과 요약을 출력합니다."""
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

    def export_to_csv(self, filename: str = None):
        """결과를 CSV 파일로 내보냅니다."""
        if not filename:
            filename = os.path.join(self.output_dir, 'sheet_results.csv')

        with open(filename, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['row_number', 'name', 'image1', 'image2',
                         'status', 'diff_percentage', 'changed_percentage']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in self.results:
                writer.writerow({
                    'row_number': result.get('row_number'),
                    'name': result.get('name'),
                    'image1': result.get('image1'),
                    'image2': result.get('image2'),
                    'status': result.get('status'),
                    'diff_percentage': result.get('diff_percentage', ''),
                    'changed_percentage': result.get('changed_percentage', '')
                })

        print(f"📁 CSV 결과 저장: {filename}")


def main():
    parser = argparse.ArgumentParser(description='구글 시트 연동 이미지 비교')
    parser.add_argument('spreadsheet_id', help='구글 시트 ID')
    parser.add_argument('--range', default='B3:C',
                       help='읽을 범위 (기본값: B3:C)')
    parser.add_argument('--output-dir', default='googlesheet_results',
                       help='결과 저장 디렉토리')
    parser.add_argument('--update-sheet', action='store_true',
                       help='결과를 구글 시트에 업데이트')
    parser.add_argument('--credentials', default='credentials.json',
                       help='구글 API 인증 파일 경로')
    parser.add_argument('--result-column', default='D',
                       help='결과를 입력할 시작 열 (기본값: D)')
    parser.add_argument('--result-row', type=int, default=3,
                       help='결과를 입력할 시작 행 (기본값: 3)')

    args = parser.parse_args()

    # 구글 시트 비교기 초기화
    comparator = GoogleSheetImageComparator(
        args.spreadsheet_id,
        args.range,
        args.output_dir
    )

    # 인증
    comparator.authenticate(args.credentials)

    # 비교 실행
    comparator.compare_from_sheet()

    # CSV 내보내기
    comparator.export_to_csv()

    # 구글 시트 업데이트 (옵션)
    if args.update_sheet:
        comparator.update_sheet_results(
            start_column=args.result_column,
            start_row=args.result_row
        )

    return 0


if __name__ == '__main__':
    exit(main())