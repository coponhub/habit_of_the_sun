
__author__ = 'Aoyagi Knesuke'

import os
import atexit
import itertools
import math
import time
import pigpio

def frange(start, stop, step):
    return itertools.takewhile(lambda x: x< stop, itertools.count(start, step))

def flatten(listOfLists):
    "Flatten one level of nesting"
    return itertools.chain.from_iterable(listOfLists)

def flatrepeat(iterator,n):
    return flatten(itertools.repeat(iterator,n))


MAX_PWM_DUTY = 1000000
interval = 0.001
step = 0.0001
PORT = 18
FREQ = 2000
GRAD = 1
MAX_LUM=1000000
MIN_LUM=92000

def pos(x):
    return max(0,x)
def around(x):
    return abs(round(x))
def sine(rad):
    return min(MAX_LUM, around((math.cos(rad/GRAD) + 1.203) * (1/1.1) * MAX_PWM_DUTY) // 2)

def rescale(value):
    return pos(100 - math.log(value - MIN_LUM + 1, 1.12))
def lazy(value):
    time.sleep(interval * rescale(value))

pi = pigpio.pi()
atexit.register(pi.stop)

def change_lum(lightness):
    pi.hardware_PWM(PORT, FREQ, lightness)

atexit.register(change_lum, 0)

curve = (sine(x) for x in frange(-math.pi*GRAD, math.pi*GRAD, step))
#curve3 = flatrepeat(curve,3)
curveE = itertools.cycle(curve)

for i,v in enumerate(curveE):
    if i % 200 == 0:
        t = time.strftime("%H:%M:%S", time.localtime())
        print(v, t)
    lazy(v)
    change_lum(v)

