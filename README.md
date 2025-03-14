# WCAG Focus Visible Checker

## Overview
WCAG Focus Visible Checker is a tool that evaluates web pages for compliance with WCAG 2.4.7 (Focus Visible) accessibility requirements. This tool simulates keyboard tabbing through interactive elements on a webpage and uses AI-powered image analysis to determine whether each element displays a visible focus indicator when it receives keyboard focus.

## Installation
1. Clone the repository:
   ```
   git clone https://github.com/daishir0/wcag_focus_visible_checker
   cd wcag_focus_visible_checker
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install Chrome/Chromium browser if not already installed.

4. Download the appropriate ChromeDriver for your Chrome version from [ChromeDriver website](https://chromedriver.chromium.org/downloads).

5. Create a `config.py` file with the following content:
   ```python
   ANTHROPIC_API_KEY = "your_anthropic_api_key"
   CHROME_BINARY_PATH = "/path/to/chrome"  # e.g., "/usr/bin/google-chrome"
   CHROME_DRIVER_PATH = "/path/to/chromedriver"  # e.g., "/usr/local/bin/chromedriver"
   DEBUG = False  # Set to True for verbose output
   ```

## Usage
Run the tool by providing a URL to check:
```
python wcag_focus_visible_checker.py https://example.com
```

The tool will:
1. Open the webpage in a headless Chrome browser
2. Tab through all focusable elements
3. Take screenshots before and after focusing each element
4. Analyze the screenshots to determine if focus is visibly indicated
5. Generate a detailed report showing:
   - Total number of focusable elements
   - Elements with visible focus indicators
   - Elements without visible focus indicators
   - Overall WCAG 2.4.7 compliance status

## Notes
- The tool requires an Anthropic API key to use Claude for image analysis.
- The analysis process may take several minutes depending on the number of focusable elements on the page.
- For accurate results, ensure the ChromeDriver version matches your Chrome browser version.
- The tool creates temporary directories for Chrome data which are automatically cleaned up after execution.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---

# WCAG フォーカス可視チェッカー

## 概要
WCAG フォーカス可視チェッカーは、ウェブページがWCAG 2.4.7（フォーカス可視）アクセシビリティ要件に準拠しているかを評価するツールです。このツールは、ウェブページ上のインタラクティブな要素をキーボードのタブ操作でシミュレートし、AI画像分析を使用して、各要素がキーボードフォーカスを受けた時に視覚的なフォーカス表示があるかどうかを判断します。

## インストール方法
1. リポジトリをクローンします：
   ```
   git clone https://github.com/daishir0/wcag_focus_visible_checker
   cd wcag_focus_visible_checker
   ```

2. 必要な依存関係をインストールします：
   ```
   pip install -r requirements.txt
   ```

3. Chrome/Chromiumブラウザがインストールされていない場合はインストールします。

4. お使いのChromeバージョンに適合するChromeDriverを[ChromeDriverウェブサイト](https://chromedriver.chromium.org/downloads)からダウンロードします。

5. 以下の内容で`config.py`ファイルを作成します：
   ```python
   ANTHROPIC_API_KEY = "あなたのAnthropic APIキー"
   CHROME_BINARY_PATH = "/Chromeへのパス"  # 例："/usr/bin/google-chrome"
   CHROME_DRIVER_PATH = "/ChromeDriverへのパス"  # 例："/usr/local/bin/chromedriver"
   DEBUG = False  # 詳細な出力が必要な場合はTrueに設定
   ```

## 使い方
チェックするURLを指定してツールを実行します：
```
python wcag_focus_visible_checker.py https://example.com
```

このツールは以下を行います：
1. ヘッドレスChromeブラウザでウェブページを開く
2. フォーカス可能なすべての要素をタブで移動
3. 各要素にフォーカスする前と後のスクリーンショットを撮影
4. スクリーンショットを分析してフォーカスが視覚的に表示されているかを判断
5. 詳細なレポートを生成：
   - フォーカス可能な要素の総数
   - フォーカス表示がある要素
   - フォーカス表示がない要素
   - WCAG 2.4.7への全体的な準拠状況

## 注意点
- このツールは画像分析にClaudeを使用するため、Anthropic APIキーが必要です。
- 分析プロセスは、ページ上のフォーカス可能な要素の数によって数分かかる場合があります。
- 正確な結果を得るために、ChromeDriverのバージョンがお使いのChromeブラウザのバージョンと一致していることを確認してください。
- このツールはChromeデータ用の一時ディレクトリを作成し、実行後に自動的にクリーンアップします。

## ライセンス
このプロジェクトはMITライセンスの下でライセンスされています。詳細はLICENSEファイルを参照してください。