# -*- coding:utf-8 -*-
from main import mainloop
from util import *
import cv2
import numpy as np
# import pyautogui
import keyboard
import threading
from time import perf_counter, sleep

class AutoRhythm:
    def __init__(self) -> None:
        self.cfg = load_cfg('./rhythm_config.json')
        
        self.chn = 2
        self.crop = self.cfg['crop']
        self.n_track = self.cfg['n_track']
        self.thre = self.cfg['thre']
        self.pkey = self.cfg['key']
        self.speed = self.cfg['speed']
        self.t_long = cv2.resize(cv2.imread('./img/t1.png')[..., self.chn], (20, 40))
        self.t_single = cv2.resize(cv2.imread('./img/t2.png')[..., self.chn], (20, 40))
        self.last = [None] * self.n_track
        self.down = [False] * self.n_track
        self.pred = [None] * self.n_track
        self.run = True
        self.new_cmd = threading.Event()
        self.shell_thre = threading.Thread(target=self._keyboard_send_loop)
        self.shell_thre.start()


    def _keyboard_send_loop(self):
        while self.run:
            # t1 = perf_counter()
            self.new_cmd.wait()
            # td = perf_counter() - t1
            last = [i for i in self.down]
            skip = 1
            for i in range(0, self.speed, skip):
                to_press = []
                to_release = []
                for k in range(self.n_track):
                    row = np.mean(self.pred[k][-i-skip-1:-i-1])
                    if row > 0:
                        if last[k] == False:
                            to_press.append(k)
                            self.down[k] = True
                    else:
                        if last[k]:
                            to_release.append(k)
                            self.down[k] = False
                    last[k] = row > 0
                    
                if len(to_press):
                    keyboard.press('+'.join([self.pkey[t] for t in to_press]))
                if len(to_release):
                    keyboard.release('+'.join([self.pkey[t] for t in to_release]))
            self.new_cmd.clear()  
            # print(f'Wait: {td:.5f}')
            
    
    def split_match(self, src):
        # longs = []
        # singles = []
        rs = cv2.matchTemplate(src, self.t_single, cv2.TM_CCOEFF_NORMED)
        rl = cv2.matchTemplate(src, self.t_long, cv2.TM_CCOEFF_NORMED)
        
        w = rs.shape[1] // self.n_track
        longs = [np.max(rl[:, i * w: (i + 1) * w], axis=1) for i in range(self.n_track)]
        singles = [np.max(rs[:, i * w: (i + 1) * w], axis=1) for i in range(self.n_track)]
        # cv2.waitKey(1)
        return longs, singles
            
    
    def merge_single_long(self, long, single, idx):
        w = len(long)
        res = np.zeros(w, dtype=np.uint8)
        if self.last[idx] is not None:
            res[self.speed:] = self.last[idx][:-self.speed]
            res[:self.speed] = self.last[idx][0]
        # press
        start = self.speed * 3
        enable = long[start + 1] > self.thre
        for i in range(start, -1, -1):
            if long[i] > self.thre:
                enable = True
            else:
                if enable:
                    # falling edge
                    enable = False
                    res[i] = 255 - res[i + 1]
                    continue
            res[i] = res[i + 1]
        # self.down[idx] = res[w - self.speed] > 0
        self.last[idx] = res.copy()
        # single button
        res[single > self.thre] = 255
        return res
            
    
    def stop_loop(self):
        self.run = False
        self.new_cmd.set()
        self.shell_thre.join()
                    
    def proc(self, img):
        # print(img.shape)
        r_img = crop_image_by_pts(cv2.resize(img[..., self.chn],
                                             (self.cfg['match_width'], self.cfg['match_height'])
                                             ),
                                  self.crop)
        
        longs, singles =self.split_match(r_img)
        
        t = 0
        for l, s in zip(longs, singles):
            res = self.merge_single_long(l, s, t)
            self.pred[t] = res.copy()
            h = len(longs[0])
            w = 15
            hs = int(self.crop[1] * self.cfg['match_height']) + 40
            ws = 250
            wh = 141
            for i in range(3):
                img[hs: hs + h, ws + wh*t: ws + wh*t + w, i] = res.reshape(-1, 1).repeat(w, 1)
                img[hs: hs + h, ws + wh*t - w: ws + wh*t, i] = ((l > self.thre).astype(np.uint8)  * 255).reshape(-1, 1).repeat(w, 1)
            t += 1
            
        self.new_cmd.set()
        # return 'AutoRhythm is running'
        return ' '.join(['down' if i else 'up' for i in self.down])
        # return ','.join([f'{i:.2f}({j:.2f})' for i, j in zip(vloc_long, vmax_long)])
        # return ','.join([f'{np.max(i):.2f}({np.max(j):.2f})' for i, j in zip(longs, singles)])


if __name__ == '__main__':
    ar = AutoRhythm()
    mainloop('-Rhythm', callback=ar.proc)
    ar.stop_loop()
