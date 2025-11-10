#!/usr/bin/env python3
"""
구글 시트 내용 확인 - IMAGE 함수 포함
"""

import pickle
import os
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

def check_sheet_content(spreadsheet_id):
    """구글 시트 내용 확인"""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # B3:C 범위의 값 가져오기 (수식 포함)
    try:
        # 1. 일반 값 가져오기
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='B3:C10',
            valueRenderOption='FORMATTED_VALUE'
        ).execute()

        values = result.get('values', [])

        print("📋 시트 내용 (표시값):")
        print("-" * 50)
        for i, row in enumerate(values, 3):
            if len(row) >= 2:
                print(f"B{i}: {row[0][:50]}...")
                print(f"C{i}: {row[1][:50]}...")
            elif len(row) == 1:
                print(f"B{i}: {row[0][:50]}...")
            print()

        # 2. 수식 가져오기
        result_formula = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='B3:C10',
            valueRenderOption='FORMULA'
        ).execute()

        formulas = result_formula.get('values', [])

        print("\n📐 시트 수식:")
        print("-" * 50)
        for i, row in enumerate(formulas, 3):
            if len(row) >= 2:
                b_val = row[0]
                c_val = row[1]

                # IMAGE 함수에서 URL 추출
                b_url = extract_url_from_image(b_val)
                c_url = extract_url_from_image(c_val)

                if b_url:
                    print(f"B{i}: IMAGE 함수 감지")
                    print(f"     URL: {b_url}")
                else:
                    print(f"B{i}: {b_val}")

                if c_url:
                    print(f"C{i}: IMAGE 함수 감지")
                    print(f"     URL: {c_url}")
                else:
                    print(f"C{i}: {c_val}")
                print()

        # 3. 배치 가져오기로 더 상세한 정보
        batch_result = service.spreadsheets().values().batchGet(
            spreadsheetId=spreadsheet_id,
            ranges=['B3:C10'],
            valueRenderOption='FORMULA'
        ).execute()

        print("\n🔍 URL 추출 결과:")
        print("-" * 50)

        url_pairs = []
        for range_data in batch_result.get('valueRanges', []):
            for i, row in enumerate(range_data.get('values', []), 3):
                if len(row) >= 2:
                    url1 = extract_url_from_image(row[0])
                    url2 = extract_url_from_image(row[1])

                    if url1 and url2:
                        url_pairs.append({
                            'row': i,
                            'url1': url1,
                            'url2': url2
                        })
                        print(f"행 {i}:")
                        print(f"  URL1: {url1}")
                        print(f"  URL2: {url2}")

        return url_pairs

    except Exception as e:
        print(f"❌ 오류: {e}")
        return []

def extract_url_from_image(cell_value):
    """IMAGE 함수에서 URL 추출"""
    if not cell_value:
        return None

    # =IMAGE("URL") 패턴
    pattern1 = r'=IMAGE\s*\(\s*"([^"]+)"\s*\)'
    # =IMAGE('URL') 패턴
    pattern2 = r"=IMAGE\s*\(\s*'([^']+)'\s*\)"

    match = re.match(pattern1, str(cell_value), re.IGNORECASE)
    if match:
        return match.group(1)

    match = re.match(pattern2, str(cell_value), re.IGNORECASE)
    if match:
        return match.group(1)

    return None

if __name__ == '__main__':
    sheet_id = "1GjpcVKjSaY7O_ouCuORuTaE7cdzyYmUQYYtGFRDBs-U"
    print(f"구글 시트 내용 확인: {sheet_id}")
    print("=" * 50)

    url_pairs = check_sheet_content(sheet_id)

    if url_pairs:
        print(f"\n✅ {len(url_pairs)}개의 URL 쌍을 발견했습니다!")
        print("\n이제 URL에서 이미지를 다운로드하여 비교할 수 있습니다.")