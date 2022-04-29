import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
logging.basicConfig(format='%(asctime)s %(levelname)-4s : %(message)s', datefmt='%H:%M:%S', filename=BASE_DIR / 'bot.log', encoding='utf-8', level=logging.INFO)

def log(text):
    logging.info(f"{text}")
