import logging

def log_info(text):
    logging.basicConfig(format='%(asctime)s: %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p', filename='bot.log', level=logging.INFO)
    logger = logging.getLogger()
    logger.info(text)
