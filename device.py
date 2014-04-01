"""
The MIT License (MIT)

Copyright (c) 2014 Fran Viktor Pavelić <fv.pavelic@egzodus.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import configparser
from numpy import interp, mean

import pdb

debug = True

def logMe(*value):
    if debug:
        print(value)

"""
    Magical device class
    Needs some heavy refactoring.
"""
class Device(object):
    """
        Basic initialisation.
    """
    def __init__(self, configData, extras):
        self.extras = extras
        self.item = dict()
        self.item.update({'currentTemps': [30]})
        self.populateData(configData)
        self.enableOutputs()

    """
        Parse the config file provided data
        There is probably a better way to do this.
        I however havent figured it out yet.
    """
    def populateData(self, data):
        logMe(data)
        for item in data:
            if item == 'outputenabler':
                # if its a outputenabler, append the prefix path. determines which output devices should be enabled. (pwm<num>_enable stuff)
                self.item['outputenabler'] = data['maindevicepathprefix']+data['outputenabler']
            elif item == 'temps':
                # if its a temperature, split it, we need to interpret all the values inbetween later, depending on the fun stuff in ranges...
                self.item['temps'] = data['temps'].split(',')
            elif item == 'temperaturemonitor':
                # a list of temperature monitoring devices used for calculating the PWM speed for the current device. also, strip whitespace :D
                tmp = data['temperaturemonitor'].split(',')
                self.item['temperaturemonitor'] = [data['tempMonDevicePathPrefix']+x.strip() for x in tmp]
            elif item == 'inputtype':
                # temperature input type. hddtemp or componentTemp currently. TODO: set intelligent names. For once.
                self.inputType = data['inputtype']
            elif item == 'outputtype':
                # PWM output type, basically, my way of deciding if i output to lm-sensors or my serial board.
                self.outputType = data['outputtype']
            elif item == 'device':
                # if its a device, append the prefix path.
                if data['outputtype'] == 'fanPWM':
                    self.item['device'] = data['maindevicepathprefix']+data['device']
                else:
                    self.item['device'] = data['device']
            else:
                # otherwise interpret as is
                self.item[item] = data[item]
            """
                TODO: this whole thing needs a bit more of a brain than i originally had.
            """
            #logMe('inputtype: ', self.item['inputtype'])
        """
            Interpolate the speeds for given temperature ranges.
        """
        self.interpolateSpeeds(self.item['temps'])
        #logMe('inputtype: ', self.item['inputtype'])
        logMe(self.item)
        #logMe(self.item['currentTemps'])
        #logMe(self.device)

    """
        Spawn of satan below.
    """
    def interpolateSpeeds(self, temps):
        tmp = list()
        tmp2 = list()
        # split the output some more
        for temp in temps:
            tmp.append(temp.split('|'))

        # sort out proper ranges for min/max
        tmp[0] = [int(tmp[0][0]), int(self.item['minimumspeed'])]
        tmp[len(tmp)-1] = [int(tmp[len(tmp)-1][0]), int(self.item['maximumspeed'])]

        # cast to integer, we dont want no strings here WHY: sometimes it treated the stuff as strings. We dont need no stinkin strings here.
        for k, v in enumerate(tmp):
            for k2, v2 in enumerate(v):
                tmp[k][k2] = int(v2)

        """
            determine first and last temperature 
            and treat them as minimum and maximum of the ranges
            temp > max = maximum fan speed
            temp < min = minimum fan speed
        """
        first = tmp[0]
        last = tmp[len(tmp)-1]

        temperatures = list()
        """
            We bother with the 0-100°C range.
            Why? Because.
            Could probably be made more efficient by
            not going through the whole 0-100 range
            and just go between first and last.
        """
        for j in range(100):
            if j <= first[0]:
                temperatures.append(first[1])
            elif j >= last[0]:
                temperatures.append(last[1])
            else:
                temperatures.append(0)
                for a in tmp:
                    if j == a[0]:
                        temperatures[a[0]] = a[1]
        """
            This somehow determines whether to interpolate temps or not.
            TODO: Need to step through and record values to figure out what i did here.
        """
        for i, v in enumerate(temperatures):
            for index, a in enumerate(tmp):
                if v == 0:
                    if v == a[1]:
                        break
                    else:
                        temperatures[i] = int(interp(i, [i-1, a[0]], [temperatures[i-1], a[1]]))
                else:
                    break

        self.item['temps'] = temperatures

    """
        Output enabler.
        For lm-sensors based outputs. 
        If you ever dug through /sys/class/hwmon/hwmon<number>/device/
        reasons why should be familiar.
        Especially if you had a motherboard on which the cpu fan controller
        would not respond to pwm1 but instead to pwm1_auto_point1_pwm.
        You could call it the whole reason behind writing this and not using
        pwmconfig and fancontrol in the first place.
    """
    def enableOutputs(self):
        """
            Obviously, we need to do this only if the output type is fanPWM or lm-sensors
            TODO: probably give smarter names...
        """
        if self.outputType == 'fanPWM':
            try:
                with open(self.item['outputenabler'], 'r+') as Writer:
                    Writer.write('1')
            except:
                logMe('Failed enabling output:', self.item['outputenabler'])

    """
        Temperature reader.
    """
    def getTemps(self):
        #logMe('inputtype: ', self.item['inputtype'],self.inputType)
        #self.item = { currentTemps: list() }
        tmp = list()
        """
            Read temperatures from lm-sensors or hddtemp sources...
        """
        if self.inputType == 'componentTemp':
            for monitor in self.item['temperaturemonitor']:
                with open(monitor, 'r') as Reader:
                    Reader = Reader.read()
                    tmp.append(float(Reader[:-4]))
        elif self.inputType == 'hddtemp':
            dev = self.extras['hddtemp']
            tmp = dev.getTemps()
        
        """
            If reading results with a speed of 0, 
            act as if the temperature is the previous value...
        """
        if tmp[0] == 0:
            tmp = self.item['currentTemps']
        #pdb.set_trace()
        """
            Record the mean value of all temperatures monitored for this device/output.
        """
        self.item.update({'currentTemps':int(mean(tmp))})
        #logMe('currTemp: ',mean(tmp),'device: ',self.item['device'])
    """
        Temperature writer
    """
    def setTemps(self):
        #logMe('inputtype: ', self.inputType)
        #logMe('outputType: ', self.outputType)
        """
            This is ugly, but eh, cant do much right now, due to the way i structured the data...
            Reads the current temperature from the temps dict, interpolates the desires value,
            casts to integer and then to string.
        """
        speed = str(int(interp(self.item['temps'][self.item['currentTemps']], [0, 100], [0, 255])))
        logMe('Writing speed: ', speed, 'For device:', self.item['device'], 'For temperature:', self.item['currentTemps'])
        """
            If output is to lm-sensors, just write to the file. We arent using any wrappers here.
            If its for the serial board, get the device number and speed, conver them to bytes,
            pretending UTF-8 is relevant here and finally, write to the serial device.
        """
        if self.outputType == 'fanPWM':
            try:
                with open(self.item['device'], 'w') as pwmWriter:
                    try:
                        pwmWriter.write(speed)
                    except:
                        logMe("Writing PWM value failed")
            except:
                logMe('Failed opening file for writing', self.item['device'])
        elif self.outputType == 'serial':
            ser = self.extras['serial']
            if ser.serialAvailible:
                #logMe('Serial written to:', self.item['device'], 'speed: ', speed)
                ser.write(bytes(self.item['device']+'/'+speed+'/', 'utf-8'))