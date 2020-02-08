#!/usr/bin/env python
# Display data with double-buffering.
#System
import ctypes,sys
import threading
import atexit

#Led matrix
from samplebase import SampleBase
from rgbmatrix import graphics
from PIL import Image

#Sensors
import SI1145.SI1145 as SI1145
import time
import board
import busio
import adafruit_bmp280

#Time
from datetime import datetime, timezone
from dateutil import parser as DUp
import time

#Math
import numpy
import math

#GPModules
from utils import *
from handlers import *

#Clock
from math import sin, cos, radians

#Timetable
from fmi import FMI

#Radiation

#Warnings


#This is hack to get thread names to show up in linux process monitor
LIB = 'libcap.so.2'
try:
    libcap = ctypes.CDLL(LIB)
except OSError:
    print(
        'Library {} not found. Unable to set thread name.'.format(LIB)
    )
else:
    def _name_hack(self):
        # PR_SET_NAME = 15
        libcap.prctl(15, self.name.encode())
        threading.Thread._bootstrap_original(self)

    threading.Thread._bootstrap_original = threading.Thread._bootstrap
    threading.Thread._bootstrap = _name_hack

#Setup light, temperature and pressure sensor libraries
try:
    sensor = SI1145.SI1145()
    i2c = busio.I2C(board.SCL, board.SDA)
    bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c,0x76)
    bmp280.sea_level_pressure = 1013.25
    bmp280.mode = adafruit_bmp280.MODE_FORCE
    bmp280.standby_period = adafruit_bmp280.STANDBY_TC_500
    bmp280.iir_filter = adafruit_bmp280.IIR_FILTER_DISABLE
    bmp280.overscan_pressure = adafruit_bmp280.OVERSCAN_X1
    bmp280.overscan_temperature = adafruit_bmp280.OVERSCAN_X1
except:
    sensor = None
    print("I2C bus error")

fontpath = "/home/pi/rpi-rgb-led-matrix-master/fonts/"    
    
#Set columns for bus timetable
column1 = 0
column2 = 24
column3 = 40

#Monitored bus stop
busstop = "5005"
stopname = "TKL"

#global brightness variables
bright = 10
max_light = 100

#global outside temperature variable
city = 'Tampere'
OutsideTemp = None

currentScreen = 0

