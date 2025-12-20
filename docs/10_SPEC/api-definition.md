# API Definition (CLI Interface)

## コマンドラインインターフェース

### 基本コマンド

```bash
manga-ocr <zip_file> [OPTIONS]
```

### 引数

- **`zip_file`** (必須)
  - 処理対象のZipファイルのパス
  - 相対パス・絶対パス両方に対応

### オプション

#### 出力関連

- **`--output-dir`, `-o`** (オプション)
  - 出力ディレクトリを指定
  - デフォルト: Zipファイルと同じディレクトリ
  - 例: `--output-dir ./output`

- **`--output-format`, `-f`** (オプション)
  - 出力形式を指定（複数指定可能）
  - 選択肢: `json`, `txt`, `both`
  - デフォルト: `both`
  - 例: `--output-format json`

#### 処理設定

- **`--device`** (オプション)
  - 使用デバイスを明示的に指定
  - 選択肢: `auto`, `mps`, `cpu`
  - デフォルト: `auto` (MPS利用可能ならMPS、そうでなければCPU)
  - 例: `--device mps`

- **`--temp-dir`** (オプション)
  - 一時ディレクトリを指定
  - デフォルト: システムの一時ディレクトリ
  - 例: `--temp-dir /tmp/manga-ocr`

#### 動作制御

- **`--skip-errors`** (フラグ)
  - エラーが発生した画像をスキップして処理を継続
  - デフォルト: `True` (有効)

- **`--no-skip-errors`** (フラグ)
  - エラー時に処理を中断
  - `--skip-errors` の逆

- **`--verbose`, `-v`** (フラグ)
  - 詳細ログを出力
  - デフォルト: `False`

- **`--quiet`, `-q`** (フラグ)
  - エラー以外のログを抑制
  - デフォルト: `False`

#### ヘルプ

- **`--help`, `-h`**
  - ヘルプメッセージを表示

### 使用例

```bash
# 基本的な使用
manga-ocr comic.zip

# JSON形式のみ出力
manga-ocr comic.zip --output-format json

# 出力ディレクトリを指定
manga-ocr comic.zip -o ./results

# 詳細ログ付きで実行
manga-ocr comic.zip --verbose

# CPUを強制使用
manga-ocr comic.zip --device cpu

# エラー時に中断
manga-ocr comic.zip --no-skip-errors
```

## 内部API（モジュール間インターフェース）

### `processor.py`

```python
def process_zip(zip_path: str, config: Config) -> List[PageResult]:
    """
    Zipファイルを処理してOCR結果を返す
    
    Args:
        zip_path: Zipファイルのパス
        config: 設定オブジェクト
    
    Returns:
        ページごとのOCR結果のリスト
    
    Raises:
        ZipExtractionError: Zip展開エラー
        NoImagesFoundError: 画像ファイルが見つからない
    """
    pass
```

### `detector.py`

```python
def detect_text_regions(image: PIL.Image) -> List[TextRegion]:
    """
    画像からテキスト領域を検出
    
    Args:
        image: PIL Imageオブジェクト
    
    Returns:
        読み順でソートされたテキスト領域のリスト
    """
    pass

def sort_by_reading_order(regions: List[TextRegion]) -> List[TextRegion]:
    """
    テキスト領域を漫画の読み順でソート
    
    Args:
        regions: テキスト領域のリスト
    
    Returns:
        ソートされたテキスト領域のリスト
    """
    pass
```

### `ocr.py`

```python
def recognize_text(region_image: PIL.Image, device: str) -> OCRResult:
    """
    テキスト領域画像からテキストを認識
    
    Args:
        region_image: クロップされたテキスト領域画像
        device: 使用デバイス ("mps" | "cpu")
    
    Returns:
        OCR結果（テキスト、信頼度など）
    """
    pass
```

### `output.py`

```python
def generate_json_output(results: List[PageResult], output_path: str) -> None:
    """
    JSON形式の出力ファイルを生成
    
    Args:
        results: ページごとのOCR結果
        output_path: 出力ファイルパス
    """
    pass

def generate_text_output(results: List[PageResult], output_path: str) -> None:
    """
    テキスト形式の出力ファイルを生成
    
    Args:
        results: ページごとのOCR結果
        output_path: 出力ファイルパス
    """
    pass
```

### `utils.py`

```python
def get_device() -> str:
    """
    利用可能なデバイスを取得（MPS優先）
    
    Returns:
        "mps" または "cpu"
    """
    pass

def validate_image_file(filename: str) -> bool:
    """
    画像ファイルかどうかを判定
    
    Args:
        filename: ファイル名
    
    Returns:
        画像ファイルの場合True
    """
    pass
```

