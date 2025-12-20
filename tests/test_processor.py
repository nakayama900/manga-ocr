"""processor.py のユニットテスト"""

import pytest
import tempfile
import zipfile
from pathlib import Path
from PIL import Image
from src.processor import extract_zip, get_image_files, process_zip
from src.exceptions import ZipExtractionError, NoImagesFoundError


def create_test_zip(tmpdir: Path, image_count: int = 3) -> Path:
    """テスト用のZipファイルを作成"""
    zip_path = tmpdir / "test.zip"
    
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for i in range(1, image_count + 1):
            # テスト画像を作成
            img = Image.new('RGB', (100, 100), color='white')
            img_path = tmpdir / f"{i:04d}.png"
            img.save(img_path)
            zf.write(img_path, f"{i:04d}.png")
    
    return zip_path


def test_extract_zip():
    """Zip展開のテスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = create_test_zip(Path(tmpdir))
        
        with extract_zip(str(zip_path)) as extracted_dir:
            assert extracted_dir.exists()
            files = list(extracted_dir.glob("*.png"))
            assert len(files) == 3


def test_extract_zip_invalid():
    """無効なZipファイルのテスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        invalid_zip = Path(tmpdir) / "invalid.zip"
        invalid_zip.write_text("not a zip file")
        
        with pytest.raises(ZipExtractionError):
            with extract_zip(str(invalid_zip)):
                pass


def test_get_image_files():
    """画像ファイル取得のテスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # 画像ファイルを作成
        for i in [1, 2, 10]:
            img = Image.new('RGB', (100, 100), color='white')
            img.save(tmpdir_path / f"{i:04d}.png")
        
        # 非画像ファイルを作成
        (tmpdir_path / "readme.txt").write_text("test")
        
        image_files = get_image_files(tmpdir_path)
        assert len(image_files) == 3
        # 自然順ソートの確認
        assert image_files[0].filename == "0001.png"
        assert image_files[1].filename == "0002.png"
        assert image_files[2].filename == "0010.png"


def test_get_image_files_no_images():
    """画像ファイルが見つからない場合のテスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        (tmpdir_path / "readme.txt").write_text("test")
        
        with pytest.raises(NoImagesFoundError):
            get_image_files(tmpdir_path)


def test_process_zip():
    """Zip処理の統合テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = create_test_zip(Path(tmpdir))
        
        image_files = process_zip(str(zip_path))
        assert len(image_files) == 3
        assert all(img.filename.endswith('.png') for img in image_files)

