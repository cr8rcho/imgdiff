#!/usr/bin/env python3
"""
테스트용 이미지 생성 스크립트
두 개의 비슷하지만 약간 다른 이미지를 생성합니다.
"""

from PIL import Image, ImageDraw, ImageFont
import random
import numpy as np


def create_test_images():
    """테스트용 이미지 2개를 생성합니다."""

    # 이미지 크기
    width, height = 800, 600

    # 첫 번째 이미지 생성
    img1 = Image.new('RGB', (width, height), color='white')
    draw1 = ImageDraw.Draw(img1)

    # 배경 그라디언트
    for y in range(height):
        intensity = int((y / height) * 100)
        color = (intensity + 100, intensity + 120, intensity + 140)
        draw1.rectangle([0, y, width, y+1], fill=color)

    # 도형 그리기
    # 원
    draw1.ellipse([100, 100, 250, 250], fill='red', outline='darkred', width=3)

    # 사각형
    draw1.rectangle([300, 150, 450, 300], fill='blue', outline='darkblue', width=3)

    # 삼각형
    triangle_points = [(550, 250), (650, 100), (750, 250)]
    draw1.polygon(triangle_points, fill='green', outline='darkgreen')

    # 텍스트
    draw1.text((200, 400), "Test Image 1", fill='black', font=None)
    draw1.text((200, 450), "Sample Text Here", fill='purple', font=None)

    # 선 그리기
    draw1.line([(50, 500), (750, 500)], fill='orange', width=5)

    # 랜덤 점들
    for _ in range(100):
        x = random.randint(0, width-1)
        y = random.randint(350, 450)
        draw1.point((x, y), fill='gray')

    # 첫 번째 이미지 저장
    img1.save('image1.png')
    print("✅ image1.png 생성 완료")

    # 두 번째 이미지 생성 (첫 번째와 비슷하지만 약간 다름)
    img2 = Image.new('RGB', (width, height), color='white')
    draw2 = ImageDraw.Draw(img2)

    # 배경 그라디언트 (약간 다른 색상)
    for y in range(height):
        intensity = int((y / height) * 100)
        color = (intensity + 105, intensity + 115, intensity + 135)  # 약간 다른 색
        draw2.rectangle([0, y, width, y+1], fill=color)

    # 도형 그리기 (위치와 색상이 약간 다름)
    # 원 (위치 이동)
    draw2.ellipse([110, 105, 260, 255], fill='red', outline='darkred', width=3)

    # 사각형 (크기 변경)
    draw2.rectangle([300, 160, 460, 310], fill='navy', outline='darkblue', width=3)

    # 삼각형 (한 점 이동)
    triangle_points2 = [(550, 250), (660, 110), (750, 250)]  # 한 점이 이동
    draw2.polygon(triangle_points2, fill='forestgreen', outline='darkgreen')

    # 텍스트 (내용 변경)
    draw2.text((200, 400), "Test Image 2", fill='black', font=None)  # 숫자 변경
    draw2.text((200, 450), "Modified Text", fill='purple', font=None)  # 텍스트 변경

    # 선 그리기 (위치 이동)
    draw2.line([(50, 510), (750, 510)], fill='darkorange', width=5)

    # 추가 도형 (두 번째 이미지에만)
    draw2.rectangle([600, 400, 700, 480], fill='yellow', outline='gold', width=2)

    # 랜덤 점들 (다른 패턴)
    for _ in range(80):  # 개수도 다름
        x = random.randint(0, width-1)
        y = random.randint(360, 440)
        draw2.point((x, y), fill='darkgray')

    # 노이즈 추가 (미세한 차이 생성)
    img2_array = np.array(img2)
    noise = np.random.normal(0, 2, img2_array.shape)
    img2_array = np.clip(img2_array + noise, 0, 255).astype(np.uint8)
    img2 = Image.fromarray(img2_array)

    # 두 번째 이미지 저장
    img2.save('image2.png')
    print("✅ image2.png 생성 완료")

    print("\n생성된 이미지 간 차이점:")
    print("- 배경 그라디언트 색상 미세하게 다름")
    print("- 빨간 원의 위치가 약간 이동")
    print("- 파란 사각형의 크기와 색상이 변경")
    print("- 녹색 삼각형의 한 꼭지점이 이동")
    print("- 텍스트 내용이 변경됨")
    print("- 주황색 선의 위치가 이동")
    print("- 노란색 사각형이 추가됨")
    print("- 랜덤 점들의 패턴이 다름")
    print("- 미세한 노이즈 추가")


def create_identical_images():
    """동일한 이미지 2개를 생성합니다 (차이 없음 테스트용)."""

    width, height = 400, 300

    img = Image.new('RGB', (width, height), color='lightblue')
    draw = ImageDraw.Draw(img)

    # 간단한 패턴 그리기
    draw.ellipse([100, 50, 200, 150], fill='yellow', outline='orange')
    draw.rectangle([220, 100, 320, 200], fill='green')
    draw.text((150, 250), "Identical", fill='black')

    # 동일한 이미지를 두 개 저장
    img.save('identical1.png')
    img.save('identical2.png')

    print("\n✅ identical1.png, identical2.png 생성 완료 (동일한 이미지)")


def create_different_size_images():
    """크기가 다른 이미지 2개를 생성합니다."""

    # 첫 번째 이미지 (작은 크기)
    img1 = Image.new('RGB', (400, 300), color='lightgreen')
    draw1 = ImageDraw.Draw(img1)
    draw1.ellipse([50, 50, 150, 150], fill='blue')
    draw1.text((200, 150), "Small Image", fill='white')
    img1.save('small_image.png')

    # 두 번째 이미지 (큰 크기)
    img2 = Image.new('RGB', (600, 450), color='lightcoral')
    draw2 = ImageDraw.Draw(img2)
    draw2.ellipse([75, 75, 225, 225], fill='blue')
    draw2.text((300, 225), "Large Image", fill='white')
    img2.save('large_image.png')

    print("\n✅ small_image.png (400x300), large_image.png (600x450) 생성 완료")


if __name__ == '__main__':
    print("테스트용 이미지 생성 시작...\n")

    # 메인 테스트 이미지 생성
    create_test_images()

    # 동일한 이미지 생성
    create_identical_images()

    # 크기가 다른 이미지 생성
    create_different_size_images()

    print("\n" + "="*50)
    print("모든 테스트 이미지가 생성되었습니다!")
    print("\n사용 방법:")
    print("  python imgdiff.py image1.png image2.png")
    print("  python imgdiff.py identical1.png identical2.png")
    print("  python imgdiff.py small_image.png large_image.png")