# Include the library.
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

def send_mail(ra, dec, details):
    # Send out email alert:
    f = open('Email.txt','w')
    time = strftime("%Y-%m-%d-T%H:%M:%S", gmtime())
    f.write('Triggering ATCA:')
    f.write('\n')
    f.write("Time is "+time)
    f.write('\n')
    f.write('Coordinates: RA = '+(ra)+' Dec = '+str(dec))
    f.write('\n')
    f.write('Source = Short GRB')
    f.write('\n')
    f.write(details)
    f.close()
    # Send out email alert
    os.system("mail -s \"Triggering ATCA on short GRB\" martin.bell@csiro.au, gemma.anderson@curtin.edu.au < Email.txt")

################################

ra_in = sys.argv[1]
dec_in = sys.argv[2]
details = sys.argv[3]

print "VO Details:"
print details

ra = deg2hms(float(ra_in))
dec = deg2dms(float(dec_in))

print "RA, Dec:"
print ra, dec

# Make a new schedule.
schedule = cabb.schedule()

# Add a scan to look at the VO coordinates.
scan1 = schedule.addScan(
    { 'source': "SHORT_GRB", 'rightAscension': ra, 'declination': dec,
      'freq1': 5500, 'freq2': 9000, 'project': "C3204", 'scanLength': "00:20:00", 'scanType': "Dwell" }
)

# Since we definitely want to get onto source as quickly as possible, we tell the
# library not to go to the calibrator first.
schedule.disablePriorCalibration()

# Request a list of nearby calibrators from the ATCA calibrator database.
calList = scan1.findCalibrator()

# Ask for the library to choose the best one for the current array. We first need to
# get the current array from MoniCA.
currentArray = cabb.monica_information.getArray()
# And pass this as the arggument to the calibrator selector.
bestCal = calList.getBestCalibrator(currentArray)

print "Calibrator chosen: %s, %.1f degrees away" % (bestCal['calibrator'].getName(),
                                                    bestCal['distance'])

# We add this calibrator to the schedule, attaching it to the scan it
# will be the calibrator for. We'll ask to observe the calibrator for 2
# minutes.
calScan = schedule.addCalibrator(bestCal['calibrator'], scan1, { 'scanLength': "00:02:00" })

# We want the schedule to run for about 12 hours, so we want another 36 copies
# of these two scans. Remembering that the library will take care of
# associating a calibrator to each source, we only need to copy the source
# scan.
for i in xrange(0, 36):
    schedule.copyScans([ scan1.getId() ])

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

# We have our schedule now, so we need to craft the service request to submit it to
# the rapid response service.
rapidObj = { 'schedule': schedString }
# The authentication token needs to go with it, and we point to the file that
# contains the token.
rapidObj['authenticationTokenFile'] = "authorisation_token_test_C3204_2016OCT.jwt"
# The name of the main target needs to be specified.
rapidObj['nameTarget'] = "SHORT_GRB"
# So does the name of the calibrator.
rapidObj['nameCalibrator'] = bestCal['calibrator'].getName()
# The email address of the requester needs to be there.
rapidObj['email'] = "Martin.Bell@csiro.au"
# We want to use whatever frequencies are running at the time.
rapidObj['usePreviousFrequencies'] = True

# Because this is a test run, we'll specify a few parameters to just try things out.
rapidObj['test'] = True
rapidObj['emailOnly'] = "Jamie.Stevens@csiro.au"
rapidObj['noTimeLimit'] = True
rapidObj['noScoreLimit'] = True
#rapidObj['noEmail'] = True

# Send the request.
request = arrApi.api(rapidObj)
try:
    response = request.send()
except arrApi.responseError as r:
    print r.value
#############################

# Send out email
send_mail(ra, dec, details)


