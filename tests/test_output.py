"""output.py のユニットテスト"""

import pytest
import json
import tempfile
from pathlib import Path
from src.output import generate_json_output, generate_text_output, generate_outputs
from src.pipeline import PageResult
from src.detector import TextRegion
from src.ocr import OCRResult
from PIL import Image


def create_test_page_result() -> PageResult:
    """テスト用のPageResultを作成"""
    img = Image.new('RGB', (100, 50), color='white')
    region = TextRegion(bbox=(0, 0, 100, 50), image=img, reading_order=0)
    ocr_result = OCRResult(text="テストテキスト", confidence=0.95, region=region)
    
    return PageResult(
        filename="test.png",
        page_number=1,
        regions=[region],
        ocr_results=[ocr_result],
        processing_time=1.23
    )


def test_generate_json_output():
    """JSON出力のテスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.json"
        results = [create_test_page_result()]
        
        generate_json_output(results, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["filename"] == "test.png"
        assert data[0]["page_number"] == 1
        assert len(data[0]["texts"]) == 1
        assert data[0]["texts"][0] == "テストテキスト"


def test_generate_text_output():
    """テキスト出力のテスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.txt"
        results = [create_test_page_result()]
        
        generate_text_output(results, output_path)
        
        assert output_path.exists()
        content = output_path.read_text(encoding='utf-8')
        assert "[test.png]" in content
        assert "テストテキスト" in content


def test_generate_outputs():
    """出力生成の統合テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        results = [create_test_page_result()]
        
        # both形式
        files = generate_outputs(results, output_dir, "test", "both")
        assert len(files) == 2
        assert any(f.name.endswith('.json') for f in files)
        assert any(f.name.endswith('.txt') for f in files)
        
        # json形式のみ
        files = generate_outputs(results, output_dir, "test2", "json")
        assert len(files) == 1
        assert files[0].name.endswith('.json')
        
        # txt形式のみ
        files = generate_outputs(results, output_dir, "test3", "txt")
        assert len(files) == 1
        assert files[0].name.endswith('.txt')

