# -*- coding:utf-8 -*-
from main import mainloop
from util import *
import cv2
import numpy as np
# import pyautogui
import keyboard
import threading


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
        self.canvas = np.zeros((720, self.n_track * self.viz_w * 3), dtype=np.uint8)
        self.down = [False] * self.n_track
        self.dist = np.array([1] * self.n_track)
        self.diff = np.array([1] * self.n_track)
        
        self.run = True
        self.new_cmd = threading.Event()
        self.shell_thre = threading.Thread(target=self._keyboard_send_loop)
        self.shell_thre.start()
        
        
    def _keyboard_send_loop(self):
        while self.run:
            self.new_cmd.wait()
            t_down = []
            for i, j in enumerate(self.dist):
                if j < self.cfg['press_down']:
                    self.down[i] = self.diff[i] < 0
                    t_down.append(i)
            
            # pyautogui.keyDown(self.pkey[i])
            if len(t_down):
                keyboard.press('+'.join([self.pkey[i] for i in t_down]))
            # reset button
            t = '+'.join([self.pkey[i] for i in t_down if not self.down[i]])
            if len(t):
                keyboard.release(t)
            self.new_cmd.clear()  
            
    
    def stop_loop(self):
        self.run = False
        self.new_cmd.set()
        self.shell_thre.join()
        
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
                v_loc.append(1)
            else:
                p = np.argmax(r, axis=1)
                # from bottle to top
                for t in range(len(p) - 1, -1, -1):
                    if r[t, p[t]] > self.cfg['thre']:
                        v_loc.append(1 - t / len(p))
                        break
        return np.array(v_loc), v_max
                    
            
    def viz(self, long, single):
        # move one line down
        self.canvas[1:] = self.canvas[:-1]
        self.canvas[0, :self.n_track * self.viz_w] = np.repeat(long, self.viz_w) * 255
        self.canvas[0, self.n_track * self.viz_w: self.n_track * self.viz_w * 2] = np.repeat(single, self.viz_w) * 255
        self.canvas[0, self.n_track * self.viz_w * 2:] = np.repeat(single, self.viz_w) * 255
        
    def proc(self, img):
        # print(img.shape)
        r_img = crop_image_by_pts(cv2.resize(img[..., self.chn],
                                             (self.cfg['match_width'], self.cfg['match_height'])
                                             ),
                                  self.crop)
        
        
        vloc_long, vmax_long = self.get_vertical_loc(r_img, self.t_long)
        vloc_single, vmax_single = self.get_vertical_loc(r_img, self.t_single)

        self.diff = vloc_long - vloc_single
        self.dist = np.minimum(vloc_long, vloc_single)
        self.new_cmd.set()
        
        self.viz(vloc_long, vloc_single)
        h = img.shape[0]
        for i in range(3):
            img[:, -self.canvas.shape[1]:, i] = self.canvas[:h]
        """
        t_down = []
        for i, j in enumerate(np.minimum(vloc_long, vloc_single)):
            if j < self.cfg['single_press']:
                # check single press or long press
                if d[i] > 0: # single press
                    pyautogui.keyDown(self.pkey[i])
                    t_down.append(i)
        # reset button
        for i in t_down:
            if i in self.down:
                continue
            pyautogui.keyUp(self.pkey[i])
        
        t_down = []
        # press the key
        for i, j in enumerate(vloc_single):
            if j < self.cfg['single_press']:
                pyautogui.keyDown(self.pkey[i])
                t_down.append(i)
        for i in t_down:
            if i in self.down:
                continue
            pyautogui.keyUp(self.pkey[i])
        
        
        # press the key
        for i, j in enumerate(vloc_long):
            if j < self.cfg['single_press']:
                if self.down[i]:
                    pyautogui.keyUp(self.pkey[i])
                else:
                    pyautogui.keyDown(self.pkey[i])
                self.down[i] = not self.down[i]
        """
        # return 'AutoRhythm is running'
        return ' '.join(['down' if i else 'up' for i in self.down])
        return ','.join([f'{i:.2f}({j:.2f})' for i, j in zip(vloc_long, vmax_long)])


if __name__ == '__main__':
    ar = AutoRhythm()
    mainloop('-Rhythm', callback=ar.proc)
    ar.stop_loop()
