from core.downloader import download_report
from core.processor import CbossTicketProcessor
from loguru import logger
import sys

logger.add("logs/cboss_import_{time}.log", rotation="10 MB")

if __name__ == "__main__":
    try:
        excel_file = download_report()
        processor = CbossTicketProcessor()
        processor.process_file(str(excel_file))
        
    except Exception as e:
        logger.critical(f"Critical error: {e}")
        sys.exit(1)