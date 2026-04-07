import os
import glob
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

BOT_TOKEN = "8678444569:AAF8DMWWxXhQpCnmsc6cxUTTcC6CjO-i9mk"  # ← paste your BotFather token here

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me a TikTok link and I'll download it without the watermark!"
    )

async def download_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    # Basic TikTok URL check
    if "tiktok.com" not in url:
        await update.message.reply_text("❌ Please send a valid TikTok link.")
        return

    msg = await update.message.reply_text("⏳ Downloading...")

    output_path = f"video_{update.message.message_id}"

    ydl_opts = {
        "outtmpl": f"{output_path}.%(ext)s",
        "format": "best",
        "quiet": True,
        # This removes the watermark on most TikTok videos
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the downloaded file
        files = glob.glob(f"{output_path}.*")
        if not files:
            await msg.edit_text("❌ Download failed. Try another link.")
            return

        video_file = files[0]

        await msg.edit_text("📤 Sending video...")
        with open(video_file, "rb") as f:
            await update.message.reply_video(video=f, supports_streaming=True)

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)}")

    finally:
        # Clean up file
        for f in glob.glob(f"{output_path}.*"):
            os.remove(f)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_tiktok))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()