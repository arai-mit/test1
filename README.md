# 経理実務向け PDF整理ツール

請求書、給与資料、会計資料などのPDFを、**外部へ送信せずPC内だけで**整理するWindows向けデスクトップアプリです。

## アプリを使う方

Python、PowerShell、コマンドプロンプト等のインストールや操作は不要です。

1. **[最新版をダウンロード](../../releases/latest/download/%E7%B5%8C%E7%90%86PDF%E6%95%B4%E7%90%86%E3%83%84%E3%83%BC%E3%83%AB_Windows.zip)**をクリック（または [Releases](../../releases) を開く）
2. 最新版の「`経理PDF整理ツール_Windows.zip`」をダウンロード
3. ZIPを展開
4. 展開先の「`経理PDF整理ツール.exe`」をダブルクリック

> **注意:** GitHubが表示する「Source code (zip)」ではなく、必ず「`経理PDF整理ツール_Windows.zip`」をダウンロードしてください。

展開後のフォルダーに必要な実行環境が含まれているため、Pythonが入っていないWindows PCでも利用できます。PDFの処理はPC内だけで完結し、元PDFは変更しません。

---

## 開発者向け

請求書、給与資料、会計資料などのPDFを、**外部へ送信せずPC内だけで**整理するWindows向けデスクトップアプリです。元PDFを変更せず、ページデータを直接コピーするため、文字や画像を再圧縮しません。サムネイル生成以外に画像化は行いません。

## 実装済み機能

- ボタン、複数選択、画面へのドラッグ＆ドロップによるPDF追加
- 日本語ファイル名、ページ数、3段階サイズのページサムネイル
- Ctrl/Shiftによるページ複数選択、ドラッグによるページ／PDF順の変更
- 選択位置の前後、範囲指定、指定ページ数ごと、1ページごとの分割
- 90度（左右）／180度回転、複数ページ削除、名前変更、PDF結合
- 分割・結合結果を「作業中PDF」として保存前に編集
- 選択保存／一括保存、同名時の上書き・別名・キャンセル
- 削除、回転、並び替え、分割、結合の「元に戻す」（`Ctrl+Z`）
- パスワード保護、破損PDF、範囲指定、Windows禁止文字などの日本語エラー表示

すべての処理は `pypdf` と `PyMuPDF` によりローカルで行います。外部API、通信、クラウド、一時PDFファイルは使用しません。

## 開発環境で起動

Python 3.11以上を推奨します。PowerShellで次を実行してください。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python run_app.py
```

基本操作は、PDFをドロップし、中央でページを確認・編集してから、右下の「選択PDFを保存」または「すべて保存」です。元ファイルと同じフォルダが保存画面の初期位置になります。左の一覧順が結合順です。

## テスト

```powershell
python -m pytest
```

テストでは、PDFの読込・全分割方式・結合・回転保存・禁止ファイル名・Undo、および元ファイルが変化しないことを確認します。

## Windows用exeを作成

Windows上の仮想環境で以下を実行します（Windows用exeはWindows上でビルドしてください）。

```powershell
python -m pip install -r requirements-dev.txt
pyinstaller --noconfirm --clean pdf-organizer.spec
```

`dist\経理PDF整理ツール.exe` が生成されます。クリーンなWindows PCで、読込・保存・日本語パスを確認してください。

## リリース

`v1.0.0`のようなバージョンタグをpushすると、GitHub ActionsがWindows上でテストとPyInstallerビルドを行い、「`経理PDF整理ツール_Windows.zip`」をGitHub Releaseに添付します。Actionsの「Windows完成版をリリース」から、バージョンタグを指定して手動実行することもできます。テストまたはビルドが失敗した場合、Releaseは作成されません。

改ざん検知とWindowsの警告抑制のため、実運用では組織のコード署名証明書による署名とウイルススキャンを推奨します。顧客資料そのものは同梱しないでください。

## 今後追加できる機能

- 暗号化PDFのパスワード入力（パスワードを保存しない設計）
- ページの拡大プレビュー、分割点マーカーの常時表示
- 定型ファイル名テンプレート、保存前の重複名一括解決
- Windowsインストーラー、組織用コード署名
