#!/usr/bin/env python3
"""
구글 시트 ID 확인 도구
"""

import sys
import pickle
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def check_sheet_id(spreadsheet_id):
    """구글 시트 ID가 유효한지 확인"""

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = None

    # 토큰 로드
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # 인증이 없거나 만료된 경우
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("❌ credentials.json 파일이 없습니다!")
                return False

            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    try:
        service = build('sheets', 'v4', credentials=creds)

        # 시트 메타데이터 가져오기
        sheet_metadata = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()

        print("✅ 유효한 구글 시트입니다!")
        print(f"제목: {sheet_metadata.get('properties', {}).get('title', 'N/A')}")
        print(f"시트 수: {len(sheet_metadata.get('sheets', []))}")

        # 시트 이름들 출력
        for sheet in sheet_metadata.get('sheets', []):
            sheet_name = sheet.get('properties', {}).get('title', 'N/A')
            print(f"  - {sheet_name}")

        return True

    except HttpError as error:
        if 'not found' in str(error).lower():
            print("❌ 시트를 찾을 수 없습니다. ID를 확인해주세요.")
        elif 'not supported' in str(error).lower():
            print("❌ 이 ID는 구글 시트가 아닙니다.")
            print("   구글 독스나 드라이브 폴더 ID인 것 같습니다.")
        else:
            print(f"❌ 오류: {error}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("사용법: python check_sheet_id.py SPREADSHEET_ID")
        sys.exit(1)

    sheet_id = sys.argv[1]
    print(f"\n확인 중: {sheet_id}")
    print("-" * 50)

    if check_sheet_id(sheet_id):
        print("\n이 ID로 이미지 비교를 실행할 수 있습니다:")
        print(f"python imgdiff_googlesheet.py {sheet_id} --update-sheet")
    else:
        print("\n올바른 구글 시트 URL 예시:")
        print("https://docs.google.com/spreadsheets/d/YOUR_ID_HERE/edit")