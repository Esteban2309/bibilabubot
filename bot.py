import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import yt_dlp

# Configurar logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('¡Hola! Envía /download <enlace> para procesar tu video 🚀')

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Por favor, envía un enlace. Ejemplo: /download https://youtube.com/watch?v=...")
        return

    url = context.args[0]
    status_msg = await update.message.reply_text("⏳ Procesando video en la nube...")

    # Opciones de yt-dlp optimizadas para servidores y evitar bloqueos
    ydl_opts = {
        'format': 'best[height<=720]',  # 720p para equilibrar calidad y peso
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'socket_timeout': 60,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    filename = None
    try:
        os.makedirs('downloads', exist_ok=True)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
        
        # Validación estricta del límite de la API de Telegram (50MB)
        if file_size_mb > 50:
            await status_msg.edit_text(f"❌ El video pesa {file_size_mb:.1f}MB. Supera el límite de 50MB que permite la API de Telegram para bots.")
            if os.path.exists(filename):
                os.remove(filename)
            return

        await status_msg.edit_text("📤 Subiendo video al chat...")

        with open(filename, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=f"🎥 {info.get('title', 'Video')}"
            )

        if os.path.exists(filename):
            os.remove(filename)

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ Ocurrió un error: {str(e)}")
        if filename and os.path.exists(filename):
            os.remove(filename)

if __name__ == '__main__':
    TOKEN = os.getenv("TOKEN", "8723783721:AAFIicHnrSrEB5YVurEasSxIN3R_OdrRaLU")
    
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("download", download_video))
    
    print("Bot en ejecución...")
    app.run_polling()