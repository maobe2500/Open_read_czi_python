import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter
from customtkinter import *
import os
import tifffile as tf
from czifile import CziFile
from matplotlib import pyplot as plt
from czifile import *
import cv2 as cv
from ..Primitives.HelperFrame import HelperFrame


class CZIViewerFrame(HelperFrame):
    def __init__(self, master, progress_bar, *args, **kwargs):
        HelperFrame.__init__(self, master, progress_bar, *args, **kwargs)
        self.test_label = None

        self.frame_info = CTkFrame(master=self)
        self.frame_info.grid(row=0, column=0, columnspan=2, rowspan=9, pady=20, padx=20, sticky="nsew")
        self.frame_info.grid_rowconfigure(0, weight=1)
        self.frame_info.grid_columnconfigure(0, weight=1)

        self.image_panel = CTkLabel(self.frame_info, image=None)
        self.image_panel.grid(row=0, column=0, pady=0, padx=0, sticky="nsew")
        self.img_index = 0
        # ============ frame_info ============

        # configure grid layout (1x1)
        self.frame_info.rowconfigure(0, weight=1)
        self.frame_info.columnconfigure(0, weight=1)

        # Radio buttons
        self.radio_var = tkinter.IntVar(value=0)
        self.label_radio_group = CTkLabel(master=self, text="Choose Channel")
         # Settings dropdown
        self.combobox_1 = CTkComboBox(master=self, values=["Value 1", "Value 2"])
        self.combobox_1.grid(row=3, column=2, columnspan=1, pady=10, padx=10, sticky="we")
         # Settings dropdown
        self.combobox_1 = CTkComboBox(master=self, values=["Value 1", "Value 2"])
        self.combobox_1.grid(row=4, column=2, columnspan=1, pady=10, padx=10, sticky="we")
         # Settings dropdown
        self.combobox_1 = CTkComboBox(master=self, values=["Value 1", "Value 2"])
        self.combobox_1.grid(row=5, column=2, columnspan=1, pady=10, padx=10, sticky="we")


        # Sliders
        #self.slider_1 = CTkSlider(master=self, from_=0, to=1, number_of_steps=3, command=self.PROGRESS_BAR.set)
        #self.slider_1.grid(row=4, column=0, columnspan=2, pady=10, padx=20, sticky="we")
        #self.slider_2 = CTkSlider(master=self, command=self.progressbar.set)
        #self.slider_2.grid(row=5, column=0, columnspan=2, pady=10, padx=20, sticky="we")

        # Switches
        self.make_save_folder = BooleanVar(value=True)
        self.create_new_dir = CTkSwitch(master=self, text="New folder?",
                                        variable=self.make_save_folder, onvalue=True, offvalue=False)
        self.create_new_dir.grid(row=6, column=2, columnspan=1, pady=10, padx=20, sticky="we")
        self.switch_2 = CTkSwitch(master=self, text="CTkSwitch")
        self.switch_2.grid(row=7, column=2, columnspan=1, pady=10, padx=20, sticky="we")

        # Settings dropdown
        self.combobox_1 = CTkComboBox(master=self, values=["No file selected"])
        self.combobox_1.grid(row=8, column=2, columnspan=1, pady=10, padx=20, sticky="we")

        # Check boxes
        self.check_box_1 = CTkCheckBox(master=self, text="CTkCheckBox")
        self.check_box_1.grid(row=9, column=0, pady=10, padx=20, sticky="w")
        self.check_box_2 = CTkCheckBox(master=self, text="CTkCheckBox")
        self.check_box_2.grid(row=9, column=1, pady=10, padx=20, sticky="w")

        self.entry = CTkEntry(master=self, width=120, placeholder_text="CTkEntry")
        self.entry.grid(row=10, column=0, columnspan=2, pady=20, padx=20, sticky="we")

        self.button_5 = CTkButton(master=self, text="CTkButton", border_width=2, fg_color=None, command=self.button_event)
        self.button_5.grid(row=10, column=2, columnspan=1, pady=20, padx=20, sticky="we")

        # set default values
        self.combobox_1.set("CTkCombobox")
        #self.progressbar.set(0.5)
        self.switch_2.select()
        #self.radio_button_3.configure(state=tkinter.DISABLED)
        #self.check_box_1.configure(state=tkinter.DISABLED, text="CheckBox disabled")
        self.check_box_2.select()


        # Actual stuff
        self.active_files = {}
        self.active_file_type = "All"
        self.save_folder_path = None
        self.multistack_img = None
        self.current_image = None
        self.red_channel = None
        self.green_channel = None
        self.blue_channel = None
        self.label_names = {}

    def open_image(self):
        pass

    def set_save_folder(self, folder_path):
        self.save_folder_path = folder_path

    def save_attachments(self):
        if not self.save_folder_path or not os.path.exists(self.save_folder_path):
            return
        with CziFile(self.save_folder_path) as cf:
            cf.save_attachments(directory="./test_images/")

    def get_current_image_channels(self, path):
        if not os.path.exists(path):
            return
        if path.split(".")[-1] == "tif":
            img = imread(path)
            print(img.shape)
            if not len(img.shape) == 5:
                return

            cv.split(self.current_image)
            self.red_channel = img[:, :, 0]
            self.green_channel = img[:, :, 1]
            self.blue_channel = img[:, :, 2]
        return

    def save_entire_stack_as_jpg(self, tifPath, imageFormat, folderPath):
        """ Function to convert tif to image

        Args:
            tifPath (str): path of input tif
            imageFormat (str): format to save image
            folderPath (str): Folder to save images
        Returns:
            int: 0 if successful
        """
        try:
            print('tiftoimage: {}'.format(tifPath))
            sep = '/' if '/' in tifPath else '\\'
            fileName = tifPath.split(sep)[-1][:-4]
            ### Loading tiff image
            tiffstack = Image.open(tifPath)
            tiffstack.load()

            ### Saving each image to output folder
            for i in range(tiffstack.n_frames):
                tiffstack.seek(i)
                pageName = fileName + '_{:05d}.{}'.format(i + 1, imageFormat)
                imagePath = os.path.join(folderPath, pageName)
                tiffstack.save(imagePath, format="JPEG")
        except FileNotFoundError as fnfe:
            print("File not found!\nRecieved error:\n", fnfe)
        except Exception as e:
            print("Error\n", e)

    def read_multi_stack_tif(self, tiff_path):
        try:
            # it's important to set the right flags. If you want the separate channels/pages to be read as is
            # https://docs.opencv.org/3.4/d8/d6a/group__imgcodecs__flags.html#ga61d9b0126a3e57d9277ac48327799c80
            self.multistack_img = cv.imreadmulti(tiff_path, flags=cv.IMREAD_UNCHANGED)
        except EOFError:
            pass

    def PIL_to_cv2(self, img):
        np_img = np.array(img)
        #cv2_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return np_img

    def button_event(self):
        print("Button is pressed")

