import os
import subprocess
import shutil
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# ===== CONFIGURATION =====
TOKEN = "7789837723:AAGA3RlTDbOQqRdqk8Lgh-EZNSUusxV35q8"  # BotFather से मिला token
FFMPEG_PATH = "ffmpeg"  # Render Linux path
DOWNLOAD_DIR = "/tmp"
VIDEO_PATH = os.path.join(DOWNLOAD_DIR, "video.mp4")
MAX_TELEGRAM_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB
# =========================

# ---------- Ping Command ----------
async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive and running!")
# -----------------------------------

# ---------- Main Lecture Downloader ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if url.startswith("http") and ".m3u8" in url:
        if not shutil.which(FFMPEG_PATH):
            await update.message.reply_text("⚠️ FFmpeg नहीं मिला! Render install script चेक करो।")
            return

        await update.message.reply_text("⏳ Download शुरू हो रहा है...")

        command = [
            FFMPEG_PATH,
            "-headers", "User-Agent: Mozilla/5.0\r\n",
            "-headers", "Referer: https://stream.pwjarvis.app/\r\n",
            "-i", url,
            "-c", "copy",
            "-bsf:a", "aac_adtstoasc",
            VIDEO_PATH,
            "-y"
        ]

        process = subprocess.Popen(command, stderr=subprocess.PIPE, universal_newlines=True)

        total_duration = 0
        last_progress = -1

        while True:
            line = process.stderr.readline()
            if not line:
                break
            if "Duration" in line:
                try:
                    parts = line.strip().split("Duration: ")[1].split(",")[0].split(":")
                    total_duration = int(float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2]))
                except:
                    pass
            if "time=" in line:
                try:
                    time_str = line.split("time=")[1].split(" ")[0]
                    t = time_str.split(":")
                    current_time = int(float(t[0]) * 3600 + float(t[1]) * 60 + float(t[2]))
                    if total_duration > 0:
                        progress = int((current_time / total_duration) * 100)
                        if progress != last_progress and progress % 10 == 0:
                            last_progress = progress
                            await update.message.reply_text(f"⬇️ Download प्रगति: {progress}%")
                except:
                    pass

        process.wait()

        if process.returncode == 0 and os.path.exists(VIDEO_PATH):
            await update.message.reply_text("✅ Download पूरा हुआ! Local में save कर दिया गया।")

            size = os.path.getsize(VIDEO_PATH)
            if size <= MAX_TELEGRAM_SIZE:
                try:
                    with open(VIDEO_PATH, 'rb') as vid:
                        await update.message.reply_video(video=InputFile(vid, "lecture.mp4"))
                    await update.message.reply_text("📤 Lecture Telegram पर भेज दिया गया।")
                except Exception as e:
                    await update.message.reply_text(f"⚠️ Telegram पर भेजने में समस्या: {e}")
            else:
                await update.message.reply_text("⚠️ फाइल 2GB से बड़ी है, सिर्फ local में save है।")
        else:
            await update.message.reply_text("❌ Download fail हो गया।")
    else:
        await update.message.reply_text("कृपया सही .m3u8 लिंक भेजें।")

# ---------- Bot Runner ----------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # /ping command for UptimeRobot
    app.add_handler(CommandHandler("ping", ping_command))

    # Main message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot चालू हो गया है...")
    app.run_polling()
