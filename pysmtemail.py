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


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# most_recent_read = '2023-01-08'

def download_attachment(service,messageid):
    
    msg = service.users().messages().get(userId='me', id=messageid).execute()
    parts = msg.get('payload').get('parts')
    all_parts = []
    for part in parts:
        if part.get('parts'):
            all_parts.extend(part.get('parts'))
        else:
            all_parts.append(part)

    for part in all_parts:
        if bool(re.search('.*(\.CSV)', part['filename'])):
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
    conn = pyodbc.connect('Driver={SQL Server};'f"Server={config['sql_server']};"f"Database={config['database']};"'Trusted_Connection=yes;')
    cursor = conn.cursor()

    rows=[]
    for row in data:
        column_values = {
            "DT" : datetime.strptime(f"{row['USAGE_DATE']} {row['USAGE_END_TIME']}", '%m/%d/%Y %H:%M'),
            "KWH" : row['USAGE_KWH'],
            "TimeStart" : f"{row['USAGE_START_TIME']}",
            "TimeEnd" : f"{row['USAGE_END_TIME']}",
            "ReadDate" : f"{row['USAGE_DATE']}"
        }
        rows.append(column_values)
    
    inserts = f"INSERT INTO {config['table']} (DT,KWH,TimeStart,TimeEnd,ReadDate) VALUES"
    for row in rows:
        # date_string = datetime.strptime(f"{row['USAGE_DATE']}{row['USAGE_END_TIME']}", '%m/%d/%Y %H:%M')
        insert=f"(\'{row['DT']}\',\'{row['KWH']}\',\'{row['TimeStart']}\',\'{row['TimeEnd']}\',\'{row['ReadDate']}\'),"
        inserts+=(insert)
    
    inserts=inserts.rstrip(',')
    print(inserts)
    cursor.execute(inserts)

    cursor.commit()
    cursor.close()
    # conn.close()

    return


def get_latest_readdate():
    config = read_config()
    conn = pyodbc.connect('Driver={SQL Server};'f"Server={config['sql_server']};"f"Database={config['database']};"'Trusted_Connection=yes;')

    cursor = conn.cursor()
    cursor.execute(f"SELECT top (1) [DT] FROM {config['table']} order by DT desc")

    for i in cursor:
        latest_date=i[0].strftime("%Y-%m-%d")
        print(latest_date)
    # return the epoch if your database is new.
    try: latest_date
    except:
        logging.info('sql database appears to be empty.  Starting from the beginning.')
        return '1970-01-01'
    return latest_date

def read_config() -> dict:
    if os.path.exists('smt_download_config.json'):
        json_path=open('smt_download_config.json','r')
        config = json.load(json_path) 
        json_path.close()
        return config
        
def get_oauth():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds
