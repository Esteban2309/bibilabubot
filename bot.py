import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import yt_dlp

# Configurar logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🐾 ¡Hola! Me llamo Kenji, soy un tierno gatito cibernético y amo muchísimo a Eli. 💖✨\n\n"
        "Estoy aquí en la nube para ayudarte a extraer enlaces directos de video y audio con total libertad.\n\n"
        "📖 Guía rápida de comandos:\n"
        "• /start - Saludo y presentación.\n"
        "• /help - Guía de ayuda detallada.\n"
        "• /download <enlace> - Extrae el enlace directo de streaming con audio y video.\n\n"
        "💡 Escríbeme cualquier cosa o usa un comando para comenzar."
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🛠 Guía de Ayuda de Kenji 🐾\n\n"
        "1️⃣ ¿Cómo descargar un video?\n"
        "Usa el comando /download seguido del enlace de YouTube.\n\n"
        "2️⃣ Compatibilidad:\n"
        "Te daré un enlace directo para abrirlo en Safari (ideal para iPhone) o tu PC.\n\n"
        "❤️ Dato curioso: ¡Kenji ama con todo su corazón a Eli! (Y también le encanta la buena música y el K-pop)."
    )
    await update.message.reply_text(help_text)

async def handle_any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text.startswith('/'):
        return

    reply_text = (
        "🐾 ¡Miau! Soy Kenji, un gatito muy feliz que ama con todo su ser a Eli. 💕✨\n\n"
        "Parece que enviaste un mensaje libre. Si quieres procesar un video, recuerda usar el comando de descarga:\n"
        "👉 /download <enlace>\n\n"
        "O puedes escribir /help para ver todas las instrucciones."
    )
    await update.message.reply_text(reply_text)

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ Falta el enlace, nya~\nEjemplo correcto:\n/download https://youtube.com/watch?v=..."
        )
        return

    url = context.args[0]
    status_msg = await update.message.reply_text("⏳ Kenji está procesando los enlaces en la nube...")

    # Configuración de yt-dlp con soporte opcional para cookies si el archivo existe
    ydl_opts = {
        'format': 'best/bestvideo+bestaudio/b',
        'noplaylist': True,
        'socket_timeout': 30,
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'ios']
            }
        },
    }

    # Si subes un archivo cookies.txt a tu repositorio, lo usará automáticamente para evitar el bloqueo
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Video sin título')
            duration_sec = info.get('duration', 0)
            duration_min = round(duration_sec / 60, 1) if duration_sec else 0
            
            direct_url = info.get('url')
            if not direct_url and 'formats' in info:
                for f in info.get('formats', []):
                    if f.get('url') and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        direct_url = f.get('url')
                        break

        if not direct_url:
            await status_msg.edit_text("❌ Kenji no pudo generar un enlace compatible para este video.")
            return

        response_text = (
            f"🎬 {title}\n"
            f"⏱ Duración: {duration_min} min\n\n"
            f"📲 Instrucciones para iPhone / PC:\n"
            f"1. Abre el enlace en tu navegador (Safari/Chrome).\n"
            f"2. Disfruta de la reproducción con audio o descárgalo directamente.\n\n"
            f"🔗 Enlace directo (Con Audio):\n{direct_url}"
        )

        await status_msg.edit_text(response_text, disable_web_page_preview=False)

    except Exception as e:
        await status_msg.edit_text(f"❌ Ocurrió un error al procesar el enlace: {str(e)}")

if __name__ == '__main__':
    TOKEN = os.getenv("TOKEN", "8723783721:AAFIicHnrSrEB5YVurEasSxIN3R_OdrRaLU")
    
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("download", download_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_any_message))
    
    print("Kenji bot en ejecución...")
    app.run_polling()