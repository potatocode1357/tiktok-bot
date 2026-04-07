import os
import glob
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# Using your token directly to ensure it works
BOT_TOKEN = "8678444569:AAF8DMWWxXhQpCnmsc6cxUTTcC6CjO-i9mk"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ **High-Quality Downloader Active**\nSend me a TikTok, Instagram, or YouTube link!")

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    valid_sites = ["tiktok.com", "youtube.com", "youtu.be", "instagram.com", "facebook.com", "fb.watch"]
    
    if not any(site in url for site in valid_sites):
        return

    msg = await update.message.reply_text("📡 Searching for high-quality video...")
    output_path = f"video_{update.message.message_id}"

    ydl_opts = {
        "outtmpl": f"{output_path}.%(ext)s",
        # This tells the bot to get the BEST quality that is still MP4
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get info to check size
            info = ydl.extract_info(url, download=False)
            
            # Fixed the 'NoneType' error here with .get() defaults
            filesize = info.get('filesize') or info.get('filesize_approx') or 0
            
            # If size is known and over 50MB
            if filesize > 50000000:
                await msg.edit_text("⚠️ Video is too large (over 50MB). Try a shorter video!")
                return

            await msg.edit_text("📥 Downloading HQ Video...")
            ydl.download([url])

        # Find the file
        files = glob.glob(f"{output_path}.*")
        if not files:
            await msg.edit_text("❌ Failed to grab video. It might be private.")
            return

        video_file = files[0]
        
        # Double check actual file size on disk before sending
        if os.path.getsize(video_file) > 50000000:
            await msg.edit_text("⚠️ Final file exceeded 50MB. Telegram won't let me send it!")
            os.remove(video_file)
            return

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
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()