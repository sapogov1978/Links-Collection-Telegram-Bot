import os
import json
import re
import gspread
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

def clean_urls(text):
    raw = URL_REGEX.findall(text)
    return [url.rstrip(TRAILING_CHARS) for url in raw]

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    urls = clean_urls(update.message.text)
    if not urls:
        await update.message.reply_text("🤬 No links found in the message.")
        return

    values = sheet.col_values(1)
    responses = []

    for url in urls:
        if url in values:
            responses.append(f"😥 Duplicate: {url} ignored")
        else:
            sheet.append_row([url])
            responses.append(f"✅ Added: {url}")

    await update.message.reply_text("\n".join(responses))

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()
