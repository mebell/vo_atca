import os
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from oauth2client.tools import argparser, run_flow
import time
import datetime
from time import gmtime, strftime


def send_SMS(ra, dec, subject):
    # Send out email alert:
    f = open('Email.txt','w')
    time = strftime("%Y-%m-%d-T%H:%M:%S", gmtime())
    f.write('HESS trigger email recieved')
    f.write('\n')
    f.write("Time is "+time)
    f.write('\n')
    f.write('Coordinates: RA = '+str(ra)+' Dec = '+str(dec))
    f.write('\n')
    f.close()
    # Send out email alert
    os.system("mail -s \"Triggering ATCA: "+subject+"\" mebell.GRB@groups.smsbroadcast.com.au  < Email.txt")


# Setup the Gmail API
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('gmail', 'v1', http=creds.authorize(Http()))

dates = []
hess_email = []
hess_trig_sent = []

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
	subject_split = subject[0]
	#### Do the check the Mid GRBs ####
	if (body[0:3]=='YES') and (subject_split.find('GRB') != -1):
	   print "Email trigger found, parsing trigger"
	   # get the ra and dec
	   text = body.split(' ')
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

	#### Check for HESS triggers ####
	if (subject_split.find('HESS')!=-1) and (body[0:3] != 'YES'):
	  date_time = subject[0].split('HESS:')[1]
	  #count = hess_email.count(date_time)
	  text = body.split(' ')
	  ra = [s for s in text if "RA" in s]
	  ra = float(ra[0].split('=')[1])
	  dec = [s for s in text if "DEC" in s]
	  dec = float(dec[0].split('=')[1])
	  web_link = 'no_web_link'
	  if date_time not in hess_email:
	     print "Found HESS trigger"
	     send_SMS(ra, dec, subject='HESS Trigger') 
	     hess_email.append(date_time)
	if (subject_split.find('HESS')!=-1) and (body[0:3] == 'YES'):
	   date_time = subject[0].split('HESS:')[1]
	   #count = hess_trig_sent.count(date_time)
	   text = body.split(' ')
	   ra = [s for s in text if "RA" in s]
	   ra = float(ra[0].split('=')[1])
	   dec = [s for s in text if "DEC" in s]
	   dec = float(dec[0].split('=')[1])
	   web_link = 'no_web_link'
	   if date_time not in hess_trig_sent: 
	      print "Email trigger found, parsing trigger"
	      os.system('python schedule_HESS.py '+str(ra)+' '+str(dec)+' '+web_link+' '+'HESS')
	      hess_trig_sent.append(date_time)         
	#######################
	time.sleep(20) # Delay before re-checking email. 
      except KeyboardInterrupt:
	       break
      except: print str(datetime.datetime.now())+': Code could not retrieve mail'
