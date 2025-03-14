#!/usr/bin/env python3
# WCAG Focus Visible Checker (WCAG 2.4.7)
# ======================================
#
# 使い方 (Usage):
#   python /home/ec2-user/a11y/wcag_focus_visible_checker/wcag_focus_visible_checker.py [URL]
#
# 説明:
#   このツールはWebページをチェックして、キーボードフォーカスの可視性（WCAG 2.4.7）を
#   評価します。キーボードでタブ操作をシミュレートし、各要素がフォーカスを受けた時に
#   視覚的な表示があるかどうかを検証します。
#
# 出力:
#   - コマンドラインに詳細なレポートを表示
#     - フォーカス可視化されている要素のリスト
#     - フォーカス可視化されていない要素のリスト
#     - WCAG 2.4.7への準拠状況
#
# 必要条件:
#   - Python 3.7以上
#   - Chrome/Chromiumブラウザ
#   - ChromeDriver
#   - Anthropic API キー（config.pyに設定）
#   - 依存パッケージ（requirements.txtに記載）
import sys
import time
import json
import base64
import os
import tempfile
import shutil
import anthropic
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import ANTHROPIC_API_KEY, CHROME_BINARY_PATH, CHROME_DRIVER_PATH, DEBUG

def setup_driver():
    """
    Set up and return a Chrome WebDriver instance
    """
    options = Options()
    # サーバー環境では必ずヘッドレスモードで実行
    # Use the new headless mode - don't set the deprecated options.headless property
    options.binary_location = CHROME_BINARY_PATH
    options.add_argument("--window-size=1366,768")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-software-rasterizer')
    # Don't use a fixed debugging port to avoid conflicts
    # options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--disable-infobars')
    options.add_argument('--headless=new')
    options.add_argument('--disable-setuid-sandbox')
    
    # Don't use single-process as it can cause issues with DevTools
    # options.add_argument('--single-process')
    
    # Add these arguments to help with the DevToolsActivePort issue
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-prompt-on-repost')
    options.add_argument('--disable-sync')
    
    # Use a dedicated temporary directory for Chrome data
    temp_dir = tempfile.mkdtemp()
    options.add_argument(f'--user-data-dir={temp_dir}')
    options.add_argument('--data-path=' + os.path.join(temp_dir, 'data'))
    options.add_argument('--homedir=' + os.path.join(temp_dir, 'home'))
    options.add_argument('--disk-cache-dir=' + os.path.join(temp_dir, 'cache'))

    # ChromeDriverの設定
    service = Service(executable_path=CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    return driver, temp_dir

def cleanup_temp_dir(temp_dir):
    """
    Clean up temporary directory after the driver is closed
    """
    try:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"一時ディレクトリを削除しました: {temp_dir}")
    except Exception as e:
        print(f"警告: 一時ディレクトリの削除に失敗しました: {e}")

def get_focusable_elements(driver):
    """
    Get a list of potentially focusable elements
    """
    # List of commonly focusable elements
    selectors = [
        "a[href]", "button", "input", "select", "textarea", 
        "[tabindex]:not([tabindex='-1'])", "[contenteditable='true']",
        "details", "summary", "iframe", "object", "embed", "audio[controls]", 
        "video[controls]", "[role='button']", "[role='link']", "[role='checkbox']",
        "[role='radio']", "[role='tab']", "[role='menuitem']", "[role='combobox']"
    ]
    
    # Join all selectors with commas
    combined_selector = ", ".join(selectors)
    
    # Find all potentially focusable elements
    elements = driver.find_elements(By.CSS_SELECTOR, combined_selector)
    
    print(f"フォーカス可能な要素を {len(elements)} 個見つけました")
    return elements

