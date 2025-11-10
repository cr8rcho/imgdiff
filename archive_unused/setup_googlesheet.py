#!/usr/bin/env python3
"""
구글 시트에 테스트 데이터 입력
"""

import pickle
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

def setup_sheet(spreadsheet_id):
    """구글 시트에 테스트 데이터 입력"""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
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

    # B3:C6에 테스트 데이터 입력
    values = [
        ['image1.png', 'image2.png'],
        ['v1_001.png', 'v2_001.png'],
        ['identical1.png', 'identical2.png'],
        ['small_image.png', 'large_image.png']
    ]

    body = {
        'values': values
    }

    try:
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='B3:C6',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

        print(f"✅ 테스트 데이터 입력 완료!")
        print(f"   업데이트된 셀: {result.get('updatedCells')}개")
        print("\n입력된 데이터:")
        print("   B3: image1.png        C3: image2.png")
        print("   B4: v1_001.png        C4: v2_001.png")
        print("   B5: identical1.png    C5: identical2.png")
        print("   B6: small_image.png   C6: large_image.png")

        # 헤더도 추가
        header_body = {
            'values': [['이미지1', '이미지2']]
        }
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='B2:C2',
            valueInputOption='USER_ENTERED',
            body=header_body
        ).execute()

        print("\n✅ 헤더 추가 완료 (B2:C2)")

        return True

    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

if __name__ == '__main__':
    sheet_id = "1GjpcVKjSaY7O_ouCuORuTaE7cdzyYmUQYYtGFRDBs-U"
    print(f"구글 시트 설정 중: {sheet_id}")
    print("-" * 50)

    if setup_sheet(sheet_id):
        print(f"\n이제 이미지 비교를 실행할 수 있습니다:")
        print(f"python imgdiff_googlesheet.py {sheet_id} --update-sheet")