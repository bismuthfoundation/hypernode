# HN sentinel

This python script will make sure your Hypernode is running and not stuck.  
It will restart it should it die.

The recommended sentinel is the crontab sentinel, found in `crontab` directory.  

This autonomous sentinel is dedicated toward the linux installs where python 3.6 is **not** the default python.  
For these linuxes, since cronjobs do not run with full user environment, the cron sentinel can't work.

## Pre-requisites

- Running node
- HN installed
- hn_check.py run once
- hn_instance.py run once, was ok, stopped
- all hypernode screens closed, the cron will handle them.

- If your python setup is non standard, but then you know, you have to edit the "python3" invocation command within sentinel.py script.

## What does that do?

sentinel.py runs in a screen of its own. It will restart missing HN.
It spends most of the time sleeping, so won't add any load.

## Install

Make sure in which dir you are.  
Default install is `~/hypernode` so the crontab dir is `~/hypernode/sentinel` but your real, full directory should contain your username.  
Once in hypernode dir, type `pwd`.  
You should have something like `/root/hypernode` or `/home/your_user_name/hypernode`.  
This is your hypernode dir. Append /sentinel and you got your sentinel dir. Still with me?

For instance, mine could be `/home/eggdrasyl/hypernode/sentinel`

To run the sentinel in its `sentinel` screen, just do

`screen -d -S sentinel -m bash -c "python3.7 sentinel.py"`  
(supposses you run the latest version,with python3.7)

> **note**: If you need to edit your python3 invocation in sentinel.py, then you may want to rename sentinel.py to something else, like my_sentinel.py, so it won't be override by updates.

## Test

This should launch your HN within the minute.  
`screen -ls`  lists all the running screens. You should have a "sentinel" screen.    
run it until you see "*hypernode*" in the list.  

Then, `screen -x hypernode` to attach to that screen.
  
Wait until it syncs.

Be harsh, Kill it by ctrl-c

You will auto exit the screen also.  
Run `screen -ls` again until you see it coming back to life.

You can enter the sentinel screen to see what it did with  
`screen -x sentinel`  
then `ctrl-a d` to detach and let it run in background.

Do not kill it or it won't restart anything!


## How to disable

If you want to stop your Hypernode for a reason (like an update), then you need to deactivate the sentinel first.

`screen -x sentinel`      
kill it:  
`ctrl-c`  

restart with `screen -d -S sentinel -m bash -c "python3.7 sentinel.py"` to activate again


## Changelog

- V 1.0 - Initial commit  
- V 1.1 - Update python3.7
