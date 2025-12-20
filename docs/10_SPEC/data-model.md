# Data Model

## 出力データ構造

### JSON形式 (`{zip_filename}_output.json`)

```json
[
  {
    "filename": "page_01.jpg",
    "page_number": 1,
    "text_regions": [
      {
        "region_id": 0,
        "bbox": [x1, y1, x2, y2],
        "text": "セリフ1",
        "confidence": 0.95
      },
      {
        "region_id": 1,
        "bbox": [x1, y1, x2, y2],
        "text": "セリフ2",
        "confidence": 0.92
      }
    ],
    "texts": ["セリフ1", "セリフ2"],
    "processing_time": 1.23
  },
  {
    "filename": "page_02.jpg",
    "page_number": 2,
    "text_regions": [...],
    "texts": [...],
    "processing_time": 1.15
  }
]
```

#### フィールド説明

- **filename**: 元の画像ファイル名
- **page_number**: ページ番号（1始まり）
- **text_regions**: 検出されたテキスト領域の詳細情報（オプション）
  - **region_id**: 領域のID（読み順）
  - **bbox**: バウンディングボックス座標 `[x1, y1, x2, y2]`
  - **text**: 認識されたテキスト
  - **confidence**: 認識の信頼度（0.0-1.0）
- **texts**: テキストのみの配列（簡易形式）
- **processing_time**: 処理時間（秒）

### テキスト形式 (`{zip_filename}_output.txt`)

```
[page_01.jpg]
セリフ1
セリフ2

[page_02.jpg]
セリフ3
セリフ4
セリフ5

...
```

#### フォーマット仕様

- ページ区切り: `[filename]` 形式のヘッダー
- テキスト区切り: 空行で区切る
- エンコーディング: UTF-8

## 内部データ構造

### 処理中のデータフロー

```python
# 1. Zip展開後の画像リスト
ImageFile = {
    "path": str,           # ファイルパス
    "filename": str,       # ファイル名
    "index": int          # ソート後のインデックス
}

# 2. テキスト検出結果
TextRegion = {
    "bbox": Tuple[int, int, int, int],  # (x1, y1, x2, y2)
    "image": PIL.Image,                 # クロップされた画像
    "reading_order": int                # 読み順（0始まり）
}

# 3. OCR結果
OCRResult = {
    "text": str,                        # 認識されたテキスト
    "confidence": float,                # 信頼度
    "region": TextRegion                # 元の領域情報
}

# 4. ページ単位の結果
PageResult = {
    "filename": str,
    "page_number": int,
    "regions": List[TextRegion],
    "ocr_results": List[OCRResult],
    "processing_time": float
}
```

## 設定データ構造（将来拡張用）

```python
Config = {
    "device": str,              # "mps" | "cpu"
    "output_format": List[str], # ["json", "txt"]
    "output_dir": str,          # 出力ディレクトリ
    "temp_dir": str,            # 一時ディレクトリ
    "verbose": bool,            # 詳細ログ出力
    "skip_errors": bool         # エラー時スキップ
}
```

