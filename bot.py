import os
import glob
import asyncio
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = "8678444569:AAF8DMWWxXhQpCnmsc6cxUTTcC6CjO-i9mk"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **Pro Downloader Online**\nSend me a link and I'll handle the rest!")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"): return

    msg = await update.message.reply_text("🔎 Analyzing video...")
    context.user_data['current_url'] = url

    keyboard = [
        [InlineKeyboardButton("🔥 1080p", callback_data='1080'),
         InlineKeyboardButton("💎 720p", callback_data='720')],
        [InlineKeyboardButton("🎬 Best Available", callback_data='best')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await msg.edit_text("✅ Video found! Pick a quality:", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    quality = query.data
    url = context.user_data.get('current_url')
    if not url:
        await query.edit_message_text("❌ Session timed out. Send the link again.")
        return

    await query.edit_message_text(f"📥 Downloading... (Target: {quality if quality != 'best' else 'Max Quality'})")
    output_path = f"video_{query.message.message_id}"
    
    # THE "NEVER-FAIL" FORMAT LOGIC
    if quality == 'best':
        f_choice = "bestvideo+bestaudio/best"
    else:
        # Tries to get the requested height, but falls back to 'best' if it doesn't exist
        f_choice = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best"

    ydl_opts = {
        "outtmpl": f"{output_path}.%(ext)s",
        "format": f_choice,
        "merge_output_format": "mp4", # Forces the final file to be MP4
        "quiet": True,
        "cookiefile": "cookies.txt",
        "http_headers": {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [url])

        # Look for any file starting with our output_path
        files = glob.glob(f"{output_path}.*")
        if not files:
            await query.edit_message_text("❌ Could not generate video file. Try 'Best Available'.")
            return

        video_file = files[0]
        await query.edit_message_text("📤 Uploading...")
        
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