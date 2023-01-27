

import sys
import subprocess
import pkg_resources
import os

required = {'googleapis-common-protos', 'google-auth-oauthlib', 'google-api-python-client'}
installed = {pkg.key for pkg in pkg_resources.working_set}
missing = required - installed

## make sure the google modules are installed

if missing:
  python = sys.executable
  subprocess.check_call([python, '-m', 'pip', 'install', *missing], stdout=subprocess.DEVNULL)


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


creds = None
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
try:
  creds = Credentials.from_authorized_user_file(f"{os.path.join(os.getcwd(),'token.json')}", SCOPES)
except:
  pass
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        if not os.path.exists(f"{os.getcwd()}/credentials.json"):
          print(f"credentials.json file is missing.  Please place it at {os.path.join(os.getcwd(),'credentials.json')}")
        flow = InstalledAppFlow.from_client_secrets_file(
            f"{os.path.join(os.getcwd(),'credentials.json')}", SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
        print(f"\ntoken file saved at {os.path.join(os.getcwd(),'token.json')}.  Please copy this file to the /config mapped folder for your container")
        print("\nnote, this token gives full read access to your email.  And it can renew itself.  Be careful with it.")
else:
  print(f"{os.path.join(os.getcwd(),'token.json')} appears to be a valid token.")





