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

### 方法1: 自動セットアップスクリプト（推奨）

最も簡単な方法です。以下のコマンドで全てのセットアップが完了します：

```bash
# リポジトリのクローン（submoduleも含む）
git clone --recursive https://github.com/kazuki-ookura/manga-ocr.git
cd manga-ocr

# セットアップスクリプトを実行
./setup.sh
```

セットアップスクリプトは以下を自動で実行します：
- `comic-text-detector`のセットアップ（git submodule）
- モデルファイルのダウンロード
- 仮想環境の作成（オプション）
- 依存関係のインストール

### 方法2: 手動セットアップ

#### 1. リポジトリのクローン

```bash
# submoduleも含めてクローン（推奨）
git clone --recursive https://github.com/kazuki-ookura/manga-ocr.git
cd manga-ocr

# または、既にクローン済みの場合
git submodule update --init --recursive
```

#### 2. comic-text-detectorのセットアップ

`comic-text-detector`はgit submoduleとして管理されています：

```bash
# submoduleを初期化（既に--recursiveでクローンした場合は不要）
git submodule update --init --recursive
```

<details>
<summary>既存のvendor/comic-text-detectorがある場合（v0.1以前からアップデートする場合）</summary>

既に手動で`vendor/comic-text-detector`をクローンしている場合は、以下の手順でsubmoduleに変換できます：

```bash
# 既存のvendor/comic-text-detectorを削除（バックアップ推奨）
rm -rf vendor/comic-text-detector

# git submoduleとして追加
git submodule add https://github.com/dmMaze/comic-text-detector.git vendor/comic-text-detector

# submoduleを初期化
git submodule update --init --recursive
```

</details>

**重要**: `comic-text-detector`は必須です。セットアップしないとテキスト検出機能が動作しません。

#### 3. 仮想環境の作成と依存関係のインストール

```bash
# 仮想環境を作成（推奨）
python3 -m venv venv
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt

# プロジェクトをインストール（エントリーポイントを有効化）
pip install -e .
```

#### 4. モデルファイルの配置

`comic-text-detector` を使用するには、事前にトレーニングされたモデルファイルが必要です。

**setup.shが利用できない場合**（Windowsなど）は、以下のリンクからモデルファイルをダウンロードし、`vendor/comic-text-detector/data/comictextdetector.pt` に配置してください：

- [manga-image-translator 最新リリースページ](https://github.com/zyddnys/manga-image-translator/releases/latest)
- [manga-image-translator beta-0.3 リリースページ](https://github.com/zyddnys/manga-image-translator/releases/tag/beta-0.3)
- [Google Drive](https://drive.google.com/drive/folders/1cTsXP5NYTCjhPVxwScdhxqJleHuIOyXG?usp=sharing)

```bash
# dataディレクトリが存在しない場合は作成
mkdir -p vendor/comic-text-detector/data

# ダウンロードしたファイルを配置（パスを適宜変更してください）
mv ~/Downloads/comictextdetector.pt vendor/comic-text-detector/data/
```

**重要**: モデルファイル（約76MB）は必須です。配置されていない場合、テキスト検出機能は動作しません。

## 使用方法

### エントリーポイントを使用（推奨）

`pip install -e .`でインストールした場合、以下のコマンドで実行できます：

```bash
# 基本的な使用
manga-ocr comic.zip
```

### モジュールとして実行

エントリーポイントが設定されていない場合：

```bash
# 基本的な使用
python3 -m src.cli comic.zip
```

# JSON形式のみ出力
manga-ocr comic.zip --output-format json

# 出力ディレクトリを指定
manga-ocr comic.zip -o ./results

# 詳細ログ付きで実行
manga-ocr comic.zip --verbose

# CPUを強制使用
manga-ocr comic.zip --device cpu

# エラー時に処理を中断
manga-ocr comic.zip --no-skip-errors
```

### 出力ファイル

処理が完了すると、以下のファイルが生成されます:
- `{zip_filename}_output.json`: JSON形式の構造化データ
- `{zip_filename}_output.txt`: 人間が読みやすいテキスト形式

### 使用例

```bash
# 実際の使用例
manga-ocr '漫画タイトル.zip' --verbose

# 出力例:
# 画像ファイルを 218 個見つけました
# 処理を開始します（デバイス: mps）...
# 処理完了: 218 ページを処理しました
# 出力ファイル:
#   - 漫画タイトル_output.json
#   - 漫画タイトル_output.txt
```


## 注意事項

- **comic-text-detector**: テキスト検出機能を使用するために必須です。インストール手順の「2. comic-text-detectorのセットアップ」を参照してください。
- **モデルファイル**: `comic-text-detector` のモデルファイル（`comictextdetector.pt`）が必須です。インストール手順の「4. モデルファイルの配置」を参照してください。
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

