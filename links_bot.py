import os
import json
import re
import gspread
from urllib.parse import urlparse, urlunparse
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

def load_secret_files(filename):
    try:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"{filename} not found locally")

        with open(filename, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        return loaded_data
    
    except (FileNotFoundError, json.JSONDecodeError):
        if filename == "config.json":
            config_raw = os.environ.get("CONFIG_JSON")
            if not config_raw:
                raise Exception("CONFIG_JSON environment variable missing")
            with open("config.json", "w", encoding="utf-8") as f:
                f.write(config_raw)
            loaded_data = json.loads(config_raw)

        elif filename == "credentials.json":
            credentials_raw = os.environ.get("CREDENTIALS_JSON")
            if not credentials_raw:
                raise Exception("CREDENTIALS_JSON environment variable missing")
            with open("credentials.json", "w", encoding="utf-8") as f:
                f.write(credentials_raw)
            loaded_data = json.loads(credentials_raw)

        return loaded_data

config = load_secret_files("config.json") 
creds_file = load_secret_files("credentials.json")

TOKEN = config["telegram_token"]
SHEET_URL = config["sheet_url"]

gc = gspread.service_account(filename="credentials.json")
sheet = gc.open_by_url(SHEET_URL).sheet1

URL_REGEX = re.compile(r'https?://[^\s<>\]\),;"]+')
TRAILING_CHARS = ',.;:)]}>"\''

def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    clean = parsed._replace(query="", fragment="")
    normalized = urlunparse(clean)

    if normalized.startswith("https://www.instagram.com/") and normalized.endswith("/"):
        normalized = normalized.rstrip("/")

    return normalized

def clean_urls(text):
    raw = URL_REGEX.findall(text)
    cleaned = [url.rstrip(TRAILING_CHARS) for url in raw]
    return [normalize_url(url) for url in cleaned]

def categorize_url(url: str) -> str:
    if "instagram.com" in url:
        return "instagram"
    elif "tiktok.com" in url:
        return "tiktok"
    elif "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    else:
        return "other"

def get_or_create_sheet(sheet_title: str):
    try:
        return gc.open_by_url(SHEET_URL).worksheet(sheet_title)
    except gspread.exceptions.WorksheetNotFound:
        return gc.open_by_url(SHEET_URL).add_worksheet(title=sheet_title, rows="1000", cols="1")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    urls = clean_urls(update.message.text)
    if not urls:
        await update.message.reply_text("🤬 No links found in the message.")
        return

    categorized = {}

    for url in urls:
        category = categorize_url(url)
        categorized.setdefault(category, []).append(url)

    responses = []

    for category, url_list in categorized.items():
        ws = get_or_create_sheet(category)
        existing = ws.col_values(1)

        for url in url_list:
            if url in existing:
                responses.append(f"😥 Duplicate in {category}: {url} ignored")
            else:
                ws.append_row([url])
                responses.append(f"✅ Added to {category}: {url}")

    await update.message.reply_text("\n".join(responses))

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()
