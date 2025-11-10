#!/bin/bash
# 구글 시트 연동 테스트 스크립트

# 가상 환경 활성화
source venv/bin/activate

echo "구글 시트 연동 테스트"
echo "======================"
echo ""
echo "이 스크립트는 구글 시트와 연동하여 이미지를 비교합니다."
echo "구글 시트 구조:"
echo "  B3: 첫 번째 이미지 경로"
echo "  C3: 두 번째 이미지 경로"
echo "  D3~H3: 결과가 자동으로 입력됩니다"
echo ""

# 스프레드시트 ID 입력 받기
read -p "구글 시트 ID를 입력하세요: " SHEET_ID

if [ -z "$SHEET_ID" ]; then
    echo "오류: 시트 ID가 필요합니다"
    exit 1
fi

# credentials.json 파일 확인
if [ ! -f "credentials.json" ]; then
    echo ""
    echo "⚠️  credentials.json 파일이 없습니다!"
    echo ""
    echo "구글 클라우드 콘솔에서 다운로드하세요:"
    echo "1. https://console.cloud.google.com 접속"
    echo "2. API 및 서비스 > 사용자 인증 정보"
    echo "3. OAuth 2.0 클라이언트 ID 생성"
    echo "4. credentials.json 다운로드"
    exit 1
fi

echo ""
echo "실행 옵션을 선택하세요:"
echo "1) 읽기만 (로컬에 결과 저장)"
echo "2) 읽기 + 구글 시트 업데이트"
echo "3) 커스텀 범위 지정"
read -p "선택 [1-3]: " OPTION

case $OPTION in
    1)
        echo "구글 시트에서 데이터를 읽고 로컬에 결과를 저장합니다..."
        python imgdiff_googlesheet.py "$SHEET_ID"
        ;;
    2)
        echo "구글 시트에서 데이터를 읽고 결과를 시트에 업데이트합니다..."
        python imgdiff_googlesheet.py "$SHEET_ID" --update-sheet
        ;;
    3)
        read -p "범위 입력 (예: Sheet2!E5:F): " RANGE
        read -p "결과 열 (예: G): " COL
        read -p "결과 행 (예: 5): " ROW

        CMD="python imgdiff_googlesheet.py \"$SHEET_ID\""

        if [ -n "$RANGE" ]; then
            CMD="$CMD --range \"$RANGE\""
        fi

        if [ -n "$COL" ] && [ -n "$ROW" ]; then
            CMD="$CMD --update-sheet --result-column $COL --result-row $ROW"
        fi

        echo "실행: $CMD"
        eval $CMD
        ;;
    *)
        echo "잘못된 선택입니다."
        exit 1
        ;;
esac

echo ""
echo "✅ 완료!"
echo ""
echo "결과 확인:"
echo "  - 로컬 결과: googlesheet_results/"
echo "  - 구글 시트: https://docs.google.com/spreadsheets/d/$SHEET_ID/edit"