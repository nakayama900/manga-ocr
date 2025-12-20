"""Zip処理モジュール: Zip展開、画像フィルタリング、自然順ソート"""

import tempfile
import zipfile
from pathlib import Path
from typing import List, NamedTuple
from contextlib import contextmanager

import natsort

from .exceptions import ZipExtractionError, NoImagesFoundError
from .utils import validate_image_file


class ImageFile(NamedTuple):
    """画像ファイル情報"""
    path: Path
    filename: str
    index: int


@contextmanager
def extract_zip(zip_path: str, temp_dir: str | None = None):
    """
    Zipファイルを一時ディレクトリに展開するコンテキストマネージャー
    
    Args:
        zip_path: Zipファイルのパス
        temp_dir: 一時ディレクトリ（Noneの場合はシステムの一時ディレクトリ）
    
    Yields:
        展開先のディレクトリパス（Pathオブジェクト）
    
    Raises:
        ZipExtractionError: Zip展開エラー
    """
    zip_path_obj = Path(zip_path)
    
    if not zip_path_obj.exists():
        raise ZipExtractionError(f"Zipファイルが見つかりません: {zip_path}")
    
    if not zip_path_obj.is_file():
        raise ZipExtractionError(f"指定されたパスはファイルではありません: {zip_path}")
    
    # 一時ディレクトリの作成
    if temp_dir is None:
        temp_dir_obj = Path(tempfile.mkdtemp(prefix="manga-ocr-"))
        cleanup = True
    else:
        temp_dir_obj = Path(temp_dir)
        temp_dir_obj.mkdir(parents=True, exist_ok=True)
        cleanup = False
    
    try:
        # Zipファイルの展開
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir_obj)
        except zipfile.BadZipFile:
            raise ZipExtractionError(f"破損したZipファイルです: {zip_path}")
        except zipfile.LargeZipFile:
            raise ZipExtractionError(f"Zipファイルが大きすぎます: {zip_path}")
        except Exception as e:
            raise ZipExtractionError(f"Zip展開中にエラーが発生しました: {e}")
        
        yield temp_dir_obj
        
    finally:
        # クリーンアップ（システムの一時ディレクトリの場合のみ）
        if cleanup:
            import shutil
            shutil.rmtree(temp_dir_obj, ignore_errors=True)


def get_image_files(directory: Path) -> List[ImageFile]:
    """
    ディレクトリ内の画像ファイルを取得し、自然順でソート
    
    Args:
        directory: 検索するディレクトリ
    
    Returns:
        自然順でソートされた画像ファイルのリスト
    
    Raises:
        NoImagesFoundError: 画像ファイルが見つからない場合
    """
    image_files: List[ImageFile] = []
    
    # ディレクトリ内の全ファイルを走査
    for file_path in directory.rglob('*'):
        if not file_path.is_file():
            continue
        
        if validate_image_file(file_path.name):
            image_files.append(ImageFile(
                path=file_path,
                filename=file_path.name,
                index=0  # 後でソート後に設定
            ))
    
    if not image_files:
        raise NoImagesFoundError(f"画像ファイルが見つかりません: {directory}")
    
    # ファイル名で自然順ソート
    sorted_files = natsort.natsorted(
        image_files,
        key=lambda x: x.filename
    )
    
    # インデックスを設定
    result = [
        ImageFile(
            path=img.path,
            filename=img.filename,
            index=i
        )
        for i, img in enumerate(sorted_files, start=1)
    ]
    
    return result


def process_zip(zip_path: str, temp_dir: str | None = None) -> List[ImageFile]:
    """
    Zipファイルを処理して画像ファイルのリストを返す
    
    Args:
        zip_path: Zipファイルのパス
        temp_dir: 一時ディレクトリ（Noneの場合はシステムの一時ディレクトリ）
    
    Returns:
        自然順でソートされた画像ファイルのリスト
    
    Raises:
        ZipExtractionError: Zip展開エラー
        NoImagesFoundError: 画像ファイルが見つからない場合
    """
    with extract_zip(zip_path, temp_dir) as extracted_dir:
        image_files = get_image_files(extracted_dir)
        return image_files

