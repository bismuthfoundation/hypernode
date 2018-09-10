# Cron sentinel

These python scripts will make sure your Hypernode is running and not stuck.  
They will restart it should it die.

This guide may seem long, but it's just because I tried to think of everything for newbies.

## Pre-requisites

- Running node
- HN installed
- hn_check.py run once
- hn_instance.py run once, was ok, stopped
- all hypernode screens closed, the cron will handle them.

- If your python setup is non standard, but then you know, you may have to edit the "python3" invocation command within cron1.py script.

## What does that do?

cron1 is to be run every minute. It will restart missing HN.

cron5 is to be run, guess what, every 5 mins. It will kill a stuck HN.  
This HN will then be restarted by the cron1 a minute after.

Those as pretty "large" times, but it's ok. Round time is one hour. Slot time is 3 minutes.  
In regard, one minute is cool. 

## Install

Make sure in which dir you are.  
Default install is `~/hypernode` so the crontab dir is `~/hypernode/crontab` but your real, full directory should contain your username.  
Once in hypernode dir, type `pwd`.  
You should have something like `/root/hypernode` or `/home/your_user_name/hypernode`.  
This is your hypernode dir. Append /crontab and you got your crontab dir. Still with me?

For instance, mine could be `/home/eggdrasyl/hypernode/crontab`

Now install the cron: (choose nano if you're asked to)  
`crontab -e`  

paste these 2 lines:

```
* * * * * cd /your/crontab/dir;python3 cron1.py
*/5 * * * * cd /your/crontab/dir;python3 cron5.py
```

Or course, replace `/your/crontab/dir` by your real, custom, crontab dir above.    
If your invocation of python is not `python3`, edit also.

Exit and save (Ctrl-x , Y, enter)

## Test

This should launch your HN within the minute.  
`screen -ls`  lists all the running screens.  run it until you see "*hypernode*" in the list.  
Then, `screen -x hypernode` to attach to that screen.
  
Wait until it syncs.

Be harsh, Kill it by ctrl-c

You will auto exit the screen also.  
Run `screen -ls` again until you see it coming back to life.

Done :)

## How to disable

If you want to stop your Hypernode for a reason (like an update), then you need to deactivate the cron jobs first.

`crontab -e`  

comment out the 2 lines by adding a `#` character at the begin of each line, so it reads 

```
#* * * * * cd /your/crontab/dir;python3 cron1.py
#*/5 * * * * cd /your/crontab/dir;python3 cron5.py
```

Exit and save (Ctrl-x , Y, enter)

Redo and remove the `#` to activate again

## Changelog

V 1.1 - Fixed cron entry error
V 1.0 - Initial commit
