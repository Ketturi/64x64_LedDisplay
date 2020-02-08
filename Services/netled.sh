#!/bin/bash
set -e
exec /home/pi/LedMatrix/ipview.sh | /usr/bin/text-example --led-rows=64 --led-cols=64 -f /home/pi/rpi-rgb-led-matrix-master/fonts/4x6.bdf --led-brightness=20 -C 255,200,0


