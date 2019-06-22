#!/bin/bash -

SHUTDOWN=0
TRAPPED_SIGNAL=

function onexit() {
  echo >&2 "shutdowntest running"
  TRAPPED_SIGNAL=$1
  SHUTDOWN=1
}

for SIGNAL in SIGINT SIGTERM SIGHUP SIGPIPE SIGALRM SIGUSR1 SIGUSR2; do
  trap "onexit $SIGNAL" $SIGNAL
done

current_hour=$(date +"%H")
mode=auto
output_dir=/home/pi/camera
sleep_for=3600 # for 60 min takes
width=1800    
height=2200  

mkdir -p $output_dir

# Between 8pm (20) and 7am use night exposure mode.
# However, the computer time is returning the hour 2 hours ahead,
# so just adjust by adding 2.

while ((!SHUTDOWN)); do
  current_hour=$(date +"%H")
  if [[ "${current_hour#0}" -gt 7 && "${current_hour#0}" -lt 19 ]]; then
    # this runs 6am to 8pm
    current_datetime=$(date +"%FT%H-%M-%S%Z")
    raspistill -e png -w "$width" -ex "$mode" --nopreview -o "$output_dir/${current_datetime}.png"
  fi
  sleep $sleep_for
done

echo >&2 "shutdowntest Finished shutting down"