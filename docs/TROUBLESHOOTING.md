# トラブルシューティングガイド

## よくある問題と解決方法

### 1. モデルファイルが見つからない

**エラーメッセージ:**
```
comic-text-detector のモデルファイルが見つかりません。
```

**解決方法:**
1. モデルファイルをダウンロード:
   - [manga-image-translator 最新リリースページ](https://github.com/zyddnys/manga-image-translator/releases/latest)
   - [manga-image-translator beta-0.3 リリースページ](https://github.com/zyddnys/manga-image-translator/releases/tag/beta-0.3)
   - または [Google Drive](https://drive.google.com/drive/folders/1cTsXP5NYTCjhPVxwScdhxqJleHuIOyXG?usp=sharing)

2. モデルファイルを配置:
   ```
   vendor/comic-text-detector/data/comictextdetector.pt
   ```

詳細は `README.md` を参照してください。

### 2. MPSが利用できない

**エラーメッセージ:**
```
MPSはcomic-text-detectorでサポートされていません。CPUを使用します。
```

**説明:**
- `comic-text-detector` はMPSを直接サポートしていません
- テキスト検出はCPUで実行されます
- OCR処理（`manga-ocr`）はMPSを使用します

**対処:**
- これは正常な動作です。CPUで処理が継続されます。

### 3. テキスト領域が検出されない

**症状:**
- 出力ファイルにテキストが含まれない
- または、画像全体が1つの領域として扱われる

**考えられる原因:**
1. 画像にテキストが含まれていない
2. テキストが小さすぎる、またはコントラストが低い
3. モデルファイルが正しく読み込まれていない

**対処:**
- `--verbose` オプションで詳細ログを確認
- モデルファイルのパスを確認
- 画像の品質を確認

### 4. メモリ不足エラー

**エラーメッセージ:**
```
RuntimeError: CUDA out of memory
```

**解決方法:**
1. より小さなZipファイルに分割して処理
2. `--device cpu` を指定してCPUを使用
3. システムのメモリを確認

### 5. 一時ディレクトリのエラー

**エラーメッセージ:**
```
FileNotFoundError: No such file or directory
```

**解決方法:**
- `--temp-dir` オプションで明示的に一時ディレクトリを指定
- ディスク容量を確認

### 6. 依存ライブラリのエラー

**エラーメッセージ:**
```
ModuleNotFoundError: No module named 'xxx'
```

**解決方法:**
```bash
pip install -r requirements.txt
```

### 7. NumPyのバージョンエラー

**エラーメッセージ:**
```
AttributeError: module 'numpy' has no attribute 'bool8'
```

**解決方法:**
- `comic-text-detector` はNumPy 2.0と互換性がありません
- `requirements.txt` でNumPy 1.xが指定されていることを確認
- 再インストール: `pip install "numpy<2.0.0"`

### 8. 処理が非常に遅い

**対処:**
- MPSが使用されているか確認（`--verbose`で確認）
- 大量の画像がある場合は、処理に時間がかかります
- CPU使用率を確認

### 9. 出力ファイルが生成されない

**確認事項:**
1. エラーメッセージを確認
2. 出力ディレクトリの書き込み権限を確認
3. `--output-dir` オプションで明示的に指定

### 10. 日本語ファイル名のエラー

**症状:**
- ファイル名に日本語が含まれている場合にエラー

**対処:**
- ファイル名を英数字に変更するか、パスを引用符で囲む
- 例: `python3 -m src.cli 'ファイル名.zip'`

## ログの確認方法

詳細なログを確認するには:
```bash
python3 -m src.cli comic.zip --verbose
```

エラーの詳細を確認するには:
```bash
python3 -m src.cli comic.zip --verbose 2>&1 | tee error.log
```

## サポート

問題が解決しない場合は、以下を確認してください:
1. Python バージョン（3.10+）
2. 依存ライブラリのバージョン
3. システム要件（Apple Silicon Mac）
4. エラーログの全文

