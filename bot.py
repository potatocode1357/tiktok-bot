import os
import glob
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# Your Token
BOT_TOKEN = "8678444569:AAF8DMWWxXhQpCnmsc6cxUTTcC6CjO-i9mk"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **Ultimate HQ Downloader Online**\nSend me any TikTok, YouTube, or Instagram link!")

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        return

    msg = await update.message.reply_text("🔎 Processing... (Fetching HQ)")
    output_path = f"video_{update.message.message_id}"

    # THE BULLETPROOF SETTINGS
    # This grabs the best quality available (no matter the format) 
    # and merges it into an mp4.
    ydl_opts = {
        "outtmpl": f"{output_path}.%(ext)s",
        "format": "bestvideo+bestaudio/best", 
        "merge_output_format": "mp4",
        "quiet": True,
        "cookiefile": "cookies.txt",
        "noplaylist": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Threading keeps the bot from timing out on long downloads
            await asyncio.to_thread(ydl.download, [url])

        # Find the final file (it will be .mp4 because of merge_output_format)
        files = glob.glob(f"{output_path}.*")
        if not files:
            await msg.edit_text("❌ Download failed. The link might be protected.")
            return

        video_file = files[0]
        await msg.edit_text("📤 Uploading HQ Video...")
        
        with open(video_file, "rb") as f:
            await update.message.reply_video(video=f, supports_streaming=True)
        await msg.delete()

    except Exception as e:
        # If the video is region-blocked (like the beIN sports one), it will show here
        await msg.edit_text(f"❌ Error: {str(e)}")

    finally:
        # Clean up files so Railway doesn't run out of space
        for f in glob.glob(f"{output_path}.*"):
            if os.path.exists(f):
                os.remove(f)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_download))
    # drop_pending_updates ignores all the failed attempts you sent while fixing this
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()