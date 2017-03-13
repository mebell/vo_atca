# Include the library.
import cabb_scheduler as cabb
import sys
from math import *
from time import gmtime, strftime
import os
#### Coordinate conversion ####

def deg2sex(deg):
    """ Converts angle in degrees to sexagesimal notation
    Returns tuple containing (sign, (degrees, minutes & seconds))
    sign is -1 or 1
        
    >>> deg2sex(12.582438888888889)
    (12, 34, 56.78000000000182)

    >>> deg2sex(-12.582438888888889)
    (-12, 34, 56.78000000000182)

    """

    sign = -1 if deg < 0 else 1
    adeg = abs(deg)
    degf = floor(adeg)
    mins = (adeg - degf)*60
    minsf = int(floor(mins))
    secs = (mins - minsf)*60
    return (sign, (degf, minsf, secs))

def deg2hms(deg, format='%02d:%02d:%05.2f'):
    """Convert angle in degrees into HMS using format. Default: '%d:%d:%.2f'    

    >>> deg2hms(188.73658333333333)
    '12:34:56.78'


    >>> deg2hms(-188.73658333333333)
    '-12:34:56.78'

    >>> deg2hms(-188.73658333333333, format='%dh%dm%.2fs')
    '-12h34m56.78s'

    """

    # We only handle positive RA values
    assert deg >= 0
    sign, sex = deg2sex(deg/15.0)
    return format % sex

def deg2dms(deg, format='%02d:%02d:%05.2f'):
    """Convert angle in degrees into DMS using format. Default: '%d:%d:%.2f'
    
    >>> deg2dms(12.582438888888889)
    '+12:34:56.78'

    >>> deg2dms(2.582438888888889)
    '+02:34:56.78'

    >>> deg2dms(-12.582438888888889)
    '-12:34:56.78'
    
    >>> deg2dms(12.582438888888889, format='%dd%dm%.2fs')
    '+12d34m56.78s'
    """

    sign, sex = deg2sex(deg)
    signchar = "+" if sign == 1 else "-"
    s = signchar + format % sex
    return s

def send_mail(ra, dec, details):
    # Send out email alert:
    f = open('Email.txt','w')
    f.write('TEST: Triggering ATCA:')
    f.write('\n')
    f.write('Coordinates: RA = '+(ra)+' Dec = '+str(dec))
    f.write('\n')
    f.write('Source = GRB')
    f.write('\n')
    f.write(details)
    f.close()
    # Send out email alert
    os.system("mail -s \"Triggering ATCA on GRB\" martin.bell@csiro.au < Email.txt")


################################

ra_in = sys.argv[1]
dec_in = sys.argv[2]
details = sys.argv[3]

print details

ra = deg2hms(float(ra_in))
dec = deg2dms(float(dec_in))

print ra, dec

# Make a new schedule.
schedule = cabb.schedule()

# Add a scan to look at the VO coordinates.
scan1 = schedule.addScan(
    { 'source': "target", 'rightAscension': ra, 'declination': dec,
      'freq1': 5500, 'freq2': 9000, 'project': "C001", 'scanLength': "00:20:00", 'scanType': "Dwell" }
)

# Request a list of nearby calibrators from the ATCA calibrator database.
calList = scan1.findCalibrator()

# Ask for the library to choose the best one.
bestCal = calList.getBestCalibrator()
# This should choose 2353-686.
print "Calibrator chosen: %s, %.1f degrees away" % (bestCal['calibrator'].getName(),
                                                    bestCal['distance'])

# We add this calibrator to the schedule, attaching it to the scan it
# will be the calibrator for. We'll ask to observe the calibrator for 2
# minutes.
calScan = schedule.addCalibrator(bestCal['calibrator'], scan1, { 'scanLength': "00:02:00" })

# We want the schedule to run for about an hour, so we want another two copies
# of these two scans. Remembering that the library will take care of
# associating a calibrator to each source, we only need to copy the source
# scan.
for i in xrange(0, 2):
    schedule.copyScans([ scan1.getId() ])

# Tell the library that we won't be looping, so there will be a calibrator scan at the
# end of the schedule.
schedule.setLooping(False)
    

# Label the sched file with the current time
fname = strftime("%Y-%m-%d-T%H:%M", gmtime())
fname = fname+'.sch'

#now = datetime.date.today()
schedule.write(name=fname)
# This schedule should have 7 scans, with 2353-686 at scans 1, 3, 5 and 7, and the
# magnetar at scan 2, 4 and 6.

# Send out email
send_mail(ra, dec, details)


