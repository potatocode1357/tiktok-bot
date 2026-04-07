import os
import glob
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# Use your token here
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

    # THE ULTIMATE SETTINGS (Requires FFmpeg)
    ydl_opts = {
        "outtmpl": f"{output_path}.%(ext)s",
        # This downloads the best video and best audio separately and MERGES them
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "extractor_args": {"instagram": {"check_egotism": [True]}},
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            filesize = info.get('filesize') or info.get('filesize_approx') or 0
            
            if filesize > 50000000:
                await msg.edit_text("⚠️ Video too big (50MB+). Try a shorter one!")
                return

            await msg.edit_text("📥 Downloading & Merging HQ Tracks...")
            ydl.download([url])

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
    app.run_polling()

if __name__ == "__main__":
    main()