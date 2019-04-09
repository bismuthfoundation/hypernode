"""
Bismuth Hypernodes

Cron sentinel by @iyomisc
To be run every 5 minute.
"""

import os
import subprocess
import time

try:
    if os.path.getmtime("../main/logs/pos_app.log") < time.time() -120:
        print("Hypernode is frozen, stopping...")
        data = subprocess.getoutput("screen -S hypernode -X at '#' stuff $'\003'")
    if os.path.getmtime("../main/logs/pos_app.log") < time.time() -300:
        print("Hypernode is frozen, killing...")
        data = subprocess.getoutput("screen -list")
        i2 = data.find('.hypernode')
        i1 = data.find(chr(9),i2-10)
        if (i1>0) and (i2>i1):
            data = data[i1+1:i2]
            str = "kill -15 {}".format(data)
            subprocess.getoutput(str)        
except:
    pass