def check_focus_visibility(url):
    """
    Check focus visibility on a webpage by tabbing through interactive elements
    """
    try:
        print("Chrome WebDriverを設定中...")
        driver, temp_dir = setup_driver()
        print(f"Chrome WebDriverの設定が完了しました。一時ディレクトリ: {temp_dir}")
    except Exception as e:
        print(f"Chrome WebDriverの設定エラー: {e}")
        if "DevToolsActivePort file doesn't exist" in str(e):
            print("\nDevToolsActivePortエラーのトラブルシューティング:")
            print("1. Chromeがインストールされており、実行可能であることを確認してください")
            print("2. 実行中のChromeプロセスがないか確認してください")
            print("3. config.pyのChrome実行ファイルパスが正しいか確認してください")
            print(f"4. 現在のChrome実行ファイルパス: {CHROME_BINARY_PATH}")
            print(f"5. 現在のChromeDriverパス: {CHROME_DRIVER_PATH}")
            print("6. 既存のChromeプロセスを終了してみてください: pkill -f chrome")
        raise
    
    try:
        # Navigate to URL
        print(f"URLに移動中: {url}")
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print("ページの読み込みが完了しました")
        
        # Get initial page source and screenshot for reference
        initial_source = driver.page_source
        initial_screenshot = take_screenshot(driver)
        
        # Initialize focus results
        focus_results = []
        
        # Reset focus to the top of the page
        body = driver.find_element(By.TAG_NAME, "body")
        body.click()
        body.send_keys(Keys.HOME)
        
        # Loop through the page by pressing Tab
        tab_index = 0
        previously_focused_elements = set()
        max_tabs = 100  # Limit to prevent infinite loops
        
        while tab_index < max_tabs:
            # Capture before pressing Tab
            before_tab_screenshot = take_screenshot(driver)
            
            # Press Tab to focus the next element
            ActionChains(driver).send_keys(Keys.TAB).perform()
            time.sleep(0.5)  # Short delay to let focus effects render
            
            # Get the currently focused element
            active_element = driver.execute_script("return document.activeElement;")
            
            # Get element details
            element_tag = driver.execute_script("return document.activeElement.tagName;")
            element_type = driver.execute_script("return document.activeElement.type || '';")
            element_id = driver.execute_script("return document.activeElement.id || '';")
            element_class = driver.execute_script("return document.activeElement.className || '';")
            element_text = driver.execute_script("return document.activeElement.textContent || '';")
            element_role = driver.execute_script("return document.activeElement.getAttribute('role') || '';")
            
            # Try to get a useful identifier
            element_identifier = element_id or element_class or element_text[:50] or f"{element_tag}[{tab_index}]"
            
            # Get XPath for the focused element
            try:
                element_xpath = generate_xpath(driver, active_element)
            except:
                element_xpath = "Unknown"
            
            # Check if we've cycled back to an element we've seen before
            element_signature = f"{element_tag}_{element_id}_{element_class}_{element_xpath}"
            if element_signature in previously_focused_elements:
                print(f"インデックス {tab_index} で以前フォーカスした要素に戻りました。タブシーケンスを停止します。")
                break
            
            previously_focused_elements.add(element_signature)
            
            # Take screenshot with the element focused
            after_tab_screenshot = take_screenshot(driver)
            
            # Capture element details
            element_info = {
                "tab_index": tab_index,
                "element_tag": element_tag,
                "element_type": element_type,
                "element_id": element_id,
                "element_class": element_class,
                "element_text": element_text[:100] if element_text else "",
                "element_role": element_role,
                "element_xpath": element_xpath,
                "before_tab_screenshot": before_tab_screenshot,
                "after_tab_screenshot": after_tab_screenshot
            }
            
            focus_results.append(element_info)
            print(f"要素を処理しました {tab_index}: {element_tag} ({element_identifier})")
            
            tab_index += 1
        
        # Process results
        return process_focus_results(focus_results, initial_screenshot, url)
        
    finally:
        driver.quit()
        cleanup_temp_dir(temp_dir)

def generate_xpath(driver, element):
    """Generate a unique XPath for an element"""
    return driver.execute_script("""
    function getPathTo(element) {
        if (element.id !== '')
            return '//*[@id="' + element.id + '"]';
        if (element === document.body)
            return '/html/body';

        var index = 0;
        var siblings = element.parentNode.childNodes;
        for (var i = 0; i < siblings.length; i++) {
            var sibling = siblings[i];
            if (sibling === element)
                return getPathTo(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (index + 1) + ']';
            if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                index++;
        }
    }
    return getPathTo(arguments[0]);
    """, element)

def take_screenshot(driver):
    """Take a screenshot and convert to base64 for storage"""
    screenshot = driver.get_screenshot_as_png()
    buffered = BytesIO(screenshot)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def process_focus_results(focus_results, initial_screenshot, url):
    """
    Analyze focus results to determine visibility
    """
    # Prepare batches of elements for analysis (limit of 5 per batch for better image handling)
    batch_size = 5
    batches = [focus_results[i:i+batch_size] for i in range(0, len(focus_results), batch_size)]
    
    all_analyzed_results = []
    
    for batch_idx, batch in enumerate(batches):
        print(f"フォーカス結果のバッチ {batch_idx+1}/{len(batches)} を解析中")
        try:
            analyzed_batch = analyze_focus_batch(batch, initial_screenshot, url)
            if analyzed_batch:
                all_analyzed_results.extend(analyzed_batch)
            else:
                print(f"警告: バッチ {batch_idx+1} の解析結果がありません。スキップします。")
        except Exception as e:
            print(f"エラー: バッチ {batch_idx+1} の解析中に問題が発生しました: {e}")
            print("バッチをスキップして続行します...")
    
    # Categorize results
    visible_focus_elements = []
    invisible_focus_elements = []
    
    for result in all_analyzed_results:
        # 結果が正しい形式かチェック
        if 'analysis' not in result:
            print(f"警告: 要素 {result.get('tab_index', '不明')} の分析結果が不完全です。スキップします。")
            continue
            
        if result['analysis'].get('focus_visible', False):
            visible_focus_elements.append(result)
        else:
            invisible_focus_elements.append(result)
    
    # Create final report
    final_report = {
        "url": url,
        "total_focusable_elements": len(all_analyzed_results),
        "visible_focus_elements": len(visible_focus_elements),
        "invisible_focus_elements": len(invisible_focus_elements),
        "visible_elements": visible_focus_elements,
        "invisible_elements": invisible_focus_elements,
        "wcag_2_4_7_compliant": len(invisible_focus_elements) == 0
    }
    
    return final_report

def analyze_focus_batch(focus_batch, initial_screenshot, url):
    """
    Use Claude to analyze focus visibility for a batch of elements
    """
    client = anthropic.Anthropic(
        api_key=ANTHROPIC_API_KEY,
    )
    
    elements_data = []
    
    # Prepare element data without the full screenshots
    for element in focus_batch:
        element_data = {
            "tab_index": element["tab_index"],
            "element_tag": element["element_tag"],
            "element_type": element["element_type"],
            "element_id": element["element_id"],
            "element_class": element["element_class"],
            "element_text": element["element_text"],
            "element_role": element["element_role"],
            "element_xpath": element["element_xpath"]
        }
        elements_data.append(element_data)
    
    # Format the elements data as JSON
    elements_json = json.dumps({"elements": elements_data}, ensure_ascii=False, indent=2)
    
    # Create media blocks for the images
    media_blocks = []
    for i, element in enumerate(focus_batch):
        # Add before focus image
        media_blocks.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": element["before_tab_screenshot"]
            }
        })
        # Add image label
        media_blocks.append({
            "type": "text",
            "text": f"画像 {i*2+1}: 要素 {element['tab_index']} ({element['element_tag']}) にフォーカスする前"
        })
        
        # Add after focus image
        media_blocks.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": element["after_tab_screenshot"]
            }
        })
        
        # Add image label
        media_blocks.append({
            "type": "text",
            "text": f"画像 {i*2+2}: 要素 {element['tab_index']} ({element['element_tag']}) にフォーカスした後"
        })
    
    # Example output format
    format_example = '''{
  "elements": [
    {
      "tab_index": 0,
      "element_tag": "A",
      "element_type": "",
      "element_id": "main-logo",
      "element_class": "navbar-brand",
      "element_text": "Home",
      "element_role": "",
      "element_xpath": "/html/body/header/nav/a[1]",
      "analysis": {
        "focus_visible": true,
        "focus_indicator_description": "Blue outline around the element with 2px thickness",
        "compliance_techniques": [
          "G165: Using the default focus indicator for the platform",
          "C15: Using CSS to change the presentation of a user interface component when it receives focus"
        ],
        "recommendation": "Current implementation is compliant with WCAG 2.4.7"
      }
    }
  ]
}'''
    
    # Create the prompt with task description and examples
    prompt = f"""# あなたはWCAG 2.4.7 フォーカス可視性の評価を専門とするアクセシビリティテストの専門家です。あなたの任務は、要素がキーボードフォーカスを受けた時に可視的なフォーカス表示があるかどうかを分析することです。

# WCAG 2.4.7 フォーカス可視性の要件:
キーボード操作可能なユーザーインターフェースには、キーボードフォーカスインジケータが視覚的に確認できる操作モードがあること。

# 各要素について、2つの画像が表示されます:
1. 要素がフォーカスを受ける前（前のタブの後）
2. 要素がフォーカスを受けた後（現在のタブ）

これらの画像を比較して、要素がキーボードフォーカスを受けた時に視覚的なフォーカス表示があるかどうかを判断してください。

# 一般的なフォーカス表示には以下が含まれます:
- アウトライン（実線、点線、破線）
- 背景色の変化
- 境界線の変化
- ボックスシャドウ
- テキスト色の変化
- 下線やその他の装飾
- サイズや形状の変化

# 各要素について、以下を判断してください:
1. 視覚的なフォーカス表示があるか？ (true/false)
2. 表示がある場合、そのフォーカス表示を説明してください
3. 使用されているWCAG技術を特定してください:
   - G165: プラットフォームのデフォルトフォーカス表示を使用
   - G195: 作成者が提供する視覚的なフォーカス表示を使用
   - C15: フォーカスを受けた時にCSSで表示を変更
   - C40: 十分なコントラストを持つ二色のフォーカス表示を作成
   - SCR31: スクリプトを使用してフォーカス時に背景色または境界線を変更
   - F78: フォーカス表示を削除または非表示にするスタイリングの失敗

# 以下の画像は、フォーカス可視性のテスト対象となる要素を示しています。
# 「フォーカス前」と「フォーカス後」の画像のペアを注意深く分析してください。

# テスト対象のページ: {url}

# 回答のフォーマット:
{format_example}

# 以下の要素を分析してください:
{elements_json}"""

    print("Claudeにフォーカス可視性分析リクエストを送信中...")
    
    try:
        # Create message with text and images
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4096,
            system="あなたはWCAGコンプライアンス評価、特にキーボードユーザー向けのフォーカス可視性に特化したアクセシビリティテストの専門家です。",
            messages=[
                {"role": "user", "content": media_blocks + [{"type": "text", "text": prompt}]}
            ]
        )
        
        response_text = str(message.content[0].text)
        print("\n=== Claudeの分析結果 ===")
        if DEBUG:
            print(response_text)
    except Exception as e:
        print(f"\nエラー: Claudeへのリクエスト中に問題が発生しました: {e}")
        print("このバッチはスキップします。")
        return None
    
    try:
        # Extract and parse JSON from response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx]
            json_str = json_str.replace("'", '"').replace('\\n', '\n').strip()
            
            if DEBUG:
                print("=== フォーマット済みJSONデータ ===")
                print(json_str)
            
            try:
                result = json.loads(json_str)
                if 'elements' in result:
                    print(f"{len(result['elements'])}個の要素の分析が完了しました")
                    return result['elements']
                else:
                    print("警告: 応答にelementsフィールドがありません")
            except json.JSONDecodeError as je:
                print(f"エラー: JSONデータの解析に失敗しました: {je}")
                if DEBUG:
                    print("=== 問題のあるJSONデータ ===")
                    print(json_str[:500] + "..." if len(json_str) > 500 else json_str)
        else:
            print("警告: 応答からJSONデータを抽出できませんでした")
    except Exception as e:
        print(f"エラー: Claudeの応答の処理中に問題が発生しました: {e}")
    
    return None

