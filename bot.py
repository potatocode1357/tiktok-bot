import os
import glob
import asyncio
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = "8678444569:AAF8DMWWxXhQpCnmsc6cxUTTcC6CjO-i9mk"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **Pro Downloader Ready**\nSend me a link to get started!")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"): return

    msg = await update.message.reply_text("🔎 Analyzing video quality...")
    
    # Store the URL for later
    context.user_data['current_url'] = url

    keyboard = [
        [InlineKeyboardButton("🔥 1080p (FHD)", callback_data='1080'),
         InlineKeyboardButton("💎 720p (HD)", callback_data='720')],
        [InlineKeyboardButton("📱 480p (SD)", callback_data='480'),
         InlineKeyboardButton("🎬 Best Available", callback_data='best')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await msg.edit_text("✅ Video found! Choose your quality:", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    quality = query.data
    url = context.user_data.get('current_url')
    if not url:
        await query.edit_message_text("❌ Session expired. Please send the link again.")
        return

    await query.edit_message_text(f"📥 Downloading in {quality}p... Please wait.")
    
    output_path = f"video_{query.message.message_id}"
    
    # Format logic: Tries to find the chosen height, otherwise falls back to best
    if quality == 'best':
        f_choice = "bestvideo+bestaudio/best"
    else:
        f_choice = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"

    ydl_opts = {
        "outtmpl": f"{output_path}.%(ext)s",
        "format": f_choice,
        "merge_output_format": "mp4",
        "quiet": True,
        "cookiefile": "cookies.txt",
        "http_headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [url])

        files = glob.glob(f"{output_path}.*")
        if not files:
            await query.edit_message_text("❌ Failed to process. Try 'Best Available'.")
            return

        video_file = files[0]
        await query.edit_message_text("📤 Uploading to Telegram...")
        with open(video_file, "rb") as f:
            await context.bot.send_video(chat_id=query.message.chat_id, video=f, supports_streaming=True)
        await query.message.delete()

    except Exception as e:
        await query.edit_message_text(f"❌ Error: {str(e)}")

    finally:
        for f in glob.glob(f"{output_path}.*"):
            if os.path.exists(f): os.remove(f)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()