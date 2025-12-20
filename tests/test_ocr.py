"""ocr.py のユニットテスト"""

import pytest
from PIL import Image
from src.ocr import recognize_text, recognize_text_regions, HAS_MANGA_OCR
from src.detector import TextRegion


@pytest.mark.skipif(not HAS_MANGA_OCR, reason="manga-ocr is not installed")
def test_recognize_text():
    """OCR認識のテスト"""
    img = Image.new('RGB', (100, 50), color='white')
    region = TextRegion(bbox=(0, 0, 100, 50), image=img, reading_order=0)
    
    result = recognize_text(img, region=region, device="cpu")
    assert result.text is not None
    assert isinstance(result.text, str)
    assert result.confidence >= 0.0
    assert result.region == region


@pytest.mark.skipif(not HAS_MANGA_OCR, reason="manga-ocr is not installed")
def test_recognize_text_regions():
    """複数領域のOCR認識のテスト"""
    img1 = Image.new('RGB', (100, 50), color='white')
    img2 = Image.new('RGB', (100, 50), color='white')
    
    regions = [
        TextRegion(bbox=(0, 0, 100, 50), image=img1, reading_order=0),
        TextRegion(bbox=(0, 0, 100, 50), image=img2, reading_order=1),
    ]
    
    results = recognize_text_regions(regions, device="cpu")
    assert len(results) == 2
    assert all(r.text is not None for r in results)
    assert all(r.region is not None for r in results)

