#!/bin/bash
#Show IP address on wlan0 interface
echo -e "WiFi SSID:"
sleep 0.5s
iwgetid -r
sleep 0.5s
echo -e " \nIP addrress:"
sleep 0.5s
#echo -e "test"
#sleep 0.5s
ifconfig wlan0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p'
ifconfig wlan0 | sed -En -e 's/.*netmask ([0-9.]+).*/\1/p'
echo "b8:27:eb:0d:cf:5c"
# | cut -d'.' -f-2 && printf "." 
#ifconfig wlan0 | sed -En -e 's/.*inet ([0-9.]+).*/\1/p' | cut -d'.' -f3-
sleep 0.5s
echo -e " \nHostname:"
sleep 0.5s
hostname
hostname -d
sleep 20s

