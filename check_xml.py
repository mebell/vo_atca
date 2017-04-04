import urllib2
import voeventparse as vp


with open('TEST_VO_EVENT_SHORT_GRB.XML') as f:
     v = vp.load(f)

TrigID = v.find(".//Param[@name='TrigID']").attrib['value']
url = 'https://gcn.gsfc.nasa.gov/notices_s/'+str(TrigID)+'/BA/'
webdata = urllib2.urlopen(url)
for lines in webdata.readlines():
    print lines
    l = lines.split()
    if len(l) > 0:
       if lines.split()[0] == 'T90':
          T90 = lines.split()[1]
       if lines.split()[0] == 'T50':
          T50 = lines.split()[1]

print T90, T50


