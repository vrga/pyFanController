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

import socket

debug = False

def logMe(*value):
    if debug:
        print(value)

"""
    Class to access hddtemp data, through the daemon hddtemp uses.
    Requires that you actually run the hddtemp daemon 
    on the localhost with the default port.
"""
class hddtemp(object):
    def __init__(self):
        self.port = 7634
        self.host = '127.0.0.1'
        self.availible = False
        """
            Basic test to determine availibility of the daemon.
            If not availible, log it.
        """
        try:
            self.s = socket.socket()
            self.s.connect((self.host, self.port))
            self.availible = True
            self.s.close()
        except:
            logMe('Failed opening socket to local hddtemp')
            #self.s.close()

    """
        Get and parse HDD temperatures.
        Works for whatever number of HDD's you might have.
        If the daemon itself returns proper data that is.
    """
    def getTemps(self):
        if self.availible:
            try:
                self.s = socket.socket()
                self.s.connect((self.host, self.port))
                data = self.s.recv(4096)
                self.s.close()
                temps = list()
                temperature = str(data, 'utf-8').split('||')
                logMe(temperature)
                for i in temperature:
                    if i[0] == '|':
                        i = i[1:]
                    logMe(i)
                    """
                        If reading fails, set temperature to 0.
                        This is handled in the device.py 
                        by simply applying the previous value.
                        TODO: check that it actually does this 
                              and not set to minimum fan speed...
                    """
                    try:
                        temps.append(float(i.split('|')[2]))
                    except:
                        temps.append(float(0))
                return temps
            except:
                logMe('Connection to hddtemp failed.')
        else:
            logMe('hddtemp daemon not availible. Is it running?')

"""
    This is used for debugging the soggy thing, 
    as its callable on its own.
    
    So, y'know, just to see if the daemon even works...
"""
t = hddtemp()
t.getTemps()
