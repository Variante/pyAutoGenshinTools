# -*- coding:utf-8 -*-
from main import mainloop
from util import *
import pyautogui

"""
# Holds down the alt key
pyautogui.keyDown("alt")

# Presses the tab key once
pyautogui.press("tab")

# Lets go of the alt key
pyautogui.keyUp("alt")
"""

class AutoRhythm:
    def __init__(self) -> None:
        self.cfg = load_cfg('./rhythm_config.json')
        
    def proc(self, img):
        # print(img.shape)
        return 'AutoRhythm is working'


if __name__ == '__main__':
    ar = AutoRhythm()
    mainloop('-Rhythm', callback=ar.proc)
