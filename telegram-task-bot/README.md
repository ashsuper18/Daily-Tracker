# 🤖 Daily Task Tracker Bot

A Telegram bot that automatically tracks your daily tasks in Google Sheets.

## ✨ Features

- 📝 Automatically parses task messages
- 📊 Updates Google Sheets in real-time
- 🔄 Detects task status (Done/In Progress)
- ☁️ Runs 24/7 in the cloud
- 🌍 Access from anywhere

## 🚀 How to Use

1. Message the bot: @TaskAi2bot
2. Send your task updates:
   - "Completed the sales report"
   - "Working on project planning"
   - "Finished client meeting"

## 📊 Google Sheet

Your tasks are automatically saved to:
https://docs.google.com/spreadsheets/d/14pBuj-z7mbUFIuCmV-AGkYAj584rbFhT9QsgAQtYFyk/edit

## 🔧 Environment Variables

Required for Railway deployment:

```
TELEGRAM_BOT_TOKEN=your_bot_token
GOOGLE_SHEETS_ID=your_sheet_id
GOOGLE_SHEETS_CREDENTIALS=your_service_account_json
PORT=8000
```

## 📱 Bot Commands

- `/start` - Welcome message and instructions
- `/status` - Check bot and Google Sheets connection

---

**Built for Railway deployment** 🚂
