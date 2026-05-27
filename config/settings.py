from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

class Settings:
    DOWNLOAD_DIR = BASE_DIR / "downloads"
    LOG_DIR = BASE_DIR / "logs"
    
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_DATABASE = os.getenv("DB_DATABASE")
    DB_USERNAME = os.getenv("DB_USERNAME")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    
    HEADLESS = os.getenv("HEADLESS")
    CBOSS_URL = os.getenv("CBOSS_BASE_URL")
    
    REPORT_BASE_URL = os.getenv("CBOSS_BASE_URL")
    REPORT_NAME = os.getenv("CBOSS_REPORT_NAME")
    
    @staticmethod
    def get_report_url():
        today = datetime.now()
        six_months_ago = today - timedelta(days=60)  # approx 6 bulan
        
        start = six_months_ago.strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")
        
        return f"{Settings.REPORT_BASE_URL}?__report={Settings.REPORT_NAME}&start={start}%2000:00:00&end={end}%2023:59:59&__format=xlsx"

settings = Settings()
settings.DOWNLOAD_DIR.mkdir(exist_ok=True)
settings.LOG_DIR.mkdir(exist_ok=True)