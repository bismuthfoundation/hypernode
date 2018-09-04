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
except:
    pass



