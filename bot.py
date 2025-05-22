import logging
import openai
import base64
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# === CONFIG ===
TELEGRAM_BOT_TOKEN = "7972031642:AAHH7xxNlCyNIG3j-r8osQx3O4H2wqW8Qqg"
TELEGRAM_CHANNEL_ID = -1002690403598
OPENAI_API_KEY = "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"
WEBHOOK_URL = "https://tradebot-1-dkz2.onrender.com/webhook"  # ← webhook direct

openai.api_key = OPENAI_API_KEY

# === GPT VISION ===
async def analyze_image_with_gpt(image_bytes):
    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "Tu es un assistant qui analyse des captures d'écran de trades TradingView. Les couleurs signifient : VERT = TP, NOIR = Prix d'entrée, ROUGE = SL, JAUNE = prix actuel (à ignorer). Repère l'actif (ex : XAUUSD, BTCUSDT, EURUSD...) écrit en haut de l’image. (...) déduire s’il s’agit d’un BUY (si TP > PE) ou SELL (si TP < PE) et Réponds strictement dans ce format sans ajouter d’explication :\\n\\nACTIF – BUY\\nPE : ...\\nTP : ...\\nSL : ..."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=200
    )
    return response["choices"][0]["message"]["content"]

# === STYLING DU SIGNAL
def stylise_result(raw_text):
    lines = raw_text.strip().splitlines()
    if len(lines) < 4:
        return raw_text
    actif, trade_type = lines[0].split("–")
    pe = lines[1].split(":")[1].strip()
    tp = lines[2].split(":")[1].strip()
    sl = lines[3].split(":")[1].strip()

    return f"""🔥 <b>SIGNAL VIP – {actif.strip()}</b> 🔥

📈 <b>Type : {trade_type.strip()}</b>
🎯 <b>Entrée</b> : {pe}
✅ <b>TP</b>      : {tp}
🛑 <b>SL</b>      : {sl}

📤 Copie et exécute ! <b>BE automatique à +20PIPS</b> !
"""

# === TRAITEMENT DE L'IMAGE
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.photo:
        print("✅ Image reçue")  # log debug
        file = await update.message.photo[-1].get_file()
        image_bytes = await file.download_as_bytearray()
        result = await analyze_image_with_gpt(image_bytes)
        styled = stylise_result(result)
        await context.bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=styled, parse_mode="HTML")
        await update.message.reply_text("✅ Signal envoyé dans le canal.")

# === LANCEMENT EN MODE WEBHOOK
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    print("🤖 Bot prêt avec webhook !")
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL
    )
