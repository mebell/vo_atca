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
from time import gmtime, strftime
import voeventparse as vp

logging.basicConfig(filename='atca.log',level=logging.DEBUG, format='%(asctime)s %(message)s')
logger = logging.getLogger('notifier')
logger.handlers.append(logging.StreamHandler(sys.stdout))

from fourpiskytools.notify import Notifier

def main():
    stdin = sys.stdin.read()
    v = voeventparse.loads(stdin)
    ivorn = v.attrib['ivorn']
    if ('SWIFT' in ivorn): 
       if is_grb(v):
          handle_grb(v)
    if ('SWIFT' in ivorn)  or ('MAXI' in ivorn):
       if is_flare_star(v):
          handle_flare_star(v)
    return 0

def send_SMS(ra, dec, details, subject):
    # Send out email alert:
    f = open('Email.txt','w')
    time = strftime("%Y-%m-%d-T%H:%M:%S", gmtime())
    f.write('ATCA Trigger:')
    f.write('\n')
    f.write("Time is "+time)
    f.write('\n')
    f.write('Coordinates: RA = '+(str(ra))+' Dec = '+str(dec))
    f.write('\n')
    f.write('Source: ')
    f.write(details)
    f.close()
    # Send out email alert
    os.system("mail -s \"Triggering ATCA: "+subject+"\" mebell.GRB@groups.smsbroadcast.com.au  < Email.txt")

def send_mail(details, subject):
    # Send out email alert:
    f = open('False_Email.txt','w')
    time = strftime("%Y-%m-%d-T%H:%M:%S", gmtime())
    f.write('Not Triggering ATCA:')
    f.write('\n')
    f.write("Time is "+time)
    f.write('\n')
    f.write(details)
    f.close()
    # Send out email alert
    os.system("mail -s \"Not Triggering ATCA: "+subject+"\" atcatriggering@gmail.com, gemma.anderson@curtin.edu.au, gemma_anderson@hotmail.com < False_Email.txt")

def mid_grb_email(details, subject, ra, dec):
    # Send out email alert:
    f = open('Mid_Email.txt','w')
    f.write('RA='+ra)
    f.write('\n')
    f.write('DEC='+dec)
    f.write('\n')
    time = strftime("%Y-%m-%d-T%H:%M:%S", gmtime())
    f.write('Mid duration GRB. Please check the link and respond to this email with "YES" if trigger is to proceed:')
    f.write('\n')
    f.write("Time is "+time)
    f.write('\n')
    f.write(details)
    f.close()
    # Send out email alert
    os.system("mail -s \"Mid Duration GRB: "+time+"\" atcatriggering@gmail.com, gemma.anderson@curtin.edu.au, gemma_anderson@hotmail.com < Mid_Email.txt")

def is_grb(v):
    ivorn = v.attrib['ivorn']
    TrigID = v.find(".//Param[@name='TrigID']").attrib['value']
    # Remove test packets
    if TrigID == '99999':
       return False
    # Look for the "GRB indetified parameter - it fails if it doesn't exist". 
    if v.find(".//Param[@name='GRB_Identified']") == None:
       return False
    if v.find(".//Param[@name='StarTrack_Lost_Lock']").attrib['value'] == 'true':
       return False
    GRB_ident = v.find(".//Param[@name='GRB_Identified']").attrib['value']
    if (ivorn.find("ivo://nasa.gsfc.gcn/SWIFT#BAT_GRB_Pos") == 0) and (GRB_ident == 'true')   :
           return True
    return False

def is_short(v):
    INTEG_TIME = v.find(".//Param[@name='Integ_Time']").attrib['value']
    RATE_SIGNIF = v.find(".//Param[@name='Rate_Signif']").attrib['value']
    if (float(INTEG_TIME) < 0.257) and (float(RATE_SIGNIF) > 0.0):
       return 'short'
    if (float(INTEG_TIME) > 0.257) and (float(INTEG_TIME) < 1.025) and (float(RATE_SIGNIF) > 0.0):
       return 'mid'
    else: 
       return 'long'

