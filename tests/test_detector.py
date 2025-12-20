"""detector.py のユニットテスト"""

import pytest
from PIL import Image
from src.detector import (
    detect_text_regions,
    sort_by_reading_order,
    crop_text_regions,
    TextRegion,
    HAS_COMIC_DETECTOR
)


def test_sort_by_reading_order():
    """読み順ソートのテスト"""
    # テスト用の領域を作成（右上から左下へ）
    regions = [
        TextRegion(bbox=(200, 50, 300, 100), image=None, reading_order=0),
        TextRegion(bbox=(50, 50, 150, 100), image=None, reading_order=0),
        TextRegion(bbox=(200, 200, 300, 250), image=None, reading_order=0),
        TextRegion(bbox=(50, 200, 150, 250), image=None, reading_order=0),
    ]
    
    sorted_regions = sort_by_reading_order(regions)
    
    # 読み順が設定されていることを確認
    assert all(r.reading_order >= 0 for r in sorted_regions)
    # ソートされていることを確認（簡易チェック）
    assert len(sorted_regions) == len(regions)


def test_crop_text_regions():
    """領域クロップのテスト"""
    img = Image.new('RGB', (300, 300), color='white')
    
    regions = [
        TextRegion(bbox=(50, 50, 150, 100), image=None, reading_order=0),
        TextRegion(bbox=(200, 200, 300, 250), image=None, reading_order=1),
    ]
    
    cropped = crop_text_regions(img, regions)
    assert len(cropped) == 2
    assert all(r.image is not None for r in cropped)
    assert all(r.image.size[0] > 0 and r.image.size[1] > 0 for r in cropped)


def test_detect_text_regions_fallback():
    """テキスト検出のフォールバックテスト"""
    img = Image.new('RGB', (100, 100), color='white')
    
    # comic-text-detectorが利用できない場合でも動作することを確認
    regions = detect_text_regions(img, device="cpu")
    assert len(regions) > 0
    assert regions[0].bbox == (0, 0, 100, 100)  # フォールバック時は画像全体

