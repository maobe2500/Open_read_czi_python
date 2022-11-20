import tkinter
import tkinter.filedialog as fd
import time
import matplotlib.pyplot as plt
from czifile import *
from customtkinter import *
from GUI.HelperFrames.CZIViewerFrame import CZIViewerFrame
import numpy as np
import sys
import os
from GUI.HelperFrames.LabelOCRFrame import LabelOCRFrame


class StudioGUI(CTk):
    set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

    def __init__(self):
        super().__init__()
        self.WIDTH = 900
        self.HEIGHT = 600
        self.main_WIDTH = int(self.WIDTH * 5 / 8)
        self.side_bar_WIDTH = self.WIDTH - self.main_WIDTH
        self.minsize(400, 300)
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed
        self.INFO_DISPLAY = None
        self.PROGRESS_BAR = None
        self.files_label = None
        self.active_files = []
        self.active_files_of_type = {"All": [], "png": [], "czi": [], "tiff": [], "tif": []}
        self.active_files_of_type_str = {"All": "", "png": "", "czi": "", "tiff": "", "tif": ""}
        self.frames = {"Start": None}
        self.active_frame = None
        self.top_menu_buttons = self.frames

        # ============================== Studio 6 x 4 Layout =================================
        # |_____ Top Bar _____||_____ Top Bar _____||_____ Top Bar _____||_____ Top Bar _____|
        # |_ Side Bar _||_ Side Bar _||_______ Main Frame _______||_______ Main Frame _______|
        # |_ Side Bar _||_ Side Bar _||_______ Main Frame _______||_______ Main Frame _______|
        # |_ Side Bar _||_ Side Bar _||_______ Main Frame _______||_______ Main Frame _______|
        # |_ Side Bar _||_ Side Bar _||_______ Main Frame _______||_______ Main Frame _______|
        # |_ Side Bar _||_ Side Bar _||_______ Main Frame _______||_______ Main Frame _______|
        # ====================================================================================

        self.num_rows = 6
        self.num_cols = 4
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)

        # ============== Helper Frames ===============

        # =====================================
        # ============= Top Menu ==============
        # =====================================
        self.top_bar_frame = CTkFrame(master=self,
                                      width=self.WIDTH,
                                      fg_color=("gray98", "gray10"),
                                      corner_radius=0)
        self.top_bar_frame.grid(row=0, column=0, columnspan=self.num_cols, pady=0, padx=0, sticky="nsew")
        self.top_bar_frame.rowconfigure(1, weight=0)
        self.top_bar_frame.columnconfigure(0, weight=0)
        #self.top_bar_frame.columnconfigure(1, weight=0)
        #self.top_bar_frame.columnconfigure(2, weight=0)
        #self.top_bar_frame.columnconfigure(3, weight=0)
        #self.top_bar_frame.columnconfigure(4, weight=0)
        self.top_bar_frame.columnconfigure(0, weight=0)
        self.top_bar_frame.columnconfigure(1, weight=1)

        self.top_menu_item_1 = CTkButton(master=self.top_bar_frame, command=lambda: self.show_frame("Start"),
                                         text="Start",
                                         fg_color=None, corner_radius=0)
        self.top_menu_item_1.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        self.PROGRESS_BAR = CTkProgressBar(master=self.top_bar_frame,
                                           corner_radius=0, height=2, fg_color=("gray98", "gray10"))
        self.PROGRESS_BAR.grid(row=1, column=0, columnspan=self.num_cols, sticky="nsew", padx=0, pady=0)
        self.PROGRESS_BAR.set(0)

        # =====================================
        # ============= Side Bar ==============
        # =====================================
        self.side_bar_frame = CTkFrame(master=self,
                                       width=self.side_bar_WIDTH,
                                       corner_radius=0)
        self.side_bar_frame.grid(row=1, column=0, rowspan=self.num_rows, columnspan=2, sticky="nswe")
        self.side_bar_frame.grid_rowconfigure(8, minsize=20)  # empty row with minsize as spacing
        self.side_bar_frame.grid_rowconfigure(6, weight=1)  # empty row as spacing
        self.side_bar_frame.grid_rowconfigure(11, minsize=10)  # empty row with minsize as spacing

        # File type filter dropdown
        self.file_type_option = CTkOptionMenu(master=self.side_bar_frame,
                                              values=list(self.active_files_of_type.keys()),
                                              command=self.choose_file_type)
        self.file_type_option.grid(row=0, column=0, padx=10, pady=10)

        self.appearance_mode_label = CTkLabel(text="Active Files:", master=self.side_bar_frame,
                                              text_font=("Roboto Medium", -14), anchor="w")

        self.appearance_mode_label.grid(row=1, column=0, pady=0, padx=20, sticky="w")

        # File window
        self.files_window = CTkTextbox(self.side_bar_frame)
        self.files_window.grid(row=2, column=0, padx=5, pady=0)
        self.files_window.insert("0.0", "  No active files... ")
        self.files_window.configure(text_font=("Roboto Medium", -12), padx=10, pady=10)

        # Add folder button
        self.add_files_btn = CTkButton(text="Add Folder", master=self.side_bar_frame, command=self.add_folder)
        self.add_files_btn.grid(row=4, column=0, pady=5, padx=10, sticky="ew")
        # Add single file button
        self.add_files_btn = CTkButton(text="Add Single File", master=self.side_bar_frame, command=self.add_files)
        self.add_files_btn.grid(row=4, column=0, pady=5, padx=10, sticky="ew")
        # Clear files button
        self.clear_files_btn = CTkButton(text="Clear Files", master=self.side_bar_frame, command=self.clear_files)
        self.clear_files_btn.grid(row=5, column=0, pady=10, padx=10, sticky="ew")

        # Appearence selection!
        self.switch_var = StringVar(value="Dark")
        switch_1 = CTkSwitch(master=self.side_bar_frame, text="Dark Mode", command=self.switch_dark_mode,
                             variable=self.switch_var, onvalue="Dark", offvalue="Light")
        switch_1.grid(row=10, column=0, padx=20, pady=10, sticky="sw")

        # =====================================
        # ============ Main Window ============
        # =====================================
        # Invisibleain frame used as a container for all helper frames and start page
        self.main_frame = CTkFrame(master=self, fg_color=None)
        self.main_frame.grid(row=1, column=2, rowspan=self.num_rows-2, columnspan=self.num_cols, sticky="nswe",
                             padx=20, pady=20)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Start Frame
        self.start_frame = CTkFrame(master=self.main_frame)
        self.start_frame.rowconfigure(0, weight=1)
        self.start_frame.columnconfigure(0, weight=1)
        self.frames["Start"] = self.start_frame
        self.start_frame.grid(row=0, column=0, pady=0, padx=0, sticky="nsew")
        self.temp_start_label = CTkLabel(master=self.start_frame, text="START FRAME")  # TODO Add useful stuff/info to start page
        self.temp_start_label.grid(row=0, column=0)

        """
        self.frames["CZIViewer"] = self.CZIViewer_frame
        self.CZIViewer_frame.grid(row=0, column=0, pady=0, padx=0, sticky="nsew")
        self.CZIViewer_frame.rowconfigure(0, weight=1)
        self.CZIViewer_frame.columnconfigure(0, weight=1)

        self.CZIViewer_button = CTkButton(master=self.top_bar_frame, command=lambda: self.show_frame("CZIViewer"),
                                          text="CZIViewer", fg_color=None, corner_radius=0)
        self.CZIViewer_button.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        """
        self.show_frame("Start")

    # ---------------  Callback Functions  --------------------
    def clear_files(self):
        self.files_window.configure(state="normal")  # configure textbox to be read-write
        #self.f_string = "Empty... "
        self.files_window.textbox.delete("0.0", "end")
        #self.files_window.insert("0.0", self.f_string)
        self.files_window.configure(state="disabled")  # configure textbox to be read-only
        self.active_files = []
        for key in self.active_files_of_type.keys():
            self.active_files_of_type[key] = []
            #self.active_files_of_type_str[key] = ""

    def display_files(self):
        self.files_window.configure(state="normal")  # configure textbox to be read-write
        self.files_window.textbox.delete("0.0", "end")
        file_string = self.active_files_of_type_str[self.file_type_option.get()]
        self.files_window.insert("0.0", file_string)
        self.files_window.configure(state="disabled")  # configure textbox to be read-only

    def choose_file_type(self, file_type):
        print("chose filter: ", file_type)
        self.active_files = self.active_files_of_type[file_type]
        print(self.active_files)
        print(self.active_files_of_type)
        self.display_files()

    def add_folder(self):
        dirname = fd.askdirectory(title="Select File or Folder")
        for val in self.active_files_of_type_str.values():
            val += f"\n{dirname.split('/')[-1]}\n"
        all_files = os.listdir(dirname)
        for file in all_files:
            f_type = file.split(".")[-1]
            if f_type in self.active_files_of_type_str.keys():
                self.active_files_of_type_str[f_type] += f" -->  {file}\n"
                self.active_files_of_type[f_type].append(file)
            self.active_files_of_type_str["All"] += f" -->  {file}\n"
            self.active_files_of_type["All"].append(file)
            self.active_files.append(file)
        self.display_files()

    def add_folder(self):
        dirname = fd.askdirectory(title="Select File or Folder")
        for val in self.active_files_of_type_str.values():
            val += f"\n{dirname.split('/')[-1]}\n"
        all_files = os.listdir(dirname)
        for file in all_files:
            f_type = file.split(".")[-1]
            if f_type in self.active_files_of_type_str.keys():
                self.active_files_of_type_str[f_type] += f" -->  {file}\n"
                self.active_files_of_type[f_type].append(file)
            self.active_files_of_type_str["All"] += f" -->  {file}\n"
            self.active_files_of_type["All"].append(file)
            self.active_files.append(file)
        self.display_files()

    def display_progress(self):
        total = 100
        for i in range(100):
            self.PROGRESS_BAR.set(self.PROGRESS_BAR.get() + 0.01)
            time.sleep(0.01)

    def show_frame(self, frame_id):
        f = self.frames[frame_id]
        #print("showing frame: ", frame_id, "of type", type(self.frames[frame_id]))
        #print("with master: ", id(f.master))
        if frame_id:
            frame = self.frames[frame_id]
            frame.tkraise()
            self.active_frame = frame
        else:
            print("No such frame!")

    def add_helper_frame(self, helper_name, helper_frame_obj):
        next_button_location = len(self.frames.keys())
        self.frames[helper_name] = helper_frame_obj
        self.top_bar_frame.columnconfigure(next_button_location, weight=0)
        self.top_bar_frame.columnconfigure(next_button_location+1, weight=1)
        helper_frame_obj.grid(row=0, column=0, pady=0, padx=0, sticky="nsew")
        helper_frame_obj.rowconfigure(0, weight=1)
        helper_frame_obj.columnconfigure(0, weight=1)
        helper_button = CTkButton(master=self.top_bar_frame, command=lambda: self.show_frame(helper_name),
                                  text=helper_name, fg_color=None, corner_radius=0)
        helper_button.grid(row=0, column=next_button_location, padx=0, pady=0, sticky="nsew")
        return helper_button

    def switch_dark_mode(self):
        set_appearance_mode(self.switch_var.get())

    def on_closing(self, event=0):
        self.destroy()