def handle_grb(v):
    ivorn = v.attrib['ivorn']
    TrigID = v.find(".//Param[@name='TrigID']").attrib['value']
    web_link = 'https://gcn.gsfc.nasa.gov/other/'+TrigID+'.swift'
    grb_length = is_short(v) # Work out if it is short or long: 
    if grb_length == 'short':
       coords = voeventparse.pull_astro_coords(v)
       c = voeventparse.get_event_position(v)
       if c.dec > 15.0:
          send_mail("GRB above declination cutoff of +15 degrees  "+web_link, "Short GRB above Dec cutoff")
       else:
          os.system('python schedule_atca.py '+str(c.ra)+' '+str(c.dec)+' '+web_link+' '+'SHORT_GRB')
          n = Notifier()
          n.send_notification(title="SWIFT Short GRB >> TRIGGERING!", text = "Coords are {}".format(coords))
    if grb_length == 'mid': 
       coords = voeventparse.pull_astro_coords(v)
       c = voeventparse.get_event_position(v)
       if c.dec > 15.0:
          send_mail("GRB above declination cutoff of +15 degrees  "+web_link, "Mid GRB above Dec cutoff")
       else:
          n = Notifier()
          n.send_notification(title="SWIFT Mid GRB >> ON HOLD!", text = "Coords are {}".format(coords))
          mid_grb_email('Please check:'+web_link, "Mid duration GRB", str(c.ra), str(c.dec))
          # Send out SMS  
          send_SMS(c.ra, c.dec, web_link, subject='Mid GRB')
    if grb_length == 'long':
       send_mail("Long GRB not triggering "+web_link, "Long GRB") 

def get_name(v):
    name = 'None'
    tel  = 'None'
    ivorn = v.attrib['ivorn']
    if 'SWIFT' in ivorn:
        # Swift uses the v.Why.Inference parameter
        if hasattr(v.Why.Inference, 'Name'):
           name = v.Why.Inference.Name
           tel = 'SWIFT'
    if 'MAXI' in ivorn:
           # MAXI uses a Source_Name parameter
           src = v.find(".//Param[@name='Source_Name']")
           if src is None:
              return False
           # MAXI sometimes puts spaces at the start of the string!
           name = src.attrib['value'].strip()
           tel = 'MAXI'
    return name, tel

flare_stars =     ['Wolf424',
                   'YZ_CMi',
                   'YZCMi',
                   'YZ CMi',
                   'CN_Leo',
                   'CNLeo',
                   'CN Leo',
                   'V1054Oph',
                   'V645Cen',
                   'ROSS1280',
                   'DM-216267',
                   'V1216Sgr',
                   'HR_1099',
                   'HR 1099',
                   'HR1099',
                   'CF_Tuc',
                   'CFTuc',
                   'CF Tuc',
                   'AT_Mic',
                   'AT Mic',
                   'ATMic',
                   'AU_Mic',
                   'AUMic',
                   'AU Mic',
                   'UV_Cet',
                   'UV Cet',
                   'Flare from UV Cet',
                   'UVCet',
                   'HD 8357',
                   'HD_8357',
                   'HD8357',
                   'CC Eri',
                   'CC_Eri',
                   'CCEri',
                   'GT Mus',
                   'GT_Mus',
                   'GTMus']

def is_flare_star(v):
    name, tel = get_name(v)
    if name is not None:
       for star in flare_stars:
           if (star in name) or (star == name):
              return True
    else:
       return False

def get_flare_name(v):
    name, tel = get_name(v)
    if name is not None:
       for star in flare_stars:
           if (star in name) or (star == name):
              return star


def get_flare_RA(name):
    ra_dict = {'Wolf424'  : '12:33:17.383', 
               'YZ_CMi'   : '07:44:40.17401', 
               'YZCMi'    : '07:44:40.17401', 
               'YZ CMi'   : '07:44:40.17401', 
               'CN_Leo'   : '10:56:28.865', 
               'CN Leo'   : '10:56:28.865', 
               'CNLeo'    : '10:56:28.865', 
               'V1054Oph' : '16:55:28.75758', 
               'V645Cen'  : '14:29:42.94853',  
               'ROSS1280' : '11:47:44.3974', 
               'DM-216267': '22:38:45.5747', 
               'V1216Sgr' : '18:49:49.36216', 
               'HR_1099'  : '03:36:47.29038', 
               'HR1099'   : '03:36:47.29038', 
               'HR 1099'  : '03:36:47.29038', 
               'CF_Tuc'   : '00:53:07.7675', 
               'CFTuc'    : '00:53:07.7675', 
               'CF Tuc'   : '00:53:07.7675', 
               'AT_Mic'   : '20:41:51.15925', 
               'AT Mic'   : '20:41:51.15925', 
               'ATMic'    : '20:41:51.15925', 
               'AU_Mic'   : '20:45:09.53147', 
               'AUMic'    : '20:45:09.53147', 
               'AU Mic'   : '20:45:09.53147', 
               'UV_Cet'   : '01:39:05.81', 
               'UV Cet'   : '01:39:05.81', 
               'UVCet'    : '01:39:01.54', 
               'Flare from UV Cet'    : '01:39:01.54', 
               'UV Cet'   : '01:39:01.54', 
               'HD 8357'  : '01:22:56.7570',
               'HD_8357'  : '01:22:56.7570',
               'HD8357'   : '01:22:56.7570',
               'CC Eri'   : '02:34:22.5660',
               'CC_Eri'   : '02:34:22.5660',
               'CCEri'    : '02:34:22.5660',
               'GT Mus'   : '11:39:29.59368',
               'GT_Mus'   : '11:39:29.59368',
               'GTMus'    : '11:39:29.59368'}

    return ra_dict[name] 

def get_flare_DEC(name):
    dec_dict = {'Wolf424' :  '09:01:15.77', 
               'YZ_CMi'   :  '03:33:08.8350', 
               'YZCMi'    :  '03:33:08.8350', 
               'YZ CMi'   :  '03:33:08.8350', 
               'CN_Leo'   :  '07:00:52.77', 
               'CNLeo'    :  '07:00:52.77', 
               'CN Leo'   :  '07:00:52.77', 
               'V1054Oph' :  '-08:20:10.7876', 
               'V645Cen'  :  '-62:40:46.1631', 
               'ROSS1280' :  '00:48:16.395', 
               'DM-216267':  '-20:37:16.081', 
               'V1216Sgr' :  '-23:50:10.4291', 
               'HR_1099'  :  '00:35:15.9327', 
               'HR1099'   :  '00:35:15.9327', 
               'HR 1099'  :  '00:35:15.9327', 
               'CF_Tuc'   :  '-74:39:05.609', 
               'CFTuc'    :  '-74:39:05.609', 
               'CF Tuc'   :  '-74:39:05.609', 
               'AT_Mic'   :  '-32:26:06.8283', 
               'ATMic'    :  '-32:26:06.8283', 
               'AT Mic'   :  '-32:26:06.8283', 
               'AU_Mic'   :  '-31:20:27.2425', 
               'AU Mic'   :  '-31:20:27.2425', 
               'AUMic'    :  '-31:20:27.2425', 
               'UV_Cet'   :  '-17:56:50.02', 
               'UVCet'    :  '-17:56:50.02', 
               'Flare from UV Cet'    :  '-17:57:00.4', 
               'UV Cet'   :  '-17:57:00.4', 
               'HD 8357'  :  '07:25:09.336',
               'HD_8357'  :  '07:25:09.336',
               'HD8357'   :  '07:25:09.336',
               'CC Eri'   :  '-43:47:46.867',
               'CC_Eri'   :  '-43:47:46.867',
               'CCEri'    :  '-43:47:46.867',
               'GT Mus'   : '-65 23 51.9586',
               'GT_Mus'   : '-65 23 51.9586',
               'GTMus'    : '-65 23 51.9586'}

    return dec_dict[name] 

def handle_flare_star(v):
    n = Notifier()
    ivorn = v.attrib['ivorn']
    name_not_used, tel = get_name(v)
    name = get_flare_name(v)
    if tel == "SWIFT":
       TrigID   = v.find(".//Param[@name='TrigID']").attrib['value']
       web_link = 'https://gcn.gsfc.nasa.gov/other/'+TrigID+'.swift'
    if tel == "MAXI":
       TrigID   = v.find(".//Param[@name='TrigID']").attrib['value']
       web_link = 'https://gcn.gsfc.nasa.gov/other/8'+TrigID+'.maxi'
       #web_link = 'http://gcn.gsfc.nasa.gov/maxi.html'
    coords = voeventparse.pull_astro_coords(v)
    c = voeventparse.get_event_position(v)
    sub = vp.prettystr(v.What.Description)
    if "The sub-sub-threshold Swift-BAT trigger position notice" in sub:
       send_mail("Flare Star "+name+" sub-sub threshold trigger", "Not triggering")
       n.send_notification(title="Flare Star "+name+" sub-sub threshold burst ", text = "Coords are {}".format(coords))
    else:
        ra =  get_flare_RA(name)
        dec = get_flare_DEC(name)
        n.send_notification(title="Flare Star "+name+" Detected >> TRIGGERING!", text = "Coords are {}".format(coords))
        os.system('python schedule_atca.py '+str(ra)+' '+str(dec)+' '+web_link+' '+tel)

if __name__ == '__main__':
    sys.exit(main())
