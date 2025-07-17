"""
🤖 Daily Task Tracker Bot - Railway Cloud Version
Automatically updates Google Sheets with your daily tasks
"""

import os
import json
import logging
import re
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from fastapi import FastAPI, Request
import gspread
from google.oauth2.service_account import Credentials
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
GOOGLE_SHEETS_CREDENTIALS = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
PORT = int(os.getenv('PORT', 8000))

# Initialize FastAPI for webhook
app = FastAPI()

# Global bot application
bot_app = None

class GoogleSheetsManager:
    def __init__(self):
        self.sheet = None
        self.setup_sheet()
    
    def setup_sheet(self):
        """Initialize Google Sheets connection"""
        try:
            # Parse credentials from environment variable
            creds_dict = json.loads(GOOGLE_SHEETS_CREDENTIALS)
            
            # Set up credentials
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            
            # Connect to Google Sheets
            gc = gspread.authorize(credentials)
            self.sheet = gc.open_by_key(GOOGLE_SHEETS_ID).sheet1
            
            # Set up headers if needed
            self.setup_headers()
            logger.info("✅ Google Sheets connected successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Google Sheets: {e}")
            self.sheet = None
    
    def setup_headers(self):
        """Set up sheet headers if they don't exist"""
        try:
            # Check if headers exist
            headers = self.sheet.row_values(1)
            if not headers or len(headers) < 4:
                # Set headers
                self.sheet.update('A1:E1', [['Date', 'Time', 'Task', 'Status', 'Notes']])
                logger.info("📝 Headers set up in Google Sheet")
        except Exception as e:
            logger.error(f"❌ Error setting up headers: {e}")
    
    def add_task(self, task_text, status="Done"):
        """Add a task to the Google Sheet"""
        try:
            if not self.sheet:
                return False
                
            # Get current date and time
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M")
            
            # Find next empty row
            next_row = len(self.sheet.get_all_values()) + 1
            
            # Add the task
            self.sheet.update(f'A{next_row}:E{next_row}', 
                            [[date_str, time_str, task_text, status, ""]])
            
            logger.info(f"✅ Task added to Google Sheet: {task_text}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding task to Google Sheet: {e}")
            return False

class TaskParser:
    @staticmethod
    def parse_message(text):
        """Parse message to extract task and status"""
        text = text.strip()
        
        # Status patterns
        done_patterns = [
            r'\b(completed?|finished?|done)\b',
            r'\b(✅|✓|☑️)\b',
            r'\bcompleted?\s+(.+)',
            r'\bfinished?\s+(.+)',
            r'\bdone\s+(.+)'
        ]
        
        progress_patterns = [
            r'\b(working on|started|begun|in progress)\b',
            r'\b(🔄|⏳)\b',
            r'\bworking on\s+(.+)',
            r'\bstarted\s+(.+)'
        ]
        
        # Check for done status
        for pattern in done_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Extract task from the message
                task = re.sub(r'\b(completed?|finished?|done|✅|✓|☑️)\s*', '', text, flags=re.IGNORECASE).strip()
                return task, "Done"
        
        # Check for in progress status
        for pattern in progress_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                task = re.sub(r'\b(working on|started|begun|in progress|🔄|⏳)\s*', '', text, flags=re.IGNORECASE).strip()
                return task, "In Progress"
        
        # Default to Done status
        return text, "Done"

# Initialize Google Sheets manager
sheets_manager = GoogleSheetsManager()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    welcome_message = """
🤖 **Daily Task Tracker Bot**

Hi! I'll help you track your daily tasks automatically.

**How to use:**
• Just send me your task updates
• I'll automatically detect the status and save to Google Sheets

**Examples:**
• "Completed the sales report"
• "Working on project planning"
• "Finished client meeting"
• "Started code review"

**Commands:**
• /start - Show this help
• /status - Check bot status

Ready to track your productivity! 📈
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check bot status"""
    sheets_status = "✅ Connected" if sheets_manager.sheet else "❌ Disconnected"
    
    status_message = f"""
🤖 **Bot Status**

📊 Google Sheets: {sheets_status}
🔗 Sheet ID: {GOOGLE_SHEETS_ID[:20]}...
⏰ Last check: {datetime.now().strftime("%H:%M:%S")}

Bot is running and ready! 🚀
    """
    await update.message.reply_text(status_message, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and extract tasks"""
    try:
        message_text = update.message.text
        user_name = update.effective_user.first_name or "User"
        
        # Parse the message
        task, status = TaskParser.parse_message(message_text)
        
        if len(task.strip()) < 3:
            await update.message.reply_text(
                "🤔 Could you provide more details about your task?"
            )
            return
        
        # Add to Google Sheets
        success = sheets_manager.add_task(task, status)
        
        if success:
            # Send confirmation
            status_emoji = "✅" if status == "Done" else "🔄"
            response = f"{status_emoji} **Task Recorded!**\n\n📝 **Task:** {task}\n📊 **Status:** {status}\n💾 **Saved to Google Sheets**"
            await update.message.reply_text(response, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                "❌ Sorry, there was an issue saving your task. Please try again."
            )
            
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text(
            "🤖 Something went wrong. Please try again!"
        )

def create_bot_application():
    """Create and configure the bot application"""
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return application

# FastAPI webhook endpoint
@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming webhook requests from Telegram"""
    try:
        json_data = await request.json()
        update = Update.de_json(json_data, bot_app.bot)
        await bot_app.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "bot": "Daily Task Tracker",
        "time": datetime.now().isoformat()
    }

async def setup_webhook():
    """Set up webhook for the bot"""
    try:
        # Get the Railway app URL (automatically provided by Railway)
        webhook_url = f"https://{os.getenv('RAILWAY_PUBLIC_DOMAIN', 'localhost')}/webhook"
        
        # Set webhook
        await bot_app.bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook set to: {webhook_url}")
        
    except Exception as e:
        logger.error(f"❌ Failed to set webhook: {e}")

def main():
    """Main function to run the bot"""
    global bot_app
    
    try:
        # Create bot application
        bot_app = create_bot_application()
        logger.info("✅ Bot application created")
        
        # Start FastAPI server
        logger.info(f"🚀 Starting server on port {PORT}")
        uvicorn.run(app, host="0.0.0.0", port=PORT)
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        raise

if __name__ == "__main__":
    main()
