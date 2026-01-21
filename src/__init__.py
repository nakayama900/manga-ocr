"""Manga OCR CLI Tool - Zipファイルから漫画画像をOCR処理するツール"""

import warnings

# Suppress pkg_resources deprecation warning from comic-text-detector
# pkg_resources is used by yolov5_utils.py in the vendored comic-text-detector
# This warning will be resolved when comic-text-detector updates to use importlib.metadata
warnings.filterwarnings('ignore', message='.*pkg_resources is deprecated.*')

__version__ = "0.1.0"

