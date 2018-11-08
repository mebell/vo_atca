import os
import glob

for file in glob.glob('achieve/*'):
    print file
    os.system('cat '+file+' | python process_voevent.py') 
