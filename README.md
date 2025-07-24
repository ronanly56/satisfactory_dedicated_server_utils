# satisfactory_dedicated_server_utils

## Restart the server every 3h 

The file main.py is a script designed to schedule a restart on your Satisfactory Dedicated Server every 3h

### Prerequis
You need to have the admin password for your server (prompted on init inside the game)
Generate an API KEY for your server :
(https://satisfactory.wiki.gg/wiki/Dedicated_servers/HTTPS_API) See documentation section PasswordLogin

```curl
curl --location 'https://YOURSERVERPUBLICIP/api/v1' \
--header 'Authorization;' \
--header 'Content-Type: application/json' \
--data '{
    "function": "PasswordLogin",
    "data": {
        "MinimumPrivilegeLevel": "",
        "Password": "<<SUPERSECRETADMINPASSWORD>>"
    }
}'
```
In the response of this request, you will find a authentificationToken which you need to put in the api_key variable inside main.py.
Don't forget to also change the server_ip if needed (if you host the script on your machine you will need public ip) and the query port.

/!\ This is a script that works for me, yes it's a bit messy, yes it's not pure code, but i don't care /!\
You can fully reuse it and adapt it for your needs :) 

### How I set the script to run on my server
The script is running as root user for me but do as you want
```bash
# Copy the script to your server
scp main.py root@yourmachineip:/root/.

# Connect to the server
ssh root@yourmachineip

# Make it executable
chmod +x main.py

# Schedule it to launch every hour
crontab -e
# Then add at the end of the file
# CTRL+O + CTRL+X to exit
0 * * * * /usr/bin/python3.9 /root/main.py >> /root/restart_logs/FG-Restart.log 2>&1

# You can adjust the python path to your env, also the logs output
```

### Debug option
If you see errors in logs or the script doesn't work, you can toggle request debugging by setting the debug var inside the main loop (bottom of the file)
This will toggle debugging and provide you with (hopefully) usefull informations.

Exemple : 
```bash 
[2025-07-24 14:24:34] {'Content-Type': 'application/json', 'Authorization': 'Bearer XXXXX'}
[2025-07-24 14:24:34] responseSatuts=200, decoded_data={"data":{"health":"healthy","serverCustomData":""}}
[2025-07-24 14:24:34] {'Content-Type': 'application/json', 'Authorization': 'Bearer XXXXX'}
[2025-07-24 14:24:34] responseSatuts=200, decoded_data={"data":{"serverOptions":{"FG.DSAutoPause":"True","FG.DSAutoSaveOnDisconnect":"True","FG.AutosaveInterval":"300.0","FG.DisableSeasonalEvents":"False","FG.NetworkQuality":"1","FG.SendGameplayData":"True","FG.ServerRestartTimeSlot":"840.0"},"pendingServerOptions":{}}}
[2025-07-24 14:24:34] The restart time must be updated : old=840, new=1020
[2025-07-24 14:24:34] {'Content-Type': 'application/json', 'Authorization': 'Bearer XXXXX'}
[2025-07-24 14:24:34] responseSatuts=204, decoded_data=
[2025-07-24 14:24:36] {'Content-Type': 'application/json', 'Authorization': 'Bearer XXXXX'}
[2025-07-24 14:24:36] responseSatuts=200, decoded_data={"data":{"serverOptions":{"FG.DSAutoPause":"True","FG.DSAutoSaveOnDisconnect":"True","FG.AutosaveInterval":"300.0","FG.DisableSeasonalEvents":"False","FG.NetworkQuality":"1","FG.SendGameplayData":"True","FG.ServerRestartTimeSlot":"1020.0"},"pendingServerOptions":{}}}
[2025-07-24 14:24:36] Successfully set next restart to 17:00:00
[2025-07-24 14:24:36] is_response_204=True, restart_minutes_check=1020, new_restart_minutes=1020
```