# Confluence to Markdown

This script converts specified Confluence pages into Markdown files.

## Features

- Fetches content from multiple Confluence pages.
- Converts Confluence's HTML storage format to clean Markdown.
- Extracts metadata such as page title, space name, author, and last updated date.
- Manages target URLs in a separate `urls.txt` file.

## Setup

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Koichi73/confluence-to-markdown
    cd confluence-to-markdown
    ```

2.  **Create a virtual environment**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables**
    Create a `.env` file in the root directory and add your Confluence credentials:
    ```
    CONFLUENCE_API_TOKEN="your_api_token_here"
    CONFLUENCE_USER_NAME="your.email@example.com"
    ```

## Usage

1.  **Edit `urls.txt`**
    Add the URLs of the Confluence pages you want to convert, one URL per line.
    ```
    https://your-domain.atlassian.net/wiki/spaces/SPACEKEY/pages/12345/Page+Title
    https://your-domain.atlassian.net/wiki/pages/viewpage.action?pageId=67890
    ```

2.  **Run the script**
    ```bash
    python3 main.py
    ```

3.  **Check the output**
    The converted Markdown files will be saved in the `outputs` directory, with a timestamped filename (e.g., `confluence_data_YYYYMMDD_HHMMSS.md`).
