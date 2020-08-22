#!/bin/bash
export DBUS_SYSTEM_BUS_ADDRESS=unix:path=/host/run/dbus/system_bus_socket

# Optional step - it takes couple of seconds (or longer) to establish a WiFi connection
# sometimes. In this case, following checks will fail and wifi-connect
# will be launched even if the device will be able to connect to a WiFi network.
# If this is your case, you can wait for a while and then check for the connection.
sleep 15

# Choose a condition for running WiFi Connect according to your use case:

# 1. Is there a default gateway?
# ip route | grep default

# 2. Is there Internet connectivity?
# nmcli -t g | grep full

# 3. Is there Internet connectivity via a google ping?
# wget --spider http://google.com 2>&1

# 4. Is there an active WiFi connection?
iwgetid -r

if [ $? -eq 0 ]; then
    printf 'Skipping WiFi Connect\n'
else
    printf 'Starting WiFi Connect\n'
    /usr/src/app/wifi-connect
fi

# Start your application here.
# Run the app once on container start

python /usr/app/smittestop.py

# Save out the current env to a file so cron job can use it
export -p > /usr/app/env.sh

# Add the job to the crontab using update_hour var, defaulting to 9 AM
#(echo "0 ${UPDATE_HOUR:-9} * * * /usr/app/run-update.sh") | crontab -

# Start the cron daemon as PID 1
#exec cron -f