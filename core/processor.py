import pandas as pd
from pathlib import Path
from loguru import logger
from utils.date_helper import parse_excel_date
from core.database import get_db_connection

class CbossTicketProcessor:
    
    def proper_case(self, value):
        if not value or str(value).strip() == '':
            return None
        return str(value).lower().title().strip()

    def generate_ticket_id(self, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT ticket_id FROM cboss_tickets ORDER BY ticket_id DESC LIMIT 1")
        result = cursor.fetchone()
        cursor.close()
        
        if not result or not result[0]:
            return 'TT00001'
        last_number = int(result[0][2:])
        return f"TT{str(last_number + 1).zfill(5)}"
    
    def clean_value(self, value):
        """Convert NaN, 'nan', None, atau string kosong jadi None (NULL di DB)"""
        if pd.isna(value) or str(value).strip().lower() in ['nan', 'none', '']:
            return None
        return value
    
    def format_datetime(self, dt_value):
        """Convert pandas Timestamp / datetime jadi string yang aman untuk MySQL"""
        if pd.isna(dt_value):
            return None
        try:
            return pd.to_datetime(dt_value).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return None

    def process_file(self, excel_path: str):
        logger.info(f"Processing file: {excel_path}")
        
        excel_file = pd.ExcelFile(excel_path)
        total_sheets = len(excel_file.sheet_names)
        logger.info(f"Total sheets ditemukan: {total_sheets}")
        
        success_count = 0
        skipped_count = 0
        close_skipped_count = 0

        with get_db_connection() as conn:
            for sheet_name in excel_file.sheet_names:
                # logger.info(f"Memproses sheet: {sheet_name}")
                
                try:
                    # Baca sheet, skip 4 baris header
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None, skiprows=4)
                    
                    if df.empty or len(df) < 1:
                        continue
                        
                    logger.info(f"Processing {sheet_name} of Sheet{total_sheets - 1} - Row Data : {len(df)}")

                    for idx, row in df.iterrows():
                        try:
                            # Skip baris kosong
                            if len(row) < 6 or (pd.isna(row.iloc[0]) and pd.isna(row.iloc[4])):
                                continue

                            subscriber_number = str(row.iloc[4]).strip() if not pd.isna(row.iloc[4]) else ''
                            if not subscriber_number:
                                continue

                            mapped = {
                                'site_id': subscriber_number,
                                'province': self.proper_case(row.iloc[26] if len(row) > 26 else None),
                                'spmk': self.clean_value(row.iloc[2] if len(row) > 2 else None),
                                'problem_map': self.clean_value(row.iloc[8] if len(row) > 8 else None),
                                'trouble_category': self.clean_value(row.iloc[19] if len(row) > 19 else None),
                                'detail_action': self.clean_value(row.iloc[9] if len(row) > 9 else None),
                                'status': self.clean_value(row.iloc[20] if len(row) > 20 else None),
                                
                                # Format datetime jadi string
                                'ticket_start': self.format_datetime(row.iloc[13] if len(row) > 13 else None),
                                'ticket_end': self.format_datetime(row.iloc[14] if len(row) > 14 else None),
                                'ticket_last_update': self.format_datetime(row.iloc[18] if len(row) > 18 else None),
                            }

                            # === Logic import sama seperti sebelumnya ===
                            cursor = conn.cursor()

                            # Cek SiteDetail
                            cursor.execute("SELECT 1 FROM site_details WHERE site_id = %s LIMIT 1", (mapped['site_id'],))
                            if not cursor.fetchone():
                                cursor.close()
                                skipped_count += 1
                                continue

                            # Cek existing ticket
                            existing = None
                            if mapped['ticket_start']:
                                cursor.execute("""
                                    SELECT ticket_id, status FROM cboss_tickets 
                                    WHERE ticket_start = %s AND site_id = %s LIMIT 1
                                """, (mapped['ticket_start'], mapped['site_id']))
                                existing = cursor.fetchone()

                            if existing and str(existing[1]).lower() == 'closed':
                                close_skipped_count += 1
                                cursor.close()
                                continue

                            ticket_id = existing[0] if existing else self.generate_ticket_id(conn)

                            # Insert / Update
                            cursor.execute("""
                                INSERT INTO cboss_tickets 
                                (ticket_id, site_id, province, spmk, problem_map, trouble_category, 
                                 status, detail_action, ticket_start, ticket_end, ticket_last_update, updated_at, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                                ON DUPLICATE KEY UPDATE
                                province=VALUES(province), spmk=VALUES(spmk), problem_map=VALUES(problem_map),
                                trouble_category=VALUES(trouble_category), status=VALUES(status),
                                detail_action=VALUES(detail_action), ticket_end=VALUES(ticket_end),
                                ticket_last_update=VALUES(ticket_last_update), updated_at=NOW(), created_at=NOW()
                            """, (
                                ticket_id, mapped['site_id'], mapped['province'], mapped['spmk'],
                                mapped['problem_map'], mapped['trouble_category'], mapped['status'],
                                mapped['detail_action'], mapped['ticket_start'], mapped['ticket_end'],
                                mapped['ticket_last_update']
                            ))
                            conn.commit()
                            success_count += 1
                            cursor.close()

                        except Exception as e:
                            logger.error(f"Error row {idx} sheet {sheet_name}: {e}")
                            skipped_count += 1
                            continue

                except Exception as e:
                    logger.error(f"Gagal memproses sheet {sheet_name}: {e}")

        logger.success(f"✅ Import SEMUA SHEET selesai! Success: {success_count}, Skipped: {skipped_count}, Closed: {close_skipped_count}")