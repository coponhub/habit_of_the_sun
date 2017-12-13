
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
interval = 0.01
step = 0.001
PORT = 18
FREQ = 2000
GRAD = 3
TIME_GRAD = 1.01
MAX_LUM=1000000
MIN_LUM=130000
LIFTER_LUM_DIFF = 10000
MIN_LUM_LIFT=30000
MIN_LUM_CEIL = MIN_LUM + MIN_LUM_LIFT

def pos(x):
    return max(0,x)
def around(x):
    return abs(round(x))
def sine(rad):
    return (math.cos(rad) + 1)**GRAD / 2**GRAD
def wave(rad):
    return min(MAX_LUM, around(sine(rad) * (MAX_LUM - MIN_LUM) + MIN_LUM))

def rescale(value):
    return pos(1000 - math.log(value - MIN_LUM + 1, TIME_GRAD))
def lazy(value):
    time.sleep(interval * rescale(value))

pi = pigpio.pi()
atexit.register(pi.stop)

def change_lum(lightness):
    pi.hardware_PWM(PORT, FREQ, lightness)

atexit.register(change_lum, 0)

curve = (wave(x) for x in frange(-math.pi, math.pi, step))
#curve3 = flatrepeat(curve,3)
curveE = itertools.cycle(curve)

for i,v in enumerate(curveE):
    if i % 100 == 0:
        t = time.strftime("%H:%M:%S", time.localtime())
        print(v, t)
    #lazy(v)
    time.sleep(interval)
    change_lum(v)