class LedDisplay(SampleBase):
    def __init__(self, *args, **kwargs):
        super(LedDisplay, self).__init__(*args, **kwargs)
    
    def centerPoint(self):
        #Use the midpoint formula to get the center of of the clock
        #instead of guessing at the middle of the circle
        corner1 = point(0, 0)
        corner2 = point(63, 63)
        x = (corner1.x + corner2.x)/2
        y = (corner1.y + corner2.y)/2
        return point(x, y)
        
    def adapt(self):
        #Read light sensor, average readings and set global led brightness
        while True:
            try:
                global bright
                self.matrix.brightness = bright
                #Place sensor readings into array
                sum_reads=[0]*10
                for i in range(0, 10):
                    sum_reads[i] = sensor.readVisible()
                    time.sleep(1)
                #Calculate mean from sensor readings
                light = numpy.mean(sum_reads)
                
                #Limit 16bit sensor value to more usable range and convert into percent:
                #NewValue = (((OldValue - OldMin) * (NewMax - NewMin)) / (OldMax - OldMin)) + NewMin
                bright = round((((light - 255) * (100 - 5)) / (500 - 255)) + 5)
                if bright > max_light:
                    bright = max_light
                #print(bright)
            except:
                bright = 50
        
    def update(self, lock, function ,interval):
        while True:
            with lock:
                function()
            time.sleep(interval*60)
            
    def weather(self):
        #Get current outside temperature from FMI
        # !!! To-Do: find better weather function, this is heavy and slow !!!
        #            -Will be replased with json api parser soon
        f = FMI('totally_leggit_apikey', place=city)
        while True:
            try:
                #Convert latest weather observation to current outside temperature
                weather = f.observations()
                temp = str(weather[-1])
                temperature = temp.split(' - ')[1].replace(' C>', '')
                global OutsideTemp
                OutsideTemp = float(temperature)
                #print(OutsideTemp)
                time.sleep(600)
            except:
                OutsideTemp = None
	
    def display(self, lock):
        #Create canvas for drawing user data
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        
        #Load fonts       
        fontRadiation       = graphics.Font()
        fontRadiationUnit   = graphics.Font()
        fontMessage         = graphics.Font()
        fontClockTime       = graphics.Font()
        fontClockDate       = graphics.Font()
        fontTimetable       = graphics.Font()
        
        fontRadiation.LoadFont(fontpath +       "profont17.bdf")
        fontRadiationUnit.LoadFont(fontpath +   "6x10.bdf")
        fontMessage.LoadFont(fontpath +         "6x9.bdf")
        fontClockTime.LoadFont(fontpath +       "6x13B.bdf")
        fontClockDate.LoadFont(fontpath +       "6x13.bdf")
        fontTimetable.LoadFont(fontpath +       "5x8.bdf")

        fontSmall = graphics.Font()
        fontTiny = graphics.Font()
        
        fontSmall.LoadFont(fontpath + "4x6.bdf")
        fontTiny.LoadFont(fontpath + "tom-thumb.bdf")

        #Set predefined colors
        textColor = graphics.Color(255, 200, 0)
        white = graphics.Color(255, 255, 255)
        gray = graphics.Color(128, 128, 128)
        green = graphics.Color(0, 255, 0)
        red =   graphics.Color(255, 0, 0)
        radcolor = graphics.Color(255, 255, 255)
        uvcolor = graphics.Color(255, 255, 255)
        
        graphics.DrawText(offscreen_canvas, fontSmall,  0, 6, white, "LED info screen")
        graphics.DrawLine(offscreen_canvas, 0, 7, 63, 7, gray)
        graphics.DrawText(offscreen_canvas, fontMessage, 0, 22    , textColor, "  Ketturi  ")
        graphics.DrawText(offscreen_canvas, fontMessage, 0, 22+  9, textColor, "Electronics")
        graphics.DrawText(offscreen_canvas, fontMessage, 0, 22+9*3, textColor, " RPi based ")
        graphics.DrawText(offscreen_canvas, fontMessage, 0, 22+9*4, textColor, "LED matrix ")
        offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)        
        time.sleep(2)
        
        radstr = "Wait"
        uvstr = "Wait"
        
        uvindexcolors = ["#BEBEBE","#4EB400", "#A0CE00", "#F7E400", "#F8B600", "#F88700", "#F85900", "#E82C0E", "#D8001D", "#FF0099", "#B54CFF", "#998CFF", "#8578EB", "#7164D7", "#5D50C3", "#493CAF", "#35289B", "#211487"]
        radcolors = ["#00FF90", "#00FF00", "#A7FF00", "#FFFF00", "#FF9000", "#FF0000"]

        BitmapPositions = [[], [(17,22)], [(3,22),(33, 22)], [(3,7),(33, 7),(17, 36)], [(3,7),(33, 7),(3, 36),(33, 36)]]
        BitmapWarning = ["", "", "", ""]
        BitmapSeveral = Image.open("bitmap/warnings/several.png")
        BitmapBorder = Image.open("bitmap/warnings/border.png")
        radiation_bitmap = Image.open("bitmap/radiation.png")
        uv_bitmap = Image.open("bitmap/uvradiation.png")

        while True:
           #current date and time
            now = datetime.now() 
            clock = now.strftime("%H:%M")
            date = now.strftime("%a %m")
                       
            def radScreen(*args, **kwargs):
                """
                    Show current radiation level from STUK measurement station
                """
                nonlocal offscreen_canvas, radcolor, uvcolor, radstr, uvstr
                offscreen_canvas.Clear()
                graphics.DrawText(offscreen_canvas, fontSmall, 45, 6, white, clock) # Draw current time       
                graphics.DrawText(offscreen_canvas, fontRadiationUnit, 35, 7+25, white, "µSv/h")
                graphics.DrawText(offscreen_canvas, fontRadiationUnit, 35, 36+25, white, "Index")
                graphics.DrawText(offscreen_canvas, fontRadiation, 18, 7+15, radcolor, radstr)
                graphics.DrawText(offscreen_canvas, fontRadiation, 18, 36+15, uvcolor, uvstr)            

                graphics.DrawLine(offscreen_canvas, 0, 7, 63, 7, gray)
                graphics.DrawLine(offscreen_canvas, 0, 36, 63, 36, gray)
                
                offscreen_canvas.SetImage(radiation_bitmap.convert("RGB"),0,13, False)
                offscreen_canvas.SetImage(uv_bitmap.convert("RGB"),0,37, False)
                
                for x in range(0, 6):
                    tempcolor = graphics.Color(*hex2rgb(radcolors[x]))
                    x = x*5
                    graphics.DrawLine(offscreen_canvas, x+35, 34, x+35, 35, tempcolor)
                    graphics.DrawLine(offscreen_canvas, x+36, 34, x+36, 35, tempcolor)
                    graphics.DrawLine(offscreen_canvas, x+37, 34, x+37, 35, tempcolor)
                    graphics.DrawLine(offscreen_canvas, x+38, 34, x+38, 35, tempcolor)
                    graphics.DrawLine(offscreen_canvas, x+39, 34, x+39, 35, tempcolor)
                
                for x in range(0, 17):
                    tempcolor = graphics.Color(*hex2rgb(uvindexcolors[x]))
                    x = x*2
                    graphics.DrawLine(offscreen_canvas, x+35, 62, x+35, 63, tempcolor)
                    graphics.DrawLine(offscreen_canvas, x+36, 62, x+36, 63, tempcolor)
                    
                if not lock.locked():
                    graphics.DrawText(offscreen_canvas, fontSmall, 0, 6, white, "RADIATION")
                else:
                    graphics.DrawText(offscreen_canvas, fontSmall, 0, 6, textColor, "UPDATING")
                    offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)       
                with lock:
                    try:
                        uvstr = str(uv.value)
                        uvcolor = hex2rgb(uvindexcolors[clamp(int(round(uv.value)),0, 17)])
                        uvcolor = graphics.Color(*uvcolor)
                    except:
                        uvcolor = graphics.Color(255, 255, 255)
                        
                with lock:
                    try:
                        radstr = str(radiation)
                        radcolor = hex2rgb(radcolors[clamp(int(math.floor(radiation.value*10)), 0, 5)])
                        radcolor = graphics.Color(*radcolor)
                    except:
                        radcolor = graphics.Color(255, 255, 255)              
                                            
            def clockScreen(*args, **kwargs):
                """
                    This is forked from https://github.com/yumaikas/pyAnalogClock tkinter clock by (yumaikas) Andrew Owen
                    Sorry dude if this is not open source, you had no license file
                    (awesome analog clock!)
                """
                offscreen_canvas.Clear()
                #Draw clock face numbers 
                graphics.DrawText(offscreen_canvas, fontSmall, 28, 6, textColor, "12")
                graphics.DrawText(offscreen_canvas, fontSmall, 63-4, 33, textColor, "3")
                graphics.DrawText(offscreen_canvas, fontSmall, 30, 62, textColor, "6")
                graphics.DrawText(offscreen_canvas, fontSmall, 2, 33, textColor, "9")
                
                def createTickMark(angle, dFromCenter):
                    angle -= 90.0
                    rads = math.radians(angle)
                    center = self.centerPoint()
                    p1 = center.offsetByVector(rads, dFromCenter)
                    offscreen_canvas.SetPixel(p1.x, p1.y, 255, 255, 255)
                    
                for angle in range(0, 360, 30):
                    createTickMark(angle, 32)
                    
                hourAngle = ((now.hour * 30.0) + (30.0 * (now.minute/60.0)))
                minuteAngle = ((now.minute * 6.0) + (6.0 * (now.second/60.0)))
                secondAngle = (now.second * 6)

                def drawHand(angle, length, color, line=True):
                    #Offset by 90.0 degrees so that we get 0 as the top of the clock,
                    #not 3 o'clock, like algebra normally does
                    angle -= 90.0
                    
                    rads = math.radians(angle)
                    center = self.centerPoint()
                    endPoint = center.offsetByVector(rads, length)
                    if line:
                        graphics.DrawLine(offscreen_canvas, center.x, center.y, endPoint.x, endPoint.y, color)
                    else:
                        graphics.DrawCircle(offscreen_canvas, endPoint.x, endPoint.y, 1, color)
                
                drawHand(secondAngle, 30, red, line=False)
                drawHand(minuteAngle, 26, gray)
                drawHand(hourAngle, 20, red)
                
                graphics.DrawText(offscreen_canvas, fontClockTime, 17, 28, textColor, clock) # Draw digital clock
                graphics.DrawText(offscreen_canvas, fontClockDate, 15, 31+12, textColor, date) # Draw date

            def nysseScreen(*args, **kwargs):
                """
                    Show bus timetable for selected stop
                """
                nonlocal offscreen_canvas
                offscreen_canvas.Clear()
                #draw general information
                graphics.DrawText(offscreen_canvas, fontSmall, 45, 6, white, clock) # Draw current time
                try:
                    try:
                        graphics.DrawText(offscreen_canvas, fontSmall, 1, 64, textColor, "{:02.0f}/{:02.0f}°C".format(OutsideTemp, bmp280.temperature)) #Draw outside/inside temperature
                    except:
                        graphics.DrawText(offscreen_canvas, fontSmall, 1, 64, textColor, "{:02.0f}°C".format(bmp280.temperature)) #Draw inside temperature
                    graphics.DrawText(offscreen_canvas, fontSmall, 36, 64, textColor, "%1.0fhPa"  % bmp280.pressure) #Draw atmospheric pressure
                except:
                    graphics.DrawText(offscreen_canvas, fontSmall, 1, 64, textColor, "Sensor error") #Error reading sensors
                    
                #draw top and bottom separator lines
                for x in range(0, self.matrix.width):
                    offscreen_canvas.SetPixel(x, 7, 128, 128, 128)
                    offscreen_canvas.SetPixel(x, 58, 128, 128, 128)
                
                data = timetable.value
         
                #Bus timetable display
                try:
                       #Loop trough timetable data
                       stopcount = len(data["body"][busstop])
                       if stopcount > 6:
                           stopcount = 6
                       for i in range(stopcount):
                           # Get bus number and draw it
                           line = data["body"][busstop][i]["lineRef"]
                           graphics.DrawText(offscreen_canvas, fontTimetable, column1, 22+(i*7), textColor, line)
                           try:
                               #Try to parse real time departure time and bus status
                               expectedDepartureTime = DUp.parse(data["body"][busstop][i]["call"]["expectedDepartureTime"])
                               departureStatus = data["body"][busstop][i]["call"]["arrivalStatus"]

                               #Calculate minutes to departure
                               TimeToArrival = expectedDepartureTime - datetime.now(timezone.utc)
                               MinutesToArrival = round(TimeToArrival.total_seconds()/60)

                               #Set color depending bus status
                               if departureStatus == "delayed":
                                   buscolor =  graphics.Color(255, 0, 0)
                               elif departureStatus == "early":
                                   buscolor =  graphics.Color(0, 255, 0)
                               else:
                                   buscolor =  graphics.Color(255, 200, 0)
                               
                               #Draw bus ETA
                               graphics.DrawText(offscreen_canvas, fontTimetable, column2, 22+(i*7), buscolor, str(MinutesToArrival))
                               graphics.DrawText(offscreen_canvas, fontTimetable, column3, 22+(i*7), textColor, expectedDepartureTime.strftime("%H:%M"))

                           except:
                                try:
                                    #Try to parse non-realtime arrival estimation if realtime not available
                                    eta=datetime.strftime(DUp.parse(data["body"][busstop][i]["call"]["aimedDepartureTime"]),"%H:%M")
                                except:
                                    #Could still fail
                                    eta = "NaN"
                                #Draw non-realtime eta
                                graphics.DrawText(offscreen_canvas, fontTimetable, column2, 22+(i*7), buscolor, str(eta))
                                
                       #Draw bus info legends         
                       graphics.DrawText(offscreen_canvas, fontSmall, column2, 14, white, "Min")
                       graphics.DrawText(offscreen_canvas, fontSmall, column1, 14, white, "Linja")
                       graphics.DrawText(offscreen_canvas, fontSmall, column3, 14, white, "ETA")

                       graphics.DrawText(offscreen_canvas, fontSmall,  0, 6, white, busstop)
                       graphics.DrawText(offscreen_canvas, fontSmall,  18, 6, white, stopname)
                except:
                    #If parsing bus timetable fails, show error
                    graphics.DrawText(offscreen_canvas, fontSmall, 0, 6, red, "ERROR")
                    graphics.DrawText(offscreen_canvas, fontTimetable, 0, 22, textColor, "Bus service")
                    graphics.DrawText(offscreen_canvas, fontTimetable, 0, 29, textColor, "unavailable")          

                if lock.locked():
                    graphics.DrawText(offscreen_canvas, fontSmall, 0, 6, textColor, "UPDATING")
                    offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)  
            
            def warningsScreen(*args, **kwargs):
                """
                    Show weather warnings
                """
                nonlocal offscreen_canvas
                offscreen_canvas.Clear()
                graphics.DrawText(offscreen_canvas, fontSmall, 45, 6, white, clock) # Draw current time
                graphics.DrawLine(offscreen_canvas, 0, 7, 63, 7, gray)
                
                if not lock.locked():
                    graphics.DrawText(offscreen_canvas, fontSmall, 0, 6, white, "W.WARNINGS")
                else:
                    graphics.DrawText(offscreen_canvas, fontSmall, 0, 6, textColor, "UPDATING")
                    offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)    
             
                with lock:
                    try:
                        if len(wwarn) == 0:
                            symbolcount = 0
                            graphics.DrawLine(offscreen_canvas, 0, 7, 63, 7, gray)
                            graphics.DrawText(offscreen_canvas, fontMessage, 0, 22    , textColor, "No weather")
                            graphics.DrawText(offscreen_canvas, fontMessage, 0, 22+  9, textColor, "warnings")
                            graphics.DrawText(offscreen_canvas, fontMessage, 0, 22+9*2, textColor, "currently")
                            graphics.DrawText(offscreen_canvas, fontMessage, 0, 22+9*3, textColor, "in effect")                    
                        elif len(wwarn) > 4:
                            offscreen_canvas.SetImage(BitmapSeveral.convert("RGB"), *BitmapPositions[3][3])
                            symbolcount = 3
                        else:
                            symbolcount = len(wwarn)
                        
                        for i in range(symbolcount):
                            BitmapWarning[i] = Image.open("bitmap/warnings/{}/{}.png".format(wwarn.severity(i),wwarn.warning_context(i)))
                            
                            BitmapWarning[i].paste(BitmapBorder, (0, 0), BitmapBorder)
                            offscreen_canvas.SetImage(BitmapWarning[i].convert("RGB"), *BitmapPositions[symbolcount][i], unsafe=False)
                    except:
                            graphics.DrawLine(offscreen_canvas, 0, 7, 63, 7, gray)
                            graphics.DrawText(offscreen_canvas, fontMessage, 0, 22    , red, "Error while")
                            graphics.DrawText(offscreen_canvas, fontMessage, 0, 22+  9, red, "loading")
                            graphics.DrawText(offscreen_canvas, fontMessage, 0, 22+9*2, red, "weather")
                            graphics.DrawText(offscreen_canvas, fontMessage, 0, 22+9*3, red, "warnings")

            global currentScreen
            screenSwitcher = {
                        0: clockScreen,
                        1: nysseScreen,
                        2: radScreen,
                        3: warningsScreen
                        }               
                            
            func = screenSwitcher.get(currentScreen, "nothing")
            func()
            
            #Swap backgound buffer to foreground buffer (double buffering)
            offscreen_canvas = self.matrix.SwapOnVSync(offscreen_canvas)
            
    def run(self):
            #Create threads
            radlock = threading.Lock()
            uvlock = threading.Lock()
            buslock = threading.Lock()
            warnlock = threading.Lock()
            lock = threading.Lock()
            
            displayThread = threading.Thread(target=self.display, daemon=True, name='DisplayLoop', args=(lock,))
            updateTimetableThread = threading.Thread(target=self.update, daemon=True, name='BusUpdater', args=(buslock, timetable.update, 1))
            updateRadiationThread = threading.Thread(target=self.update, daemon=True, name='RadUpdater', args=(radlock, radiation.update, 5))
            updateUVBThread = threading.Thread(target=self.update, daemon=True, name='UvUpdater', args=(uvlock, uv.update, 5))
            updateWarningsThread = threading.Thread(target=self.update, daemon=True, name='WarnUpdater', args=(warnlock, wwarn.update, 10))
            adaptiveThread = threading.Thread(target=self.adapt, daemon=True, name='AdaptiveBrightness') 
            weatherThread = threading.Thread(target=self.weather, daemon=True, name='WeatherUpdater')
        
            #Start threads
            adaptiveThread.start()
            displayThread.start()
            time.sleep(4)
            
            updateTimetableThread.start()
            updateRadiationThread.start()
            updateUVBThread.start()
            updateWarningsThread.start()
           
            weatherThread.start()
            
            global currentScreen
            while True:
                currentScreen = 0
                time.sleep(30)
                if timetable.is_valid():
                    currentScreen = 1
                    time.sleep(30)
                
                currentScreen = 0
                time.sleep(15)                 
                currentScreen = 2
                time.sleep(15)                 

                if wwarn.is_valid():
                    currentScreen = 0
                    time.sleep(15)                 
                    currentScreen = 3
                    time.sleep(15) 
              

# Main function
if __name__ == "__main__":
    #Create data handlers
    timetable = getNysse(busstop)
    radiation = getFMIradiation("tampere")
    uv = getFMI_UV_B("101339")
    wwarn = getFMIwarnings("county.6")
    
    #Run bus display process
    run_bus = LedDisplay()
    if (not run_bus.process()):
        run_bus.print_help()

