# Manga OCR CLI Tool

Zipファイルで圧縮された漫画画像を一括で読み込み、OCRを実行してテキストデータを出力するPython CLIツール。

Apple Silicon (M4) のMPS (Metal Performance Shaders) を活用し、ローカル環境で高速に推論を行います。

## 機能

- Zipファイルから漫画画像を一括処理
- テキスト領域（吹き出し）の自動検出
- 漫画の読み順に基づいたテキスト抽出
- JSON形式とテキスト形式での出力
- Apple Silicon (MPS) による高速処理

## 要件

- Python 3.10+
- Apple Silicon Mac (MPS対応)
- PyTorch (MPS対応版)

## インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd manga-ocr

# 仮想環境を作成（推奨）
python3 -m venv venv
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt

# 開発モードでインストール
pip install -e .
```

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

## 開発状況

**Phase 1-6 完了！** MVP機能の実装が完了しました。

- [x] Phase 1: プロジェクト基盤構築
- [x] Phase 2: 入力処理の実装（Zip展開、画像フィルタリング）
- [x] Phase 3: テキスト検出の実装（comic-text-detector統合）
- [x] Phase 4: OCR処理の実装（manga-ocr統合）
- [x] Phase 5: 出力生成の実装（JSON/TXT形式）
- [x] Phase 6: CLI統合と完成

詳細は `docs/20_PLAN/roadmap.md` を参照してください。

## 注意事項

- **モデルファイル**: `comic-text-detector` のモデルファイル（`comictextdetector.pt`）が必要です。
  詳細は `INSTALL.md` を参照してください。
- **初回実行**: 初回実行時、`manga-ocr` がモデルをダウンロードするため時間がかかります。
- **処理時間**: 画像数やサイズによって処理時間が異なります。大量の画像がある場合は時間がかかります。
- **MPSサポート**: `comic-text-detector` はMPSを直接サポートしていないため、テキスト検出はCPUで実行されます。OCR処理はMPSを使用します。

## トラブルシューティング

問題が発生した場合は、`docs/TROUBLESHOOTING.md` を参照してください。

## テスト

```bash
# テストを実行
python3 -m pytest tests/ -v
```

## ライセンス

MIT License

