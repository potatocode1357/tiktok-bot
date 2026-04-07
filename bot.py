import os
import glob
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

BOT_TOKEN = "8678444569:AAF8DMWWxXhQpCnmsc6cxUTTcC6CjO-i9mk"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **HQ Downloader Online**\nSend me any link!")

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        return

    msg = await update.message.reply_text("🔎 Processing...")
    output_path = f"video_{update.message.message_id}"

    # Simplified options to avoid the "format not available" error
    ydl_opts = {
        "outtmpl": f"{output_path}.%(ext)s",
        "format": "best",  # Just get the best single file available
        "merge_output_format": "mp4",
        "quiet": True,
        "cookiefile": "cookies.txt",
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [url])

        files = glob.glob(f"{output_path}.*")
        if not files:
            await msg.edit_text("❌ Failed to download.")
            return

        video_file = files[0]
        await msg.edit_text("📤 Uploading...")
        with open(video_file, "rb") as f:
            await update.message.reply_video(video=f, supports_streaming=True)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")

    finally:
        for f in glob.glob(f"{output_path}.*"):
            if os.path.exists(f):
                os.remove(f)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_download))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()