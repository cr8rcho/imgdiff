#!/usr/bin/env python3
"""
구글 시트 연동 예제
B3, C3부터 이미지 경로가 시작하는 경우
"""

from imgdiff_googlesheet import GoogleSheetImageComparator

def example_b3_c3_start():
    """
    B3:C부터 데이터가 시작하는 구글 시트 예제

    구글 시트 구조:
    - B3: 첫 번째 이미지 경로
    - C3: 두 번째 이미지 경로
    - D3부터: 결과가 입력될 위치
    """

    # 구글 시트 ID (URL에서 확인)
    # https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit
    SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"

    # 구글 시트 비교기 초기화 (B3:C 범위 읽기)
    comparator = GoogleSheetImageComparator(
        spreadsheet_id=SPREADSHEET_ID,
        range_name='B3:C',  # B3부터 C열 끝까지
        output_dir='sheet_results'
    )

    # 인증 (첫 실행시 브라우저가 열림)
    comparator.authenticate('credentials.json')

    # 비교 실행
    print("📊 구글 시트에서 데이터 읽기 및 비교 시작...")
    comparator.compare_from_sheet()

    # 로컬에 CSV 저장
    comparator.export_to_csv('sheet_results.csv')

    # 구글 시트에 결과 업데이트 (D3부터 시작)
    print("\n📝 구글 시트 업데이트 중...")
    comparator.update_sheet_results(
        start_column='D',  # D열부터 결과 입력
        start_row=3        # 3행부터 시작
    )

    print("\n✅ 완료!")


def example_custom_range():
    """
    사용자 정의 범위 예제
    예: Sheet2의 E5:F 범위에서 읽기
    """

    SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"

    comparator = GoogleSheetImageComparator(
        spreadsheet_id=SPREADSHEET_ID,
        range_name='Sheet2!E5:F',  # Sheet2의 E5부터 시작
        output_dir='custom_results'
    )

    comparator.authenticate()
    comparator.compare_from_sheet()

    # 결과를 G5부터 입력
    comparator.update_sheet_results(
        start_column='G',
        start_row=5
    )


def example_batch_processing():
    """
    여러 시트를 순차적으로 처리하는 예제
    """

    SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"

    # 처리할 시트와 범위 목록
    sheets_to_process = [
        {'range': 'Sheet1!B3:C', 'result_col': 'D', 'result_row': 3},
        {'range': 'Sheet2!B3:C', 'result_col': 'D', 'result_row': 3},
        {'range': 'Sheet3!A2:B', 'result_col': 'C', 'result_row': 2},
    ]

    for sheet_config in sheets_to_process:
        print(f"\n처리 중: {sheet_config['range']}")

        comparator = GoogleSheetImageComparator(
            spreadsheet_id=SPREADSHEET_ID,
            range_name=sheet_config['range']
        )

        comparator.authenticate()
        comparator.compare_from_sheet()

        comparator.update_sheet_results(
            start_column=sheet_config['result_col'],
            start_row=sheet_config['result_row']
        )


if __name__ == '__main__':
    print("""
    구글 시트 연동 예제
    ====================

    사용하기 전에:
    1. 구글 클라우드 콘솔에서 Sheets API를 활성화하세요
    2. credentials.json 파일을 다운로드하세요
    3. SPREADSHEET_ID를 실제 ID로 변경하세요

    구글 시트 준비:
    - B3: 첫 번째 이미지 경로
    - C3: 두 번째 이미지 경로
    - D3~: 결과가 자동으로 입력됨
    """)

    # 기본 예제 실행
    # example_b3_c3_start()

    # 커스텀 범위 예제
    # example_custom_range()

    # 배치 처리 예제
    # example_batch_processing()