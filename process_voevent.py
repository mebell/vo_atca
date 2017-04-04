#!/usr/bin/env python
"""
Processes a received VOEvent packet.

Accept a VOEvent packet via standard input. Parse it using voeventparse,
then decide what kind of packet it is, and what to do accordingly.

"""

import sys
import voeventparse
import os
import logging
logging.basicConfig(filename='atca.log',level=logging.DEBUG, format='%(asctime)s %(message)s')
logger = logging.getLogger('notifier')
logger.handlers.append(logging.StreamHandler(sys.stdout))
from fourpiskytools.notify import Notifier

def main():
    stdin = sys.stdin.read()
    v = voeventparse.loads(stdin)
    if is_grb(v):
       handle_grb(v)
    return 0

def is_grb(v):
    ivorn = v.attrib['ivorn']
    if ivorn.find("ivo://nasa.gsfc.gcn/SWIFT#BAT_GRB_Pos") == 0:
        return True
    return False

def is_short(v):
    INTEG_TIME = v.find(".//Param[@name='Integ_Time']").attrib['value']
    RATE_SIGNIF = v.find(".//Param[@name='Rate_Signif']").attrib['value']
    if (float(INTEG_TIME) < 2.0) and (float(RATE_SIGNIF) > 0.0):
       return True
    else: 
       return False

def handle_grb(v):
    ivorn = v.attrib['ivorn']
    short = is_short(v) # Work out if it is short or long: 
    if short:
       coords = voeventparse.pull_astro_coords(v)
       c = voeventparse.get_event_position(v)
       TrigID = v.find(".//Param[@name='TrigID']").attrib['value']
       web_link = 'https://gcn.gsfc.nasa.gov/other/'+TrigID+'.swift'
       os.system('python schedule_atca.py '+str(c.ra)+' '+str(c.dec)+' '+web_link)
       text = "Coords are {}".format(coords)
       n = Notifier()
       n.send_notification(title="NEW SWIFT SHORT GRB >> TRIGGERING!",
                        text=text)

if __name__ == '__main__':
    sys.exit(main())
