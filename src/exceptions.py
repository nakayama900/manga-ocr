"""カスタム例外クラス"""


class MangaOCRError(Exception):
    """ベース例外クラス"""
    pass


class ZipExtractionError(MangaOCRError):
    """Zip展開エラー"""
    pass


class NoImagesFoundError(MangaOCRError):
    """画像ファイルが見つからないエラー"""
    pass


class ModelLoadError(MangaOCRError):
    """モデル読み込みエラー"""
    pass


class ImageProcessingError(MangaOCRError):
    """画像処理エラー"""
    pass


class OutputGenerationError(MangaOCRError):
    """出力生成エラー"""
    pass

