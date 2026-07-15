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
    await update.message.reply_text('¡Hola! Envía /download <enlace> para obtener el link directo de tu video 🚀')

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Por favor, envía un enlace. Ejemplo: /download https://youtube.com/watch?v=...")
        return

    url = context.args[0]
    status_msg = await update.message.reply_text("⏳ Analizando video y generando enlace...")

    # Opciones para extraer información y enlaces directos sin descargar el archivo al servidor
    ydl_opts = {
        'format': 'best',
        'socket_timeout': 60,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extraemos los datos sin descargar físicamente
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Video sin título')
            duration_sec = info.get('duration', 0)
            duration_min = round(duration_sec / 60, 1)
            
            # Buscamos un enlace directo de descarga/reproducción de la lista de formatos
            direct_url = None
            for f in info.get('formats', []):
                # Buscamos formato con video y audio combinados o directo accesible
                if f.get('url') and f.get('ext') == 'mp4' and f.get('height'):
                    direct_url = f.get('url')
                    if f.get('height') <= 720: # Preferiblemente 720p o menor para ligereza
                        break

            # Si no encontró un mp4 exacto, tomamos la URL principal del info
            if not direct_url:
                direct_url = info.get('url')

        if not direct_url:
            await status_msg.edit_text("❌ No se pudo extraer un enlace directo para este video.")
            return

        # Mensaje con la información y el enlace directo limpio
        response_text = (
            f"🎬 **{title}**\n"
            f"⏱ Duración: {duration_min} minutos\n\n"
            f"🔗 **Enlace de reproducción/descarga directa:**\n{direct_url}"
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