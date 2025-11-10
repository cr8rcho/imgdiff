#!/bin/bash
# 이미지 비교 도구 실행 스크립트

# 가상 환경 활성화
source venv/bin/activate

# 인자 전달하여 실행
python3 imgdiff.py "$@"