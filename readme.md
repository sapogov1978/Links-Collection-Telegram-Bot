# Telegram Link Collector Bot

This bot receives messages with links and stores unique links into a Google Sheets document.
Made as part of a future n8n automation workflow.

## Setup

1. Create a Google Cloud Project and enable Google Sheets API.  
2. Create a Service Account and download its JSON key as `credentials.json`.  
3. Share your Google Sheet with the Service Account email with Editor permissions.  
4. Create a Telegram bot and get its token from [BotFather](https://t.me/BotFather) in Telegram.  
5. Fill in your Telegram bot token and Google Sheet URL in `config.json`, for example:
   
   ```json
    {
       "telegram_token": "YOUR_TELEGRAM_BOT_TOKEN",
       "sheet_url": "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit#gid=0"
    }
    ```
    
6. Install dependencies:
    
    ```bash
    pip install -r requirements.txt
    ```
    
7. Run the bot:
    
    ```bash
    python links_bot.py
    ```

## Features

- Detects URLs in messages.
- Checks if URL is already in Google Sheet.
- Adds new URLs; ignores duplicates.
- Replies with status messages.

## Notes

- Keep `credentials.json` secret and don't commit it to Git.
- Google Sheet must be shared with the Service Account email for write access.
