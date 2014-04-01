pyFanController
===============

A small-ish program to control fans on Linux through lm-sensors or whichever other sources you like.

There will be a lot more here soon enough.

This program was initially partially based upon Nicholas Polach's 
"NVIDIA Fan Controller V0.1 For Linux"
found currently at http://forums.evga.com/tm.aspx?m=903040
but no longer uses any code nor ideas from it.

Altough this program tries to be sane and not do stupid things to your
system, I can make no promises it wont set your machine on fire,
melt your harddrive, fry your cat or whatever other bodily harm you
can imagine.
Since, after all, it does control the fans for your machine...

With that out of the way, I am releasing this under the MIT license.

Also, it needs a LOT of polish yet.
It is partially my way of learning to code in python and
actually familiarizing myself with principles of OOP.

Provided initscript is only gentoo/funtoo compatible at the moment,
depending on python 3.3 and numpy.
You can provide whatever sources and sinks you wish through the config file.
Currently in use by me personally: lm-sensors, hddtemp, serial.

if you will use the serial one, please check out serialFC.py to see if you can work with the data it spits out.
pyserial will also be most likely required.

currently its of the form of 1/255/ aka <fan controller number>/<fan speed>/