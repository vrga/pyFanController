import socket
import logging

class hddtemp(object):
    """
    Class to access hddtemp data, through the daemon hddtemp uses.
    Requires that you actually run the hddtemp daemon
    on the localhost with the default port.
    """
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
            # logMe('Failed opening socket to local hddtemp')
            pass
            # self.s.close()

    def getTemps(self):
        """
        Get and parse HDD temperatures.
        Works for whatever number of HDD's you might have.
        If the daemon itself returns proper data that is.
        """
        if self.availible:
            try:
                self.s = socket.socket()
                self.s.connect((self.host, self.port))
                data = self.s.recv(4096)
                self.s.close()
                temps = list()
                temperature = str(data, 'utf-8').split('||')
                # logMe(temperature)
                for i in temperature:
                    if i[0] == '|':
                        i = i[1:]
                    # logMe(i)
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
                # logMe('Connection to hddtemp failed.')
                pass
        else:
            # logMe('hddtemp daemon not availible. Is it running?')
            pass

"""
    This is used for debugging the soggy thing, 
    as its callable on its own.
    
    So, y'know, just to see if the daemon even works...
"""
t = hddtemp()
t.getTemps()
