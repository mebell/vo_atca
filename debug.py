import cabb_scheduler as cabb
import atca_rapid_response_api as arrApi


schedule = cabb.schedule()

ra  = '01:19:46.63'
dec = '-30:20:15.36'

scan1 = schedule.addScan(
            { 'source': "SHORT_GRB", 'rightAscension': ra, 'declination': dec,
              'freq1': 5500, 'freq2': 9000, 'project': "C3204", 'scanLength': "00:20:00", 'scanType': "Dwell" })

schedule.disablePriorCalibration()

calList = scan1.findCalibrator()
