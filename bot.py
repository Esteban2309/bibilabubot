import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
import yt_dlp

# Configurar logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Guarda los chat_id que ya recibieron el mensaje de bienvenida,
# para saber cuándo es el "primer mensaje" de alguien.
usuarios_conocidos = set()

# Ruta opcional a un cookies.txt exportado del navegador (formato Netscape).
# YouTube a veces exige "confirmar que no eres un bot" en servidores/nube;
# pasarle cookies de una sesión real es la solución oficial de yt-dlp.
COOKIES_FILE = os.getenv("YT_COOKIES_FILE")

COMANDOS_TEXT = (
    "📖 Guía de Comandos Disponibles:\n"
    "• /start - Muestra este mensaje de bienvenida.\n"
    "• /help - Muestra la guía de ayuda y los ejemplos de uso.\n"
    "• /download <enlace> - Extrae el enlace directo de streaming y descarga.\n\n"
    "💡 Ejemplo de uso: /download https://youtube.com/watch?v=tu_video"
)


def bienvenida_text():
    return (
        "🐱 ¡Miau! Soy Kenji, un gatito bot que ama a Eli con todo su corazón. 💕\n\n"
        "Estoy listo para ayudarte a extraer enlaces directos con audio y video integrados, "
        "compatibles con iPhone y PC, sin límites de peso por tamaño de archivo.\n\n"
        f"{COMANDOS_TEXT}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuarios_conocidos.add(update.effective_chat.id)
    await update.message.reply_text(bienvenida_text())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuarios_conocidos.add(update.effective_chat.id)
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
    usuarios_conocidos.add(update.effective_chat.id)

    if not context.args:
        await update.message.reply_text(
            "❌ Falta el enlace.\nEjemplo correcto:\n/download https://youtube.com/watch?v=..."
        )
        return

    url = context.args[0]
    status_msg = await update.message.reply_text("⏳ Procesando enlaces de audio y video en la nube...")

    # Configuración basada en cliente iOS/Android
    ydl_opts = {
        'format': 'best',
        'socket_timeout': 60,
        'extractor_args': {'youtube': {'player_client': ['ios', 'android']}},
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    }

    # Si hay un archivo de cookies configurado, se usa para evitar el bloqueo
    # "Sign in to confirm you're not a bot" que YouTube aplica frecuentemente
    # a IPs de servidores/nube.
    if COOKIES_FILE and os.path.exists(COOKIES_FILE):
        ydl_opts['cookiefile'] = COOKIES_FILE

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


async def mensaje_general(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Se dispara con cualquier texto que no sea uno de los comandos reconocidos.
    Si es el primer mensaje de ese chat, responde con la bienvenida completa."""
    chat_id = update.effective_chat.id

    if chat_id not in usuarios_conocidos:
        usuarios_conocidos.add(chat_id)
        await update.message.reply_text(bienvenida_text())
    else:
        await update.message.reply_text(
            "🐾 No entendí ese mensaje. Aquí tienes de nuevo mis comandos:\n\n" + COMANDOS_TEXT
        )


if __name__ == '__main__':
    # ⚠️ Usa una variable de entorno para el token. No lo dejes escrito en el código.
    TOKEN = os.getenv("TOKEN", "TU_TOKEN_AQUI")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("download", download_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje_general))

    print("Bot en ejecución...")
    app.run_polling()