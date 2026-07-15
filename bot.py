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
    await update.message.reply_text('¡Hola! Envía /download <enlace> para obtener tu enlace compatible con iPhone 🚀')

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Por favor, envía un enlace. Ejemplo: /download https://youtube.com/watch?v=...")
        return

    url = context.args[0]
    status_msg = await update.message.reply_text("⏳ Procesando enlaces de audio y video...")

    # yt-dlp configurado para buscar formatos con audio y video integrados (evita videos mudos)
    ydl_opts = {
        'format': 'best[ext=mp4]/best',  # Prioriza MP4 nativo para iOS
        'socket_timeout': 60,
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = yt_dlp.YoutubeDL({'socket_timeout': 60}).extract_info(url, download=False)
            
            title = info.get('title', 'Video sin título')
            duration_sec = info.get('duration', 0)
            duration_min = round(duration_sec / 60, 1)
            
            # Extraer URL directa asegurando compatibilidad móvil
            direct_url = info.get('url')
            
            # Si el formato principal no da la URL directa, buscamos en los formatos disponibles uno con audio y video
            for f in info.get('formats', []):
                if f.get('url') and f.get('ext') == 'mp4' and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    direct_url = f.get('url')
                    if f.get('height') and f.get('height') <= 720:
                        break

        if not direct_url:
            await status_msg.edit_text("❌ No se pudo generar un enlace compatible.")
            return

        # Respuesta estructurada para iPhone y Telegram
        response_text = (
            f"🍏 **{title}**\n"
            f"⏱ Duración: {duration_min} min\n\n"
            f"📲 **Instrucciones para iPhone:**\n"
            f"1. Abre el enlace en **Safari**.\n"
            f"2. Mantén presionado el reproductor o usa el botón de descargas para guardarlo en tu carrete.\n\n"
            f"🔗 **Enlace directo (Con Audio):**\n{direct_url}"
        )

        await status_msg.edit_text(response_text, disable_web_page_preview=False)

    except Exception as e:
        await status_msg.edit_text(f"❌ Ocurrió un error: {str(e)}")

if __name__ == '__main__':
    TOKEN = os.getenv("TOKEN", "8723783721:AAFIicHnrSrEB5YVurEasSxIN3R_OdrRaLU")
    
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("download", download_video))
    
    print("Bot en ejecución...")
    app.run_polling()