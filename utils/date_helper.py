from datetime import datetime
import pandas as pd

def parse_excel_date(value):
    if pd.isna(value) or str(value).strip() == '':
        return None
    
    try:
        if isinstance(value, (int, float)):
            # Excel date format (25569 = 1/1/1970)
            return pd.to_datetime((value - 25569) * 86400, unit='s', utc=True).tz_convert(None)
        else:
            return pd.to_datetime(value)
    except:
        return None