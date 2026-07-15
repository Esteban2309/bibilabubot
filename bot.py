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
    welcome_text = (
        "🤖 ¡Bienvenido a tu Bot de Descargas en la Nube! 🚀\n\n"
        "Estoy listo para ayudarte a extraer enlaces directos con audio y video integrados, compatibles con iPhone y PC, sin límites de peso por tamaño de archivo.\n\n"
        "📖 Guía de Comandos Disponibles:\n"
        "• /start - Muestra este mensaje de bienvenida.\n"
        "• /help - Muestra la guía de ayuda y los ejemplos de uso.\n"
        "• /download <enlace> - Extrae el enlace directo de streaming y descarga.\n\n"
        "💡 Ejemplo de uso: /download https://youtube.com/watch?v=tu_video"
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🛠 Guía de Ayuda y Uso del Bot\n\n"
        "1️⃣ ¿Cómo descargar un video?\n"
        "Escribe el comando /download seguido del enlace de YouTube que quieres procesar.\n\n"
        "2️⃣ Compatibilidad con iPhone:\n"
        "El bot te generará un enlace directo optimizado. Solo ábrelo en Safari para reproducirlo con sonido o guardarlo directamente en tu dispositivo.\n\n"
        "3️⃣ Videos Largos:\n"
        "Al no descargar el archivo en el servidor, puedes procesar contenidos de 1 o 2 horas sin que la nube colapse.\n\n"
        "⚠️ Si el enlace llega a fallar, asegúrate de que el video sea público y accesible."
    )
    await update.message.reply_text(help_text)

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ Falta el enlace.\nEjemplo correcto:\n/download https://youtube.com/watch?v=..."
        )
        return

    url = context.args[0]
    status_msg = await update.message.reply_text("⏳ Procesando enlaces de audio y video en la nube...")

    # Configuración base segura contra bloqueos modernos
    ydl_opts = {
        'format': 'best',
        'socket_timeout': 60,
        'extractor_args': {'youtube': {'player_client': ['web', 'mweb']}},
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    }

    # Si hay cookies, las probamos, pero si fallan el script no se romperá
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Video sin título')
            duration_sec = info.get('duration', 0)
            duration_min = round(duration_sec / 60, 1)
            
            direct_url = info.get('url')
            if not direct_url and 'formats' in info:
                for f in info.get('formats', []):
                    if f.get('url') and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        direct_url = f.get('url')
                        break

        if not direct_url:
            await status_msg.edit_text("❌ No se pudo generar un enlace compatible para este video.")
            return

        # Texto plano sin parse_mode Markdown para evitar errores con caracteres especiales
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
        error_msg = str(e)
        if "cookies" in error_msg.lower():
            # Intento de emergencia sin cookies si el archivo expiró
            try:
                if 'cookiefile' in ydl_opts:
                    del ydl_opts['cookiefile']
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'Video sin título')
                    duration_sec = info.get('duration', 0)
                    duration_min = round(duration_sec / 60, 1)
                    direct_url = info.get('url')
                    
                    response_text = (
                        f"🎬 {title}\n"
                        f"⏱ Duración: {duration_min} min\n\n"
                        f"📲 Instrucciones para iPhone / PC:\n"
                        f"1. Abre el enlace en tu navegador (Safari/Chrome).\n"
                        f"2. Disfruta de la reproducción con audio o descárgalo directamente.\n\n"
                        f"🔗 Enlace directo (Con Audio):\n{direct_url}"
                    )
                    await status_msg.edit_text(response_text, disable_web_page_preview=False)
                    return
            except Exception as inner_e:
                await status_msg.edit_text(f"❌ Error al procesar sin cookies: {str(inner_e)}")
                return

        await status_msg.edit_text(f"❌ Ocurrió un error al procesar el enlace: {error_msg}")

if __name__ == '__main__':
    TOKEN = os.getenv("TOKEN", "8723783721:AAFIicHnrSrEB5YVurEasSxIN3R_OdrRaLU")
    
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("download", download_video))
    
    print("Bot en ejecución...")
    app.run_polling()