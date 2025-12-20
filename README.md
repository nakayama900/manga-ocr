# Manga OCR CLI Tool

Zipファイルで圧縮された漫画画像を一括で読み込み、OCRを実行してテキストデータを出力するPython CLIツール。

Apple Silicon (M1/M2/M3/M4) のMPS (Metal Performance Shaders) を活用し、ローカル環境で高速に推論を行います。

## 機能

- ✅ Zipファイルから漫画画像を一括処理
- ✅ テキスト領域（吹き出し）の自動検出
- ✅ 漫画の読み順に基づいたテキスト抽出
- ✅ JSON形式とテキスト形式での出力
- ✅ Apple Silicon (MPS) による高速OCR処理

## 要件

- Python 3.10+
- **推奨環境**:
  - Apple Silicon Mac (M1/M2/M3/M4) - MPS対応（最速）
  - Windows/Linux with NVIDIA GPU - CUDA対応（高速）
  - その他の環境でもCPUで動作します（やや遅い）
- PyTorch（GPU対応版を推奨）

## インストール

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd manga-ocr
```

### 2. comic-text-detectorのセットアップ（オプション）

テキスト検出の精度を上げるために、`comic-text-detector`をセットアップできます：

```bash
git clone https://github.com/dmMaze/comic-text-detector.git vendor/comic-text-detector
```

**注意**: `comic-text-detector`がなくても動作しますが、テキスト検出の精度が下がります（画像全体を1つの領域として扱います）。

### 3. 仮想環境の作成と依存関係のインストール

```bash
# 仮想環境を作成（推奨）
python3 -m venv venv
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt
```

### 4. モデルファイルの配置

`comic-text-detector` を使用するには、事前にトレーニングされたモデルファイルが必要です。

1. 以下のリンクからモデルファイルをダウンロードしてください：
   - [manga-image-translator リリースページ](https://github.com/zyddnys/manga-image-translator/releases/tag/beta-0.2.1)
   - [Google Drive](https://drive.google.com/drive/folders/1cTsXP5NYTCjhPVxwScdhxqJleHuIOyXG?usp=sharing)

2. ダウンロードしたモデルファイル（`comictextdetector.pt` または `comictextdetector.pt.onnx`）を以下の場所に配置してください：
   ```
   vendor/comic-text-detector/data/comictextdetector.pt
   ```

**注意**: モデルファイルは約100MB以上のサイズがあります。モデルファイルが配置されていない場合、テキスト検出機能は使用できません（フォールバックとして画像全体を1つの領域として扱います）。

## 使用方法

```bash
# 基本的な使用
python3 -m src.cli comic.zip

# JSON形式のみ出力
python3 -m src.cli comic.zip --output-format json

# 出力ディレクトリを指定
python3 -m src.cli comic.zip -o ./results

# 詳細ログ付きで実行
python3 -m src.cli comic.zip --verbose

# CPUを強制使用
python3 -m src.cli comic.zip --device cpu

# エラー時に処理を中断
python3 -m src.cli comic.zip --no-skip-errors
```

### 出力ファイル

処理が完了すると、以下のファイルが生成されます:
- `{zip_filename}_output.json`: JSON形式の構造化データ
- `{zip_filename}_output.txt`: 人間が読みやすいテキスト形式

### 使用例

```bash
# 実際の使用例
python3 -m src.cli '漫画タイトル.zip' --verbose

# 出力例:
# 画像ファイルを 218 個見つけました
# 処理を開始します（デバイス: mps）...
# 処理完了: 218 ページを処理しました
# 出力ファイル:
#   - 漫画タイトル_output.json
#   - 漫画タイトル_output.txt
```


## 注意事項

- **モデルファイル**: `comic-text-detector` のモデルファイル（`comictextdetector.pt`）が必要です。上記のインストール手順を参照してください。
- **初回実行**: 初回実行時、`manga-ocr` がモデルをダウンロードするため時間がかかります。
- **処理時間**: 画像数やサイズによって処理時間が異なります。大量の画像がある場合は時間がかかります。
- **MPSサポート**: OCR処理はMPSを使用して高速に実行されます。テキスト検出はCPUで実行されます（詳細は `docs/PERFORMANCE.md` を参照）。

## トラブルシューティング

問題が発生した場合は、`docs/TROUBLESHOOTING.md` を参照してください。

## ドキュメント

- **トラブルシューティング**: `docs/TROUBLESHOOTING.md` - よくある問題と解決方法
- **パフォーマンス**: `docs/PERFORMANCE.md` - デバイス使用、MPS、パフォーマンスについて
- **開発計画**: `docs/20_PLAN/roadmap.md` - 開発状況と実装計画

## ライセンス

MIT License

