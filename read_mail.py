import os
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from oauth2client.tools import argparser, run_flow
import time
import datetime


# Setup the Gmail API
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('gmail', 'v1', http=creds.authorize(Http()))

dates = []

while True:
      try:
	# Read the email in a loop
	results = service.users().messages().list(userId='me', maxResults=1).execute()
	# get the message id from the results object
	message_id = results['messages'][0]['id']
	# use the message id to get the actual message, including any attachments
	message = service.users().messages().get(userId='me', id=message_id).execute()
	body = message['snippet']
        headers=message["payload"]["headers"]
        subject= [i['value'] for i in headers if i["name"]=="Subject"]
	if body[0:3]=='YES':
           print "Email trigger found, parsing trigger"
	   # get the ra and dec
	   text = body.split(' ')
           print body
	   ra = [s for s in text if "RA" in s]
	   ra = float(ra[0].split('=')[1])
	   dec = [s for s in text if "DEC" in s]
	   dec = float(dec[0].split('=')[1])
           date_time = subject[0].split('GRB: ')[1]
           if date_time not in dates:
              web_link = 'no_web_link'
              os.system('python schedule_atca.py '+str(ra)+' '+str(dec)+' '+web_link+' '+'SHORT_GRB')
              dates.append(date_time)
              print "Sending Trigger"
           else:
              print "Trigger already sent"
        time.sleep(20) # Delay before re-checking email. 
      except KeyboardInterrupt:
        break
      except: 
        print str(datetime.datetime.now())+': Code could not retrieve mail'
