from playwright.sync_api import sync_playwright
from config.settings import settings
from loguru import logger
from pathlib import Path
import os

def download_report():
    url = settings.get_report_url()
    logger.info(f"Mencoba download dari: {url}")
    
    with sync_playwright() as p:
        # Launch browser
        headless_mode = os.getenv("HEADLESS", "true").lower() in ["true", "1", "yes"]
        
        browser = p.chromium.launch(headless=headless_mode)  # headless=False dulu buat debug
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        # Setup download listener
        download_path = None
        
        def handle_download(download):
            nonlocal download_path
            filename = download.suggested_filename
            download_path = settings.DOWNLOAD_DIR / filename
            logger.info(f"Download dimulai: {filename}")
            download.save_as(download_path)
        
        page.on("download", handle_download)
        
        try:
            # Kunjungi URL
            response = page.goto(url, wait_until="networkidle", timeout=120000)
            
            # Tunggu sebentar biar download mulai
            page.wait_for_timeout(8000)  # 8 detik cukup biasanya
            
            if download_path and download_path.exists():
                logger.success(f"✅ Download berhasil: {download_path}")
                browser.close()
                return download_path
            else:
                logger.warning("Download tidak terdeteksi, coba cara alternatif...")
                
                # Cara alternatif: paksa download via request
                browser.close()
                return download_via_request(url)
                
        except Exception as e:
            logger.error(f"Error saat goto: {e}")
            browser.close()
            return download_via_request(url)  # fallback


def download_via_request(url):
    """Fallback menggunakan requests (lebih stabil untuk direct download)"""
    import requests
    from urllib.parse import urlparse
    
    logger.info("Menggunakan fallback requests untuk download...")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=120)
        response.raise_for_status()
        
        # Ambil filename dari Content-Disposition atau buat sendiri
        filename = "cboss_report.xls"
        if 'Content-Disposition' in response.headers:
            import re
            match = re.search(r'filename="?([^"]+)"?', response.headers['Content-Disposition'])
            if match:
                filename = match.group(1)
        
        file_path = settings.DOWNLOAD_DIR / filename
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        logger.success(f"✅ Download via requests berhasil: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Requests download gagal: {e}")
        raise
    
