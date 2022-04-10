#!/bin/bash

START_SLEEP_SECS=45
ERROR_SLEEP_SECS=15
MODULE_NAME="run.sh"

# shellcheck disable=SC2006
NOW_DATE=`date +"%Y-%m-%d %H:%M:%S.%3N"`;
echo "$NOW_DATE INFO $MODULE_NAME - Starting main.py. Sleeping for $START_SLEEP_SECS seconds to give system a chance to startup"
sleep $START_SLEEP_SECS

until /usr/bin/python3.8 /home/connesha/Documents/GitHub/home-energy-mgr-main/main.py /usr/share/hassio/homeassistant/www; do
    # shellcheck disable=SC2006
    NOW_DATE=`date +"%Y-%m-%d %H:%M:%S.%3N"`;
    echo "$NOW_DATE ERROR $MODULE_NAME - main.py crashed with exit code $?. Restarting in $ERROR_SLEEP_SECS seconds"
    sleep $ERROR_SLEEP_SECS
done
