# -*- coding:utf-8 -*-
import mss
from util import *
from tkinter import *
import tkinter.font as tkFont
from PIL import Image, ImageDraw, ImageFont, ImageTk
import numpy as np
import cv2
from datetime import datetime


def mainloop(title='', callback=None):
    print("操作说明:\nW:保存当前截图\nR:重新检测窗口位置\nQ:退出\n" + '-'*8)
    
    cfg = load_cfg()
    # Windows
    root = Tk()
    # Create a frame
    app = Frame(root)
    app.pack()

    # Create a label in the frame
    lmain = Label(app)
    lmain.pack()
    ldtag1 = Label(app, font=tkFont.Font(size=15, weight=tkFont.BOLD))
    ldtag1.pack()
    
    root.title('AutoGenshin' + title)
    # root.geometry('1300x760')
    target_name = cfg['name']
    scale = cfg['scale']

    save_img = False
    img_cache = None
    win_info = None
    
    def onKeyPress(event):
        nonlocal save_img
        nonlocal win_info
        if event.keysym in 'qQ':
            root.quit()
        elif event.keysym in 'wW':
            save_img = True
        elif event.keysym in 'rR':
            win_info = None

    def get_stick(des, win):
        words = des.split(',')
        value = 0
        for w in words:
            if w in ['top', 'left', 'width', 'height']:
                value += win[w]
            else:
                value += int(w)
        return value

    root.bind('<KeyPress>', onKeyPress)
    
    # display_interval = int(1000 / cfg['display_fps'])
    display_interval = 5
    with mss.mss() as m:
        def capture_stream():
            nonlocal save_img
            nonlocal img_cache
            nonlocal win_info
            if win_info is None or cfg['always_update_window']:
                win_info = get_window_roi(target_name, [0, 0, 1, 1], cfg['padding'])
            if win_info['left'] < 0 and win_info['top'] < 0:
                ldtag1.configure(text='未检测到窗口')
                img_cache = None
            else:
                full_win = get_window_roi(target_name,[0, 0, 1, 1], [0, 0, 0, 0])
                if len(cfg['stick']) == 2:
                    root.geometry(f"+{get_stick(cfg['stick'][0], full_win)}+{get_stick(cfg['stick'][1], full_win)}")
                img = np.array(m.grab(win_info))    
                img_c = img[:, :, :3].copy()
                
                if callback is not None:
                    text = callback(img)
                    if text is not None:
                        ldtag1.configure(text=text)
                    
                pil_img = Image.fromarray(img[:, :, :3][:, :, ::-1])
                if scale > 0:
                    pil_img = pil_img.resize((int(pil_img.size[0] * scale), int(pil_img.size[1] * scale)))
                    imgtk = ImageTk.PhotoImage(image=pil_img)
                    lmain.imgtk = imgtk
                    lmain.configure(image=imgtk)
                        
                if save_img:
                    p = f'{datetime.now():%Y-%m-%d_%H-%M-%S}.png'
                    if cv2.imwrite(p, img_c):
                        print('Save to ', p)
                    save_img = False
                
                    
                # update the display
                imgtk = ImageTk.PhotoImage(image=pil_img)
                lmain.imgtk = imgtk
                lmain.configure(image=imgtk)
            lmain.after(display_interval, capture_stream) 

        capture_stream()
        root.mainloop()

if __name__ == '__main__':
    mainloop()
