import numpy as np
import time
import tkinter
from customtkinter import *
from czifile import CziFile
from matplotlib import pyplot as plt
import concurrent.futures
import czifile
from PIL import Image, TiffImagePlugin, ImageEnhance, ImageTk
import pytesseract as tess
tess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
import cv2 as cv
import sys
import os
from tifffile import TiffFile


class HelperFrame(CTkFrame):
    def __init__(self, master, progress_bar, *args, **kwargs):
        CTkFrame.__init__(self, master=master, *args, **kwargs)

        # GUI Stuff
        self.master = master
        self.PROGRESS_BAR = progress_bar

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=0)
        self.rowconfigure(4, weight=0)
        self.rowconfigure(5, weight=0)
        self.rowconfigure(6, weight=0)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)

        self.frame_info = CTkFrame(master=self)
        self.frame_info.grid(row=0, column=0, columnspan=2, rowspan=9, pady=20, padx=20, sticky="nsew")
        self.frame_info.grid_rowconfigure(0, weight=1)
        self.frame_info.grid_columnconfigure(0, weight=1)

        self.image_panel = CTkLabel(self.frame_info, image=None)
        self.image_panel.grid(row=0, column=0, pady=0, padx=0, sticky="nsew")
        self.img_index = 0
        self.open_image_btn = CTkButton(master=self, text="Open Image", command=self.open_image, height=42)
        self.open_image_btn.grid(row=0, column=2, pady=10, padx=20, sticky="we")

        # ============ frame_info ============
        # configure grid layout (1x1)
        self.frame_info.rowconfigure(0, weight=1)
        self.frame_info.columnconfigure(0, weight=1)

        self.button_5 = CTkButton(master=self, text="Quit", border_width=2, fg_color=None,
                                  command=lambda: print("Nothing"))
        self.button_5.grid(row=10, column=2, columnspan=1, pady=20, padx=20, sticky="we")

        # Setup folder for the Tiff files with labels
        self.tiff_dir = f"{os.getcwd()}\\TEMP\\tiffs_with_labels"
        if not os.path.exists(self.tiff_dir):
            os.makedirs(self.tiff_dir)
        self.active_files = {}
        self.viewed = {}
        self.files_to_preprocess = []

    def set_active_files(self, files_list):
        self.active_files = files_list

    def show_progress(self, done):
        self.PROGRESS_BAR.set(done)

    def set_image(self, img):
        self.master.update()
        current_size = (self.master.winfo_width(), self.master.winfo_height())
        img.thumbnail(current_size)
        img = img.resize(current_size, Image.ANTIALIAS)
        img = ImageTk.PhotoImage(img)
        self.image_panel = CTkLabel(self.frame_info, image=img)
        self.image_panel.grid(row=0, column=0, pady=5, padx=5, sticky="nsew")
        self.image_panel.image = img

    def log_activity(self, log_str):
        print("############# Log Message #############\n")
        print(f"At {time.strftime(format='%H:%M')}: {log_str}")
        print("#######################################\n")

    def quit_app(self):
        self.master.master.destroy()

