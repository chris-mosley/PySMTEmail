from __future__ import print_function

import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import pyodbc
import json
import re
from base64 import urlsafe_b64decode
import csv
from datetime import datetime
import logging
from zoneinfo import ZoneInfo




def download_attachment(service,messageid):
    
    msg = service.users().messages().get(userId='me', id=messageid).execute()
    logging.debug(msg)
    parts = msg.get('payload').get('parts')
    all_parts = []
    for part in parts:
        if part.get('parts'):
            all_parts.extend(part.get('parts'))
        else:
            all_parts.append(part)

    for part in all_parts:
        if bool(re.search('.*(\.CSV)', part['filename'], flags=re.IGNORECASE)):
            attachmentId = part['body']['attachmentId']
            file_name = part['filename']
    
    data=(service.users().messages().attachments().get(userId='me', id=attachmentId, messageId=messageid).execute())['data']
    csv_raw = urlsafe_b64decode(data).decode("utf-8").splitlines()
    csv_dict=csv.DictReader(csv_raw,skipinitialspace=True)

    if read_config()['save_csvs'] == True:
        w = open(file_name,'w')
        w.write(csv_raw)
        w.close()

    return csv_dict

def insert_sql(data):
    config = read_config()
    logging.debug("insert_sql running")
    if config['use_sql_trusted_connection'] == 'True':
        logging.info("use_sql_trusted_connection is True, using trusted connection.")
        conn = pyodbc.connect('Driver={SQL Server};'f"Server={config['sql_server']};"f"Database={config['database']};"'Trusted_Connection=yes;')
    else:
        logging.info("use_sql_trusted_connection is False, using sql_user and sql_pass.")
        logging.debug("using connection string: "'Driver={ODBC Driver 18 for SQL Server};'f"Server={config['sql_server']};"f"Database={config['database']};"f"UID={config['sql_user']};PWD={config['sql_pass']};Encrypt=yes;TrustServerCertificate=yes")
        conn = pyodbc.connect('Driver={ODBC Driver 18 for SQL Server};'f"Server={config['sql_server']};"f"Database={config['database']};"f"UID={config['sql_user']};PWD={config['sql_pass']};Encrypt=yes;TrustServerCertificate=yes")
    
    cursor = conn.cursor()

    rows=[]
    for row in data:
        column_values = {
            "DT" : datetime.strptime(f"{row['USAGE_DATE']} {row['USAGE_END_TIME']}", '%m/%d/%Y %H:%M'),
            "KWH" : row['USAGE_KWH'],
            "TimeStart" : f"{row['USAGE_START_TIME']}",
            "TimeEnd" : f"{row['USAGE_END_TIME']}",
            "ReadDate" : f"{row['USAGE_DATE']}",
            "UTC": (datetime.strptime(f"{row['USAGE_DATE']} {row['USAGE_END_TIME']}", '%m/%d/%Y %H:%M')).replace(tzinfo=ZoneInfo('US/Central')).astimezone(ZoneInfo('UTC'))
        }
        rows.append(column_values)
    
    # we use upserts because google's filter doesn't always return perfect results.  its pretty upserting.
    upserts = [create_upsert(config['table'],row) for row in rows]
    upserts = ";".join(upserts)
    logging.debug(upserts)
    cursor.execute(upserts)

    cursor.commit()
    cursor.close()
    
    return

def create_upsert(table,row):
    logging.debug("creating upsert")
    upsert=f"""UPDATE {table} set [DT] = '{row['DT']}', [KWH] = '{row['KWH']}', [TimeStart] = '{row['TimeStart']}', [TimeEnd] = '{row['TimeEnd']}', [ReadDate] = '{row['ReadDate']}' where [UTC] = '{row['UTC']}'
    if @@ROWCOUNT = 0 INSERT INTO {table} (UTC,DT,KWH,TimeStart,TimeEnd,ReadDate) VALUES('{row['UTC']}','{row['DT']}','{row['KWH']}','{row['TimeStart']}','{row['TimeEnd']}','{row['ReadDate']}')"""
    
    logging.debug(f"created upsert {upsert}")
    return upsert

def get_latest_readdate():
    config = read_config()
    
    if config['backfill'] == True:
        logging.info("Backfill mode enabled.  Going allllllll the way back.  Not recommended for ongoing use.")
        return '1970-01-01'

    logging.debug(print(config))
    if config['use_sql_trusted_connection'] == 'True':
        logging.info("use_sql_trusted_connection is True, using trusted connection.")
        conn = pyodbc.connect('Driver={SQL Server};'f"Server={config['sql_server']};"f"Database={config['database']};"'Trusted_Connection=yes;')
    else:
        logging.info("use_sql_trusted_connection is False, using sql_user and sql_pass.")
        logging.debug("using connection string: "'Driver={ODBC Driver 18 for SQL Server};'f"Server={config['sql_server']};"f"Database={config['database']};"f"User Id={config['sql_user']};Password={config['sql_pass']};Encrypt=yes;TrustServerCertificate=yes")
        conn = pyodbc.connect('Driver={ODBC Driver 18 for SQL Server};'f"Server={config['sql_server']};"f"Database={config['database']};"f"UID={config['sql_user']};PWD={config['sql_pass']};Encrypt=yes;TrustServerCertificate=yes")

    cursor = conn.cursor()
    cursor.execute(f"SELECT top (1) [DT] FROM {config['table']} order by DT desc")
    

    for i in cursor:
        latest_date=i[0].strftime("%Y-%m-%d")
    
    # return the epoch if your database is new.
    try: latest_date
    except:
        logging.info('sql database appears to be empty.  Starting from the beginning.')
        return '1970-01-01'
    logging.info(f"latest insert returned is {latest_date}")
    return latest_date

def read_config() -> dict:
    if os.path.exists('/config/smt_download_config.json'):
        json_path=open('/config/smt_download_config.json','r')
        try:
            config = json.load(json_path) 
        except:
            logging.warning("/config/smt_download.json does not appear to be valid.")
            exit()
        json_path.close()
    else:
        logging.warning("/config/smt_download.json appears to be missing.")
    return config
        
def get_oauth():
    creds = None
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('/config/token.json'):
        creds = Credentials.from_authorized_user_file('/config/token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '/config/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('/config/token.json', 'w') as token:
            token.write(creds.to_json())
    return creds
