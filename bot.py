import os
import glob
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# Your Token
BOT_TOKEN = "8678444569:AAF8DMWWxXhQpCnmsc6cxUTTcC6CjO-i9mk"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **Ultimate HQ Downloader**\nSend me a TikTok, YouTube, or Instagram link!")

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    valid_sites = ["tiktok.com", "youtube.com", "youtu.be", "instagram.com", "facebook.com", "fb.watch"]
    
    if not any(site in url for site in valid_sites):
        return

    msg = await update.message.reply_text("🔎 Fetching best quality...")
    output_path = f"video_{update.message.message_id}"

    # FLEXIBLE SETTINGS: Merges best audio/video if possible, else grabs the best single file.
    ydl_opts = {
        "outtmpl": f"{output_path}.%(ext)s",
        "format": "bestvideo+bestaudio/best", 
        "merge_output_format": "mp4",
        "quiet": True,
        "cookiefile": "cookies.txt",
        "extractor_args": {"instagram": {"check_egotism": [True]}},
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Threading prevents the bot from freezing
            info = await asyncio.to_thread(ydl.extract_info, url, download=False)
            filesize = info.get('filesize') or info.get('filesize_approx') or 0
            
            if filesize > 50000000: # 50MB limit
                await msg.edit_text("⚠️ Video too big (50MB+). Try a shorter one!")
                return

            await msg.edit_text("📥 Downloading & Merging...")
            await asyncio.to_thread(ydl.download, [url])

        files = glob.glob(f"{output_path}.*")
        if not files:
            await msg.edit_text("❌ Failed. The site might be blocking the bot.")
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
    # drop_pending_updates=True makes the bot ignore messages sent while it was offline
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()