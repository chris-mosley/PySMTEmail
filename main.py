from pysmtemail import read_config,get_oauth,get_latest_readdate,download_attachment,insert_sql
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import logging
import pyodbc
def main():
    
    config=read_config()
    creds=get_oauth()
    most_recent_read=get_latest_readdate()
    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        if not labels:
            print('No labels found.')
            return
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

# os.system('. /bin/msodbc.sh')
# time.sleep(10)
logging.getLogger().setLevel(read_config()['log_level'])
while True:
  
  print(pyodbc.drivers())
  # we put this here so that the sleep time can be updated in real time.
  try:
    sleep_time = read_config()['polling_rate']
  except:
    logging.warning("polling_rate does not appear to be set correctly.  defaulting to 1d.")
    sleep_time = 86400
  try:
    main()
  except Exception as e: print(e)
  
  logging.info(f"sleeping {sleep_time}s")
  time.sleep(sleep_time)