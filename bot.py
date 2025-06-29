import asyncio
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from mistralai.client import MistralClient

# Load configuration
with open('/home/ubuntu/creditbot_data/config.json') as config_file:
    config = json.load(config_file)
    TOKEN = config['telegram_token']
    MISTRAL_API_KEY = config['mistral_api_key']

# Load credit repair data
with open('/home/ubuntu/creditbot_data/refined_balanced_training_data.json') as data_file:
    credit_repair_data = json.load(data_file)

# Load master prompt
with open('/home/ubuntu/creditbot_data/master_prompt.txt') as prompt_file:
    MASTER_PROMPT = prompt_file.read().strip()

# Initialize Mistral AI client
mistral_client = MistralClient(api_key=MISTRAL_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to @LimitBreaker, your credit repair coach! 🚀 Use /help for commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Commands:\\n/start - Start the bot\\n/help - Show this message\\n/info <topic> - Get credit repair info"
    )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args:
        await update.message.reply_text("Please provide a topic, e.g., /info credit_score")
        return
    topic = " ".join(args).lower()
    # Search JSON data for matching prompt
    response = None
    for item in credit_repair_data:
        if topic in item.get('prompt', '').lower():
            response = item.get('response')
            break
    if not response:
        # Fallback to Mistral AI with master prompt
        try:
            prompt = f"{MASTER_PROMPT}\\n\\nUser query: {topic}"
            chat_response = mistral_client.chat(
                messages=[{"role": "user", "content": prompt}],
                model="mistral-small"
            )
            response = chat_response.choices[0].message.content
        except Exception as e:
            response = f"Sorry, I couldn't fetch info from Mistral AI: {str(e)}"
    await update.message.reply_text(response)

def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info_command))
    print("LimitBreaker is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
