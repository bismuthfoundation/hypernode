"""
Bismuth Hypernodes

Cron sentinel by @iyomisc
To be run every minute.
"""
import subprocess

# Edit this if you are not using the standard invocation
PYTHON_EXECUTABLE='python3.7'

list_ = subprocess.getoutput("screen -ls")
try:
    if ".hypernode\t" not in list_:
        print("Restarting stopped Hypernode...")
        data = subprocess.getoutput('screen -d -S hypernode -m bash -c "cd ../main;{} hn_instance.py -v" -X quit'.format(PYTHON_EXECUTABLE))
        print("started")
except:
    pass
