import os
import re
from dotenv import load_dotenv
import yt_dlp
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

load_dotenv()

TRANSFER_SH_URL = os.getenv("TRANSFER_SH_URL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TRANSFERSH_PUBLIC_LINK = os.getenv("TRANSFERSH_PUBLIC_LINK")

YOUTUBE_URL_PATTERN = re.compile(r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|\S*youtu\.be/)\S+')

def download_video(url: str, output_path: str) -> str:
    ydl_opts = {
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

def upload_to_transfer(file_path: str) -> str:
    file_name = file_path.split('/')[-1]
    with open(file_path, "rb") as file:
        response = requests.post(TRANSFER_SH_URL, files={file_name: file})
    if response.ok:
        response_text = response.text.strip()
        # Extract only the relevant part
        relevant_part = response_text.split('/')[-2:]
        combined_link = f"{TRANSFERSH_PUBLIC_LINK}/{'/'.join(relevant_part)}"
        return combined_link
    else:
        return f"Failed to upload the file. Status code: {response.status_code}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text
    if YOUTUBE_URL_PATTERN.search(message_text):
        output_path = './downloads'
        os.makedirs(output_path, exist_ok=True)

        try:
            await update.message.reply_text("Downloading video...")
            video_file = download_video(message_text, output_path)
            await update.message.reply_text(f"Downloaded: {os.path.basename(video_file)}\nUploading to transfer.sh...")
            link = upload_to_transfer(video_file)
            await update.message.reply_text(f"Here's your file: {link}")
            os.remove(video_file)  # Clean up downloaded file
        except Exception as e:
            await update.message.reply_text(f"An error occurred: {e}")
    else:
        await update.message.reply_text("Send a YouTube video URL to download.")

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()
