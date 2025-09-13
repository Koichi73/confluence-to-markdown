import requests
import os
import pytz
import re
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from dotenv import load_dotenv
from markdownify import markdownify as md


def get_page(page_id, base_url, session, expansions=None):
    """
    指定されたページの情報を取得する。
    """
    if expansions is None:
        expansions = "body.storage,version,ancestors,history.createdBy,space"

    url = f"{base_url}/rest/api/content/{page_id}?expand={expansions}"
    headers = {
        "Accept": "application/json"
    }

    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()  # HTTPエラーが発生した場合に例外を発生させる
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] ページ情報取得失敗: {e}")
        return None


def extract_data_from_html(html_content):
    """
    ConfluenceのHTMLコンテンツからMarkdownテキストを抽出する。

    Args:
        html_content (str): Confluence APIから取得したHTMLコンテンツ

    Returns:
        str: Markdownテキスト
    """
    markdown_text = md(html_content, heading_style="ATX")
    return markdown_text


def get_display_name(account_id, session, base_url, cache={}):
    """
    Confluence API からユーザーの表示名を取得（キャッシュ対応）

    Args:
        account_id (str): ユーザーの Account ID
        session (requests.Session): 認証済みセッション
        base_url (str): ConfluenceのベースURL
        cache (dict): 取得済みのユーザーデータキャッシュ

    Returns:
        str: ユーザーの表示名（取得できない場合は Account ID をそのまま返す）
    """
    if not account_id:
        return "不明な作成者"
    if account_id in cache:
        return cache[account_id]

    url = f"{base_url}/rest/api/user?accountId={account_id}"
    response = session.get(url)

    if response.status_code == 200:
        display_name = response.json().get("displayName", account_id)
        cache[account_id] = display_name  # キャッシュに保存
        return display_name
    else:
        print(f"⚠️ ユーザー情報取得失敗: {account_id} ({response.status_code})")
        return account_id  # エラー時は Account ID をそのまま返す


def parse_confluence_url(url):
    """
    ConfluenceのURLからbase_urlとpage_idを抽出する。
    """
    try:
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/wiki"

        # /pages/viewpage.action?pageId=... 形式
        if 'viewpage.action' in parsed_url.path:
            query_params = parse_qs(parsed_url.query)
            page_id = query_params.get('pageId', [None])[0]
            if page_id:
                return base_url, page_id

        # /spaces/.../pages/<pageId>... 形式
        match = re.search(r'/pages/(\d+)', parsed_url.path)
        if match:
            page_id = match.group(1)
            return base_url, page_id

        print(f"[ERROR] URLからページIDを抽出できませんでした: {url}")
        return None, None
    except Exception as e:
        print(f"[ERROR] URLの解析中にエラーが発生しました: {url}, {e}")
        return None, None


def process_pages_from_urls(page_urls, session):
    """指定されたURLのページを取得し、Markdownファイルに追記する。"""

    # 日本時間の現在時刻を取得し、ファイル名用にフォーマット
    jst = pytz.timezone("Asia/Tokyo")
    timestamp = datetime.now(jst).strftime("%Y%m%d_%H%M%S")

    save_directory = "./outputs"
    os.makedirs(save_directory, exist_ok=True)
    markdown_file_path = os.path.join(save_directory, f"confluence_data_{timestamp}.md")

    user_cache = {}  # ユーザーキャッシュを初期化

    with open(markdown_file_path, 'a', encoding='utf-8') as md_file:
        for url in page_urls:
            base_url, page_id = parse_confluence_url(url)
            if not page_id or not base_url:
                continue

            page = get_page(page_id, base_url, session)

            if page:
                page_contents = page.get("body", {}).get("storage", {}).get("value", "")
                text_content = extract_data_from_html(page_contents)

                creator = page.get("history", {}).get("createdBy", {})
                creator_account_id = creator.get('accountId')
                creator_display_name = get_display_name(creator_account_id, session, base_url, cache=user_cache)

                page_title = page.get('title', 'No Title')
                space_info = page.get('space', {})
                space_key = space_info.get('key')
                space_name = space_info.get('name', space_key)

                page_link = page.get('_links', {}).get('webui', url)
                last_updated = page.get('version', {}).get('friendlyWhen', 'N/A')

                markdown_content = f"# {page_title}\n"
                markdown_content += f"URL: {page_link}\n"
                markdown_content += f"スペース: {space_name}\n"
                markdown_content += f"作成者: {creator_display_name}\n"
                markdown_content += f"最終更新日: {last_updated}\n\n"
                markdown_content += f"{text_content}\n\n"

                md_file.write(markdown_content)

                print("-----------------------")
                print(f"{markdown_content}")
                print(f"Markdownファイルに追記しました (ページ: {page_title})\n\n")
            else:
                print(f"ページを取得できませんでした: {url}")

def main():
    # 環境変数を読み込み
    load_dotenv()
    api_token = os.getenv('CONFLUENCE_API_TOKEN')
    user_name = os.getenv('CONFLUENCE_USER_NAME')

    if not api_token or not user_name:
        print("[ERROR] .envファイルにCONFLUENCE_API_TOKENとCONFLUENCE_USER_NAMEを設定してください。")
        return

    session = requests.Session()
    session.auth = (user_name, api_token)

    # URLリストをファイルから読み込む
    url_file_path = "urls.txt"
    try:
        with open(url_file_path, 'r', encoding='utf-8') as f:
            # 空行や前後の空白を除外してリスト化
            page_urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[ERROR] URLファイルが見つかりません: {url_file_path}")
        print(f"'{url_file_path}'を作成し、1行に1つのURLを記述してください。")
        return

    if not page_urls:
        print(f"読み取るConfluenceページのURLが指定されていません。'{url_file_path}'にURLを記述してください。")
        return

    process_pages_from_urls(page_urls, session)


if __name__ == "__main__":
    main()