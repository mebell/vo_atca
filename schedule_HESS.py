#Include the library.
import cabb_scheduler as cabb
import atca_rapid_response_api as arrApi
import sys
from math import *
from time import gmtime, strftime
import os
import logging

logging.basicConfig(filename='atca.log',level=logging.DEBUG, format='%(asctime)s %(message)s')
logger = logging.getLogger('notifier')
logger.handlers.append(logging.StreamHandler(sys.stdout))

from fourpiskytools.notify import Notifier

#### Coordinate conversion ####
def deg2sex(deg):
    sign = -1 if deg < 0 else 1
    adeg = abs(deg)
    degf = floor(adeg)
    mins = (adeg - degf)*60
    minsf = int(floor(mins))
    secs = (mins - minsf)*60
    return (sign, (degf, minsf, secs))

def deg2hms(deg, format='%02d:%02d:%05.2f'):
    # We only handle positive RA values
    assert deg >= 0
    sign, sex = deg2sex(deg/15.0)
    return format % sex

def deg2dms(deg, format='%02d:%02d:%05.2f'):
    sign, sex = deg2sex(deg)
    signchar = "+" if sign == 1 else "-"
    s = signchar + format % sex
    return s

def send_mail(ra, dec, details, subject):
    # Send out email alert:
    f = open('Email.txt','w')
    time = strftime("%Y-%m-%d-T%H:%M:%S", gmtime())
    f.write('Triggering ATCA:')
    f.write('\n')
    f.write("Time is "+time)
    f.write('\n')
    f.write('Coordinates: RA = '+(ra)+' Dec = '+str(dec))
    f.write('\n')
    f.write('Source: ')
    f.write(details)
    f.close()
    # Send out email alert
    os.system("mail -s \"Triggering ATCA: "+subject+"\" gemma.anderson@curtin.edu.au, gemma_anderson@hotmail.com, atcatriggering@gmail.com < Email.txt")

def send_SMS(ra, dec, details, subject):
    # Send out email alert:
    f = open('Email.txt','w')
    time = strftime("%Y-%m-%d-T%H:%M:%S", gmtime())
    f.write('Triggering ATCA:')
    f.write('\n')
    f.write("Time is "+time)
    f.write('\n')
    f.write('Coordinates: RA = '+(ra)+' Dec = '+str(dec))
    f.write('\n')
    f.write('Source: ')
    f.write(details)
    f.close()
    # Send out email alert
    os.system("mail -s \"Triggering ATCA: "+subject+"\" mebell.GRB@groups.smsbroadcast.com.au  < Email.txt")

################################

ra_in   = sys.argv[1]
dec_in  = sys.argv[2]
details = sys.argv[3]
what    = sys.argv[4]

ra = deg2hms(float(ra_in))
dec = deg2dms(float(dec_in))

# Make a new schedule.
schedule = cabb.schedule()

# Scan 1
scan1 = schedule.addScan(
            { 'source': "HESS", 'rightAscension': ra, 'declination': dec,
              'freq1': 5500, 'freq2': 9000, 'project': "C3374", 'scanLength': "00:15:00", 'scanType': "Dwell" }
        )

calList = scan1.findCalibrator() # Get calibrators 
currentArray = cabb.monica_information.getArray() # Get the current array
# And pass this as the arggument to the calibrator selector.
bestCal = calList.getBestCalibrator(currentArray) # And pass this as the arggument to the calibrator selector.
print "Calibrator chosen: %s, %.1f degrees away" % (bestCal['calibrator'].getName(),
                                                    bestCal['distance'])
calScan = schedule.addCalibrator(bestCal['calibrator'], scan1, { 'scanLength': "00:02:00" }) # Add to the schedule

# Loop around both of those scans
for i in xrange(0, 1): 
    schedule.copyScans([ scan1.getId() ])

# Scan 2
scan2 = schedule.addScan(
            { 'source': "HESS", 'rightAscension': ra, 'declination': dec,
              'freq1': 16700, 'freq2': 21200, 'project': "C3374", 'scanLength': "00:05:00", 'scanType': "Dwell" }
        )
 
calList = scan2.findCalibrator() # Get calibrators 
# And pass this as the arggument to the calibrator selector.
bestCal = calList.getBestCalibrator(currentArray) # And pass this as the arggument to the calibrator selector.
print "Calibrator chosen: %s, %.1f degrees away" % (bestCal['calibrator'].getName(),
                                                    bestCal['distance'])
calScan = schedule.addCalibrator(bestCal['calibrator'], scan2, { 'scanLength': "00:02:00" }) # Add to the schedule

# Loop around both of those scans
for i in xrange(0, 5): 
    schedule.copyScans([ scan2.getId() ])

# Tell the library that we won't be looping, so there will be a calibrator scan at the
# end of the schedule.
schedule.setLooping(False)

# Label the sched file with the current time
fname = strftime("%Y-%m-%d-T%H:%M", gmtime())
fname = fname+'.sch'

# Make a copy of the sch file for checking
schedule.write(name=fname)

# We need to turn this schedule into a string.
schedString = schedule.toString()

# Log schedule file creation
n = Notifier()
n.send_notification(title='Creating schedule file', text='Schedule file created')

# We have our schedule now, so we need to craft the service request to submit it to
# the rapid response service.
rapidObj = { 'schedule': schedString }

# The authentication token needs to go with it, and we point to the file that
# contains the token.
rapidObj['authenticationTokenFile'] = "authorisation_token_C3374_2020APR.jwt"
# The name of the main target needs to be specified.
rapidObj['nameTarget'] = "MAXI"

# So does the name of the calibrator.
rapidObj['nameCalibrator'] = bestCal['calibrator'].getName()
# The email address of the requester needs to be there.
rapidObj['email'] = "martinbell81@googlemail.com"
# We want to use whatever frequencies are running at the time.
rapidObj['usePreviousFrequencies'] = False

# Because this is a test run, we'll specify a few parameters to just try things out.
rapidObj['test'] = True
#rapidObj['emailOnly'] = "Martin.Bell@csiro.au"
rapidObj['noTimeLimit'] = True
rapidObj['noScoreLimit'] = True
rapidObj['minimumTime'] = 2.0

# Send out email from our end. ATCA will also send a bunch
send = True
if send:
   send_mail(ra, dec, details, subject='HESS GRB')
   send_SMS(ra, dec, details, subject='HESS GRB')

# Send the request.
send = False # Toggle to actually trigger or not
if send:
   request = arrApi.api(rapidObj)
   try:
      response = request.send()
   except arrApi.responseError as r:
      n.send_notification(title="ATCA return message:", text=r)
   #############################
