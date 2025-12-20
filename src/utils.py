"""ユーティリティ関数: デバイス検出、画像ファイル検証など"""

import os
from pathlib import Path
from typing import Literal

try:
    import torch
except ImportError:
    torch = None


def get_device(device_preference: str = "auto") -> Literal["mps", "cpu"]:
    """
    利用可能なデバイスを取得（MPS優先）
    
    Args:
        device_preference: デバイス指定 ("auto" | "mps" | "cpu")
    
    Returns:
        "mps" または "cpu"
    
    Raises:
        RuntimeError: PyTorchがインストールされていない場合
    """
    if torch is None:
        raise RuntimeError(
            "PyTorch is not installed. Please install it with: pip install torch"
        )
    
    if device_preference == "cpu":
        return "cpu"
    
    if device_preference == "mps":
        if torch.backends.mps.is_available():
            return "mps"
        else:
            raise RuntimeError(
                "MPS is requested but not available on this system. "
                "Use --device cpu or --device auto"
            )
    
    # device_preference == "auto"
    if torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"


def validate_image_file(filename: str) -> bool:
    """
    画像ファイルかどうかを判定
    
    Args:
        filename: ファイル名
    
    Returns:
        画像ファイルの場合True
    """
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    ext = Path(filename).suffix.lower()
    return ext in valid_extensions


def get_output_path(zip_path: str, output_dir: str | None = None, suffix: str = "_output") -> Path:
    """
    出力ファイルパスを生成
    
    Args:
        zip_path: 元のZipファイルパス
        output_dir: 出力ディレクトリ（Noneの場合はZipファイルと同じディレクトリ）
        suffix: ファイル名に追加するサフィックス
    
    Returns:
        出力ファイルパス
    """
    zip_path_obj = Path(zip_path)
    zip_stem = zip_path_obj.stem
    
    if output_dir is None:
        output_dir = zip_path_obj.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir / f"{zip_stem}{suffix}"