# Removed the save_results_as_html function as it's no longer needed for command line only output

def main():
    if len(sys.argv) != 2:
        print("Usage: python wcag_focus_visible_checker.py url")
        sys.exit(1)

    url = sys.argv[1]
    
    try:
        # Check focus visibility
        print(f"{url} のフォーカス可視性チェックを開始")
        results = check_focus_visibility(url)
        
        # Print detailed results to console
        print("\n======================================")
        print("WCAG 2.4.7 フォーカス可視性 分析レポート")
        print("======================================")
        print(f"URL: {url}")
        print(f"フォーカス可能な要素の合計: {results['total_focusable_elements']}")
        print(f"フォーカス可視化されている要素: {results['visible_focus_elements']}")
        print(f"フォーカス可視化されていない要素: {results['invisible_focus_elements']}")
        print(f"WCAG 2.4.7 準拠状況: {'準拠' if results['wcag_2_4_7_compliant'] else '非準拠'}")
        
        # Print elements without visible focus
        if not results['wcag_2_4_7_compliant']:
            print("\n== フォーカス可視化されていない要素 ==")
            for element in results['invisible_elements']:
                try:
                    print(f"\n要素 {element['tab_index']}: {element['element_tag']}")
                    print(f"  ID: {element.get('element_id', '') or 'なし'}")
                    print(f"  クラス: {element.get('element_class', '') or 'なし'}")
                    print(f"  テキスト: {element.get('element_text', '') or 'なし'}")
                    print(f"  XPath: {element.get('element_xpath', 'なし')}")
                    
                    if 'analysis' in element:
                        if 'focus_indicator_description' in element['analysis']:
                            print(f"  分析: {element['analysis']['focus_indicator_description']}")
                        else:
                            print("  分析: 情報なし")
                            
                        print(f"  推奨事項: {element['analysis'].get('recommendation', 'この要素にフォーカス表示を追加してください')}")
                    else:
                        print("  分析: 情報なし")
                        print("  推奨事項: この要素にフォーカス表示を追加してください")
                except Exception as e:
                    print(f"  エラー: この要素の表示中に問題が発生しました: {e}")
        
        # Print elements with visible focus
        print("\n== フォーカス可視化されている要素 ==")
        for element in results['visible_elements']:
            try:
                print(f"\n要素 {element['tab_index']}: {element['element_tag']}")
                print(f"  ID: {element.get('element_id', '') or 'なし'}")
                print(f"  クラス: {element.get('element_class', '') or 'なし'}")
                print(f"  テキスト: {element.get('element_text', '') or 'なし'}")
                
                if 'analysis' in element and 'focus_indicator_description' in element['analysis']:
                    print(f"  フォーカス表示: {element['analysis']['focus_indicator_description']}")
                else:
                    print("  フォーカス表示: 情報なし")
                    
                if 'analysis' in element and 'compliance_techniques' in element['analysis']:
                    print("  使用されている技術:")
                    for technique in element['analysis']['compliance_techniques']:
                        print(f"    - {technique}")
            except Exception as e:
                print(f"  エラー: この要素の表示中に問題が発生しました: {e}")
        
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()