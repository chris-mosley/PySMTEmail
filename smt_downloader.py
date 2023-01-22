from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pprint import pprint
import pyodbc
import json
import re
from base64 import urlsafe_b64decode
import csv
from datetime import datetime,time


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# most_recent_read = '2023-01-08'

def main():
    
    config=read_config()
    creds=get_oauth()
    most_recent_read=get_latest_readdate()
    # most_recent_read='2023-01-16'
    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        if not labels:
            print('No labels found.')
            return
        # print('Labels:')
        for label in labels:
            if label['name'] == config['download_label']:
                label_id = label['id']
                break

        if label_id is None:
            print(f"label {config['download_label']} not found.")
            return
        message_list = service.users().messages().list(userId='me',labelIds=label_id,q=f"after:{most_recent_read}").execute()['messages']
        # messages = message_results.get('me')
        for message in message_list:
            # pprint(message)
            attachment_dict=download_attachment(service,message['id'])
            if config['use_sql']:
                insert_sql(attachment_dict)
            


    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


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
    #         "KWH" : row['USAGE_KWH'],
    #         # the space is in the format because for some god forsaken reason theres a space in the data
    #         "TimeStart" : datetime.strptime(f"{row['USAGE_START_TIME']}", ' %H:%M'),
    #         "TimeEnd" : datetime.strptime(f"{row['USAGE_END_TIME']}", ' %H:%M'),
    #         "ReadDate" : datetime.strptime(f"{row['USAGE_DATE']}", '%m/%d/%Y')

    
    inserts=inserts.rstrip(',')
    # print(inserts)
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

    type(cursor)
    for i in cursor:
        latest_date=i[0].strftime("%Y-%m-%d")
        # print(latest_date)
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


if __name__ == '__main__':
    
    main()
