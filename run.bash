#!/bin/bash
pigpiod && 
sleep 1 && 
cd /home/aki/projects/habit_of_the_sun &&
python3 /home/aki/projects/habit_of_the_sun/main.py
