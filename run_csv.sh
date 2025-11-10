#!/bin/bash
# CSV 파일 기반 이미지 비교 실행 스크립트

# 가상 환경 활성화
source venv/bin/activate

# CSV 파일 인자 확인
if [ -z "$1" ]; then
    echo "사용법: ./run_csv.sh <csv_file>"
    echo "예시: ./run_csv.sh sample_images.csv"
    exit 1
fi

# CSV 파일 존재 확인
if [ ! -f "$1" ]; then
    echo "오류: CSV 파일을 찾을 수 없습니다: $1"
    exit 1
fi

# 실행
python imgdiff_csv.py "$@"

# 결과 디렉토리 확인
if [ -d "csv_comparison_results" ]; then
    echo ""
    echo "📊 결과 보기:"
    echo "  open csv_comparison_results/summary_report.html"
fi