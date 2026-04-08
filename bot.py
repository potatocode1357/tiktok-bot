import os
import glob
import asyncio
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TOKEN_HERE")

QUALITIES = [
    ("4K 🌟", "2160"),
    ("1440p ✨", "1440"),
    ("1080p 🔥", "1080"),
    ("720p 💎", "720"),
    ("480p 📱", "480"),
    ("360p 📉", "360"),
    ("144p 🐢", "144"),
    ("🎬 Best Available", "best"),
]

def is_instagram(url): return "instagram.com" in url
def is_tiktok(url): return "tiktok.com" in url

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
            "noplaylist": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        }
        cookies_path = "cookies.txt"
        if os.path.exists(cookies_path):
            ydl_opts_info["cookiefile"] = cookies_path

        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, False)

        if "entries" in info:
            info = info["entries"][0]

        title = info.get("title", "Video")[:50]
        duration = info.get("duration", 0) or 0
        mins = duration // 60
        secs = duration % 60

        available_heights = set()
        for f in info.get("formats", []):
            h = f.get("height")
            if h:
                available_heights.add(h)
        context.user_data['available_heights'] = available_heights
        context.user_data['is_instagram'] = is_instagram(url)
        context.user_data['is_tiktok'] = is_tiktok(url)

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
        warning = "⚠️ Long video — try lower quality to stay under 50MB\n" if duration > 600 else ""

        await msg.edit_text(
            f"✅ *{title}*\n{duration_text}{warning}\nPick a quality:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    except Exception:
        context.user_data['available_heights'] = set()
        context.user_data['is_instagram'] = is_instagram(url)
        context.user_data['is_tiktok'] = is_tiktok(url)

        keyboard = []
        row = []
        for label, q in QUALITIES:
            row.append(InlineKeyboardButton(label, callback_data=q))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        await msg.edit_text(
            "✅ Video found! Pick a quality:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

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
    available = context.user_data.get('available_heights', set())
    insta = context.user_data.get('is_instagram', False)
    tiktok = context.user_data.get('is_tiktok', False)

    # Instagram and TikTok — never try to merge, just grab best single file
    if insta or tiktok:
        if quality == 'best':
            f_choice = "best"
        else:
            q = int(quality)
            f_choice = f"best[height<={q}]/best"
    elif quality == 'best':
        f_choice = "bestvideo+bestaudio/best"
    else:
        q = int(quality)

        if available:
            below = [h for h in available if h <= q]
            use_height = max(below) if below else min(available)
            if use_height != q:
                await msg.edit_text(f"📥 {q}p not available, downloading {use_height}p instead...")
        else:
            use_height = q

        if use_height <= 360:
            f_choice = f"best[height<={use_height}]/best"
        else:
            f_choice = (
                f"bestvideo[height<={use_height}][ext=mp4]+bestaudio[ext=m4a]"
                f"/bestvideo[height<={use_height}]+bestaudio"
                f"/bestvideo[height<={use_height}]"
                f"/best[height<={use_height}]"
                f"/best"
            )

    cookies_path = "cookies.txt"
    ydl_opts = {
        "outtmpl": f"{output_path}.%(ext)s",
        "format": f_choice,
        "quiet": True,
        "noplaylist": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
    }

    # Only add merge and ffmpeg options for YouTube
    if not insta and not tiktok:
        ydl_opts["merge_output_format"] = "mp4"

    if os.path.exists(cookies_path):
        ydl_opts["cookiefile"] = cookies_path

    try:
        actual_quality = None

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, True)
            if info:
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
                f"❌ File is {file_size:.1f}MB — Telegram limit is 50MB.\nTry a lower quality."
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
        await msg.edit_text(f"❌ Error: {str(e)}")

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