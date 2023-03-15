# -*- coding:utf-8 -*-
from main import mainloop
from util import *
import cv2
import numpy as np
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
        
        self.chn = 2
        self.crop = self.cfg['crop']
        self.n_track = self.cfg['n_track']
        self.pkey = self.cfg['key']
        self.t_long = cv2.imread('./img/t1.png')[..., self.chn]
        self.t_single = cv2.imread('./img/t2.png')[..., self.chn]
        self.viz_w = 15
        self.canvas = np.zeros((500, self.n_track * self.viz_w * 2), dtype=np.uint8)
        self.down = [False] * self.n_track
        
    def get_vertical_loc(self, img, template):
        res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        w = res.shape[1] // self.n_track
        
        v_loc = []
        v_max = []
        for i in range(self.n_track):
            r = res[:, w * i: w*(i + 1)]
            m = np.max(r)
            v_max.append(m)
            if m < self.cfg['thre']:
                v_loc.append(0.5)
            else:
                p = np.argmax(r, axis=1)
                # find the max value of each row
                max_val_row = np.array([value[j] for j, value in zip(p, r)])
                m_row = np.argmax(max_val_row)
                v_loc.append(1 - m_row / len(p))
        return np.array(v_loc), v_max
                    
            
    def viz(self, long, single):
        # move one line down
        self.canvas[1:] = self.canvas[:-1]
        self.canvas[0, :self.n_track * self.viz_w] = np.repeat(long, self.viz_w) * 255
        self.canvas[0, self.n_track * self.viz_w:] = np.repeat(single, self.viz_w) * 255
        
    def proc(self, img):
        # print(img.shape)
        r_img = crop_image_by_pts(cv2.resize(img[..., self.chn],
                                             (self.cfg['match_width'], self.cfg['match_height'])
                                             ),
                                  self.crop)
        
        
        vloc_long, vmax_long = self.get_vertical_loc(r_img, self.t_long)
        vloc_single, vmax_single = self.get_vertical_loc(r_img, self.t_single)
        
        self.viz(vloc_long, vloc_single)
        cv2.imshow('Test', self.canvas)
        cv2.waitKey(1)
        
        # press the key
        for i, j in enumerate(vloc_single):
            if j < self.cfg['single_press']:
                pyautogui.press(self.pkey[i])
        
        # press the key
        for i, j in enumerate(vloc_long):
            if j < self.cfg['single_press']:
                if self.down[i]:
                    pyautogui.keyUp(self.pkey[i])
                else:
                    pyautogui.keyDown(self.pkey[i])
                self.down[i] = not self.down[i]
        
        return 'L: ' + ','.join([f'{i:.2f}' for i in vmax_long]) + ' S: ' + ','.join([f'{i:.2f}' for i in vmax_single])


if __name__ == '__main__':
    ar = AutoRhythm()
    mainloop('-Rhythm', callback=ar.proc)
