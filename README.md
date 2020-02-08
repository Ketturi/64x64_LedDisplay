# 64x64 Led Display
Led information display using hub75 64x64 panel and Raspberry Pi Zero W to control it.
Scripts included polls and displays data from different sources.

# Hardware
Display is custom build using 64x64 P2.5 HUB75e display module. It is connected to raspberry pi using 
https://github.com/hzeller/rpi-rgb-led-matrix library, which includes information about hardware connections.
Display case includes DC/DC converter and temperature, pressure, and light sensors.

# Setup
/boot/config.txt and /boo/cmdline.txt for RPi are included as these have important performance optimizations enabled.
Following services are removed
```
sudo systemctl disable keyboard-setup.service
sudo systemctl disable apt-daily.service
sudo systemctl disable hciuart.service
sudo systemctl disable triggerhappy.service
sudo systemctl disable bluetooth.service
sudo systemctl disable getty@.service
sudo apt-get purge bluez -yes

sudo nano /etc/modprobe.d/raspi-blacklist.conf
    blacklist snd_bcm2835
```

Following python packets are needed:
```
sudo pip3 install adafruit-circuitpython-bmp280
sudo pip3 install adafruit-circuitpython-busdevice
sudo pip3 install adafruit-gpio
git clone https://github.com/THP-JOE/Python_SI1145
git clone https://github.com/hzeller/rpi-rgb-led-matrix
```

## userled.py
This is main display program. It handles all data sources and graphics.
