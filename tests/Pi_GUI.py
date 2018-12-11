import numpy as np
from tkinter import *
import tkinter.font

def randNum():
    return np.random.rand()

# GUI
win = Tk()
win.title = 'mini_CPC'
myFont = tkinter.font.Font(
    family = 'Helvetica', 
    size = 12, 
    weight = 'bold')

# WIDGETS
button = Button(
    win, 
    text = 'click me!!!', 
    font  = myFont,
    command = randNum,
    bg = 'bisque2',
    height = 1,
    width = 24)

button.grid(row=0,column=1)