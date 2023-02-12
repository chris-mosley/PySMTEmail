# PySMTEmail

Along the same lines as [pysmtreader](https://github.com/scadaguru/pysmtreader), this is meant to grab the data from Smart Meter Texas.  But uses a completely different mechanism.

The reason you might want to use this instead of the already existing pysmtreader is that this should be _slightly_ less fragile.  This is through no fault of pysmtreader.  Calling the the SMT API _finicky_ would be kind.

The other reason you might want to use this would be to get higher resolution.  Via the API you're basically stuck with 1hr resolution.  This allows 15m resolution.

## Downsides

The primary downside is that you have to wait until end-of-day to get your data.  This also complicates something like a metric exporter because prometheus doesn't really want to deal with included timestamps.  This is a problem on the todo list.

## SQL
Currently this inserts into a table in an MSSQL Server. the createdatabase.sql file in the repo will create the database and table for you.

## Grafana
I have included a basic grafana dashboard to view this once you have it in SQL.

### Disclaimer.  
As of writing this is currently still very very new.  You will need to get your own API key authorized for your gmail account, [this page](https://developers.google.com/gmail/api/quickstart/python) should give you all the steps you need to get started of you're really insistent on doing it _now_.

## I want to use it RIGHT NOW!
So for those that are so inclined the steps to make this work are
- Create an account at [SmartMeterTexas](https://www.smartmetertexas.com), your ESIID can be found on your electric bill
- Under Manage Subscriptions, create new subscription to email you 15 Minute Interval CSVs every day.
- In GMail create a rule to automatically add the "smt" label to every email, the easiest way to do this would be to import the pysmtemailfilter.xml file in the repo.

- On your SQL server run createdatabase.sql
- Set the sql_server in smt_download_config.json to the name of your sql instance.

- Log into the [Google Cloud Console](https://console.cloud.google.com)
- Create a new project, or use an existing one if you know what you're doing.
- On your project page, go to "Enabled APIs and services"
- At the top, click "+ Enable APIS AND SERVICES"
- Search for "Gmail API" and select "Gmail API" in the result list
- Enable API
- On OAuth consent screen click "Edit App"
- App name can be anything.  Fill in your email and an arbitrary website for the Authorized Domains. -> Save and Continue
- Add or remove Scopes
- Enable the https://www.googleapis.com/auth/gmail.readonly scope.
- Go to APIs & Services > Credentials > Create Credentials > Oauth client ID
- Save and continue.  Be sure that your email is one of the test users.

- For Application type select "Desktop app"
-   You can name this anything you want.
- Click "DOWNLOAD JSON" and save this as "credentials.json" in the same directory as generate_token.py
- Run generate_token.py.  It will pop up an oauth screen for you to accept.  (this requires python 3.10)
- Copy token.json to be next to your smt_download_config.json file
- The docker image is at cmosley/pysmtemail:latest, please check docker-compose.yaml.

### I know this is a ridiculous list of steps.  I'm working on trying to simplify this, mostly all the API stuff.