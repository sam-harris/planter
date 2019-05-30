#!/bin/bash -

current_hour=$(date +"%H")
mode=auto
output_dir=/home/pi/camera
sleep_for=1800000 # for 30 min takes
width=1944    
height=2200  

mkdir -p $output_dir

# Between 8pm (20) and 7am use night exposure mode.
# However, the computer time is returning the hour 2 hours ahead,
# so just adjust by adding 2.

while true; do
  current_hour=$(date +"%H")
  if [[ "${current_hour#0}" -gt 20 || "${current_hour#0}" -lt 7 ]]; then
    mode=night
  fi
  current_datetime=$(date +"%FT%H-%M-%S%Z")
  raspistill -e png -w "$width" -h "$height" -ex "$mode" --nopreview -o "$output_dir/${current_datetime}.png"
  sleep $sleep_for
done