import os
import glob
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# It's better to get the token from Railway's settings (Variables)
# If you didn't set the variable in Railway yet, it will use the one below.
BOT_TOKEN = os.getenv("BOT_TOKEN", "8678444569:AAF8DMWWxXhQpCnmsc6cxUTTcC6CjO-i9mk")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **Universal Downloader Bot**\n\n"
        "Send me a link from:\n"
        "✅ TikTok\n"
        "✅ YouTube & Shorts\n"
        "✅ Instagram\n"
        "✅ Facebook\n\n"
        "I'll handle the rest!"
    )

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    # Check for valid links
    valid_sites = ["tiktok.com", "youtube.com", "youtu.be", "instagram.com", "facebook.com", "fb.watch"]
    if not any(site in url for site in valid_sites):
        return # Ignore messages that aren't links

    msg = await update.message.reply_text("⏳ Processing link...")

    output_path = f"video_{update.message.message_id}"

    ydl_opts = {
        "outtmpl": f"{output_path}.%(ext)s",
        "format": "best[ext=mp4]/best", # Prefers MP4 for Telegram compatibility
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. Get video info first to check size
            info = ydl.extract_info(url, download=False)
            filesize = info.get('filesize', 0) or info.get('filesize_approx', 0)
            
            # 2. Check 50MB Telegram Limit (50,000,000 bytes)
            if filesize > 50000000:
                await msg.edit_text("❌ File is too large! Telegram bots can only send videos under 50MB.")
                return

            # 3. Download if size is okay
            await msg.edit_text("📥 Downloading...")
            ydl.download([url])

        # Find the downloaded file
        files = glob.glob(f"{output_path}.*")
        if not files:
            await msg.edit_text("❌ Download failed. The video might be private or deleted.")
            return

        video_file = files[0]

        await msg.edit_text("📤 Sending to Telegram...")
        with open(video_file, "rb") as f:
            await update.message.reply_video(video=f, supports_streaming=True)

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")

    finally:
        # Clean up files from the server
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