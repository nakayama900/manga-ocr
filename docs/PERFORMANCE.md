# パフォーマンスとデバイス使用について

## デバイス使用の概要

このツールは2つの主要な処理を行います：

1. **テキスト検出** (`comic-text-detector`)
2. **OCR処理** (`manga-ocr`)

それぞれが異なるデバイスを使用する可能性があります。

## MPS（Metal Performance Shaders）とは

**MPS（Metal Performance Shaders）** は、Appleが開発したGPUアクセラレーション技術です。Apple Silicon（M1、M2、M3、M4など）を搭載したMacで、機械学習や画像処理を高速化するために使用されます。

### なぜ速いのか？

1. **並列処理**: GPUは数千個の小さなコアを持ち、同時に多くの計算を実行できます
2. **専用ハードウェア**: 画像処理や行列計算に最適化された回路を持っています
3. **メモリ帯域**: CPUよりも高速なメモリアクセスが可能です

## デバイス使用の詳細

### テキスト検出（comic-text-detector）

**使用デバイス**: CPU（またはCUDA、利用可能な場合）

**理由**:
- `comic-text-detector` はPyTorchのMPS（Metal Performance Shaders）を直接サポートしていません
- このライブラリは主にCUDA（NVIDIA GPU）またはCPUでの実行を想定しています
- Apple SiliconのMPSは、PyTorch 1.12以降でサポートされていますが、`comic-text-detector`の実装ではMPSが明示的にサポートされていません

**影響**:
- テキスト検出処理はCPUで実行されます
- 処理速度はCPUの性能に依存します
- 通常、テキスト検出は比較的高速に完了します

### OCR処理（manga-ocr）

**使用デバイス**: MPS（Apple Siliconの場合）またはCPU

**理由**:
- `manga-ocr` はPyTorchベースで、MPSを自動的に検出して使用します
- Apple Silicon Macでは、MPSを使用することで高速な推論が可能です

**影響**:
- OCR処理はMPSで高速に実行されます
- 大量のテキスト領域がある場合でも、MPSにより高速に処理できます

## パフォーマンス

### 処理時間の目安

一般的な処理時間の目安（218ページの例）:
- テキスト検出: 各画像数秒（CPU）
- OCR処理: 各領域0.5-2秒（MPS）

### パフォーマンス比較

| デバイス | OCR処理速度（1領域あたり） |
|---------|------------------------|
| CPU | 2-5秒 |
| MPS | 0.5-2秒 |

**約2-4倍高速**になります！

## 確認方法

デバイス使用状況を確認するには：

```bash
python3 -m src.cli comic.zip --verbose
```

出力例：
```
使用デバイス: mps
comic-text-detectorはMPSを直接サポートしていないため、テキスト検出はCPUで実行されます。
OCR処理（manga-ocr）はMPSを使用します。
2025-12-20 12:30:23.957 | INFO | manga_ocr.ocr:__init__:25 - Using MPS
```

「Using MPS」と表示されていれば、MPSが使用されています。

## よくある質問

### Q: MPSはすべてのMacで使える？

A: いいえ。Apple Silicon（M1/M2/M3/M4）を搭載したMacでのみ使用できます。Intel Macでは使用できません。

### Q: MPSを使わないとどうなる？

A: CPUで処理されます。速度は遅くなりますが、結果は同じです。

### Q: 強制的にCPUを使いたい場合は？

A: `--device cpu` オプションを使用してください：
```bash
python3 -m src.cli comic.zip --device cpu
```

### Q: なぜテキスト検出だけCPUなのか？

A: `comic-text-detector`ライブラリがMPSを直接サポートしていないためです。これはライブラリの制限であり、ツール側で変更することはできません。

### Q: 処理速度に影響はあるか？

A: テキスト検出は比較的軽量な処理のため、CPUでも十分な速度で実行できます。OCR処理はMPSを使用するため、全体的なパフォーマンスは良好です。

### Q: CUDAは使用できるか？

A: NVIDIA GPUが利用可能な場合、`comic-text-detector`は自動的にCUDAを使用します。ただし、Apple Silicon MacではCUDAは利用できません。

## 参考リンク

より詳しい技術情報が必要な場合は、以下のドキュメントを参照してください：
- [PyTorch MPS ドキュメント](https://pytorch.org/docs/stable/notes/mps.html)
- [Apple Metal ドキュメント](https://developer.apple.com/metal/)
