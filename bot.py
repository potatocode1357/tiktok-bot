import os
import glob
import asyncio
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TOKEN_HERE")

QUALITIES = [
    ("4K 🌟", "2160"),
    ("1080p 🔥", "1080"),
    ("720p 💎", "720"),
    ("480p 📱", "480"),
    ("360p 📉", "360"),
    ("144p 🐢", "144"),
    ("🎬 Best Available", "best"),
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 *Pro Downloader Online*\n\nSend me a YouTube, TikTok, or Instagram link!",
        parse_mode="Markdown"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        return

    context.user_data['current_url'] = url
    msg = await update.message.reply_text("🔎 Fetching video info...")

    try:
        ydl_opts_info = {
            "quiet": True,
            "skip_download": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            },
        }
        cookies_path = "cookies.txt"
        if os.path.exists(cookies_path):
            ydl_opts_info["cookiefile"] = cookies_path

        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, False)

        title = info.get("title", "Video")[:50]
        duration = info.get("duration", 0) or 0
        mins = duration // 60
        secs = duration % 60

        # Build quality keyboard
        keyboard = []
        row = []
        for label, q in QUALITIES:
            row.append(InlineKeyboardButton(label, callback_data=q))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        duration_text = f"⏱ {mins}m {secs}s\n" if duration else ""
        await msg.edit_text(
            f"✅ *{title}*\n{duration_text}\nPick a quality:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    except Exception as e:
        await msg.edit_text(f"❌ Could not fetch video info: {str(e)}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    quality = query.data
    url = context.user_data.get('current_url')
    if not url:
        await query.edit_message_text("❌ Session timed out. Send the link again.")
        return

    label = "Best Available" if quality == 'best' else f"{quality}p"
    await query.edit_message_text(f"📥 Downloading at {label}...")
    await download_and_send(url, quality, query.message, query.message.chat_id, context)

async def download_and_send(url, quality, msg, chat_id, context):
    output_path = f"video_{msg.message_id}"

    if quality == 'best':
        f_choice = "bestvideo+bestaudio/best"
    else:
        f_choice = (
            f"bestvideo[height<={quality}]+bestaudio"
            f"/bestvideo[height<={quality}]/best"
        )

    cookies_path = "cookies.txt"
    ydl_opts = {
        "outtmpl": f"{output_path}.%(ext)s",
        "format": f_choice,
        "merge_output_format": "mp4",
        "quiet": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        },
    }
    if os.path.exists(cookies_path):
        ydl_opts["cookiefile"] = cookies_path

    try:
        actual_quality = None

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, True)
            if info:
                # For playlists or single videos
                if "entries" in info:
                    info = info["entries"][0]
                actual_quality = info.get("height")

        files = glob.glob(f"{output_path}.*")
        if not files:
            await msg.edit_text("❌ Could not generate video file. Try Best Available.")
            return

        video_file = files[0]
        file_size = os.path.getsize(video_file) / (1024 * 1024)

        if file_size > 50:
            await msg.edit_text(
                f"❌ File is {file_size:.1f}MB — Telegram's limit is 50MB.\nTry a lower quality."
            )
            return

        quality_text = f"{actual_quality}p" if actual_quality else "Best Available"
        await msg.edit_text(f"📤 Uploading in {quality_text}...")

        with open(video_file, "rb") as f:
            await context.bot.send_video(
                chat_id=chat_id,
                video=f,
                supports_streaming=True,
                caption=f"✅ Downloaded in *{quality_text}*",
                parse_mode="Markdown"
            )

        await msg.delete()

    except Exception as e:
        error_msg = str(e)
        if "format" in error_msg.lower() or "not available" in error_msg.lower():
            await msg.edit_text("❌ That quality isn't available. Try a lower one or Best Available.")
        elif "private" in error_msg.lower():
            await msg.edit_text("❌ This video is private and can't be downloaded.")
        elif "copyright" in error_msg.lower():
            await msg.edit_text("❌ This video is blocked due to copyright.")
        else:
            await msg.edit_text(f"❌ Error: {error_msg}")

    finally:
        for f in glob.glob(f"{output_path}.*"):
            if os.path.exists(f):
                os.remove(f)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()