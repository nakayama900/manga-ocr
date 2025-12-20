"""utils.py のユニットテスト"""

import pytest
from pathlib import Path
from src.utils import get_device, validate_image_file, get_output_path


def test_get_device_auto():
    """デバイス自動検出のテスト"""
    device = get_device("auto")
    assert device in ("mps", "cpu")


def test_get_device_cpu():
    """CPUデバイス指定のテスト"""
    device = get_device("cpu")
    assert device == "cpu"


def test_validate_image_file():
    """画像ファイル検証のテスト"""
    assert validate_image_file("test.jpg") is True
    assert validate_image_file("test.jpeg") is True
    assert validate_image_file("test.png") is True
    assert validate_image_file("test.webp") is True
    assert validate_image_file("test.JPG") is True  # 大文字小文字を区別しない
    assert validate_image_file("test.txt") is False
    assert validate_image_file("test") is False


def test_get_output_path(tmp_path):
    """出力パス生成のテスト"""
    zip_path = "/path/to/comic.zip"
    output_path = get_output_path(zip_path, None, "_output")
    assert output_path.name == "comic_output"
    
    # 一時ディレクトリを使用
    custom_output = tmp_path / "custom" / "output"
    output_path = get_output_path(zip_path, str(custom_output), "_result")
    assert output_path.parent == custom_output
    assert output_path.name == "comic_result"

