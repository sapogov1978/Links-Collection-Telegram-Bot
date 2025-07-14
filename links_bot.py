import re
import json
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# load token and sheet URL from config file
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

TOKEN = config["telegram_token"]
GOOGLE_SHEET_URL = config["sheet_url"]

# Google Service Account authorization
# Ensure you have a credentials.json file with the service account key
scope = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_file("credentials.json", scopes=scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_url(GOOGLE_SHEET_URL).sheet1

# links parsing template
URL_REGEX = re.compile(r'https?://[^\s<>\]\),;"]+')
TRAILING_CHARS = ',.;:)]}>"\''

#clean up links from trailing characters
def clean_urls(text):
    raw = URL_REGEX.findall(text)
    return [url.rstrip(TRAILING_CHARS) for url in raw]

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    urls = clean_urls(update.message.text)
    if not urls:
        await update.message.reply_text("Links not found in message")
        return

    values = sheet.col_values(1)
    responses = []

    for url in urls:
        if url in values:
            responses.append(f"Duplicate: {url} ignored.")
        else:
            sheet.append_row([url])
            responses.append(f"Added: {url}")

    await update.message.reply_text("\n".join(responses))

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()
