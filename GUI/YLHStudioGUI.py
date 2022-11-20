import tkinter
from datetime import time
import concurrent.futures
import tkinter
import tkinter.filedialog as fd
import time
import matplotlib.pyplot as plt
from PIL import Image, ImageEnhance
from customtkinter import *
from czifile import CziFile, czi2tif
from GUI.HelperFrames.CZIViewerFrame import CZIViewerFrame
import numpy as np
from PIL import Image, TiffImagePlugin, ImageEnhance, ImageTk
import pytesseract as tess

tess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
import cv2 as cv
from tifffile import TiffFile
import os
from GUI.HelperFrames.LabelOCRFrame import LabelOCRFrame
from customtkinter import *
# from GUI.Primitives.StudioGUI import StudioGUI
from GUI.HelperFrames.CZIViewerFrame import CZIViewerFrame
from GUI.HelperFrames.LabelOCRFrame import LabelOCRFrame


class File:
    def __init__(self, path):
        self.path = path
        self.edited = False
        self.viewed = False
        self.preprocessed_jpeg = None
        self.unprocessed_jpeg = None
        self.tiff_images = []
        self.filename = path.split("/")[-1]
        self.type = path.split(".")[-1]
        self.display_string = f" -->  {self.filename}\n"


class YLHStudio(CTk):
    # set_default_color_theme(f"{os.getcwd()}\\Assets\\Themes\\sweetkind.json")
    # set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

    def __init__(self):
        super().__init__()
        self.title("YLHStudio")
        self.HEADER_TEXT = tkinter.StringVar(value="Yumi's Little Helper Studio")
        self.WIDTH = 950
        self.HEIGHT = 650
        self.main_WIDTH = int(self.WIDTH * 5 / 8)
        self.side_bar_WIDTH = self.WIDTH - self.main_WIDTH
        self.minsize(900, 600)
        x, y = self.get_center_window_offsets()
        self.geometry(f"{self.WIDTH}x{self.HEIGHT} + {x} + {y}")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed
        self.INFO_DISPLAY = None
        self.PROGRESS_BAR = None
        self.files_label = None
        self.active_files = {}
        self.active_files_iter = None
        self.selected_files_of_type = {"All": {}, "png": {}, "czi": {}, "tiff": {}, "tif": {}}
        self.selected_files_of_type_str = {"All": "", "png": "", "czi": "", "tiff": "", "tif": ""}
        self.frames = {"Start": None}
        self.active_frame = None
        self.current_file = None
        self.top_menu_buttons = self.frames
        # Setup folder for the Tiff files with labels
        self.tiff_dir = f"{os.getcwd()}\\TEMP\\tiffs_with_labels"
        if not os.path.exists(self.tiff_dir):
            os.makedirs(self.tiff_dir)

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
        # self.top_bar_frame.columnconfigure(1, weight=0)
        # self.top_bar_frame.columnconfigure(2, weight=0)
        # self.top_bar_frame.columnconfigure(3, weight=0)
        # self.top_bar_frame.columnconfigure(4, weight=0)
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
        self.side_bar_frame.grid_rowconfigure(7, weight=1)  # empty row as spacing
        self.side_bar_frame.grid_rowconfigure(10, weight=1)  # empty row as spacing
        self.side_bar_frame.grid_rowconfigure(11, minsize=10)  # empty row with minsize as spacing

        # File type filter dropdown
        self.file_type_option = CTkOptionMenu(master=self.side_bar_frame,
                                              values=list(self.selected_files_of_type.keys()),
                                              command=self.choose_file_type)
        self.file_type_option.grid(row=0, column=0, padx=10, pady=10)

        self.appearance_mode_label = CTkLabel(text="Active Files:", master=self.side_bar_frame,
                                              text_font=("Roboto Medium", -14), anchor="w")

        self.appearance_mode_label.grid(row=1, column=0, pady=0, padx=20, sticky="w")

        # File window
        self.files_window = CTkTextbox(self.side_bar_frame)
        self.files_window.grid(row=2, column=0, padx=5, pady=10)
        self.files_window.insert("0.0", "  No active files... ")
        self.files_window.configure(text_font=("Roboto Medium", -12), padx=10, pady=10)
        self.files_window.configure(state="disabled")  # configure textbox to be read-only

        # Add folder button
        self.add_files_btn = CTkButton(text="Add Folder", master=self.side_bar_frame, command=self.add_folder)
        self.add_files_btn.grid(row=4, column=0, pady=5, padx=10, sticky="ew")
        # Add single file button
        self.add_files_btn = CTkButton(text="Add Single File", master=self.side_bar_frame, command=self.add_files)
        self.add_files_btn.grid(row=5, column=0, pady=5, padx=10, sticky="ew")
        # Clear files button
        self.clear_files_btn = CTkButton(text="Clear Files", border_width=2, fg_color=None,
                                         master=self.side_bar_frame, command=self.clear_files)
        self.clear_files_btn.grid(row=6, column=0, pady=5, padx=10, sticky="ew")
        # Settings dropdown
        self.convert_type_var = tkinter.StringVar(value="Don't convert")
        self.convert_type_menu = CTkOptionMenu(master=self.side_bar_frame,
                                               values=[
                                                   "Don't convert",
                                                   "CZI to TIFF",
                                                   "CZI to JPEG",
                                                   "TIFF to .jpeg"
                                               ], variable=self.convert_type_var)
        self.convert_type_menu.grid(row=8, column=0, columnspan=1, pady=5, padx=10, sticky="we")
        # Clear files button
        self.clear_files_btn = CTkButton(text="Convert Files", border_width=2, fg_color=None,
                                         border_color="#cb3b3b", text_color="#cb3b3b",
                                         master=self.side_bar_frame, command=self.conversion_callback)
        self.clear_files_btn.grid(row=9, column=0, pady=5, padx=10, sticky="ew")


        # Appearence selection!
        self.switch_var = StringVar(value="Dark")
        switch_1 = CTkSwitch(master=self.side_bar_frame, text="Dark Mode", command=self.switch_dark_mode,
                             variable=self.switch_var, onvalue="Dark", offvalue="Light")
        switch_1.grid(row=11, column=0, padx=20, pady=20, sticky="sw")

        # =====================================
        # ============ Main Window ============
        # =====================================
        # Invisibleain frame used as a container for all helper frames and start page
        self.main_frame = CTkFrame(master=self, fg_color=None)
        self.main_frame.grid(row=1, column=2, rowspan=self.num_rows - 2, columnspan=self.num_cols, sticky="nswe",
                             padx=20, pady=20)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Start Frame
        self.start_frame = CTkFrame(master=self.main_frame)
        self.start_frame.rowconfigure(0, weight=1)
        self.start_frame.columnconfigure(0, weight=1)
        self.frames["Start"] = self.start_frame
        self.start_frame.grid(row=0, column=0, pady=0, padx=0, sticky="nsew")
        self.temp_start_label = CTkLabel(master=self.start_frame,
                                         text="START FRAME")  # TODO Add useful stuff/info to start page
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

        # CZIViewer Frame
        self.CZIViewerFrame = CZIViewerFrame(self.main_frame, self.PROGRESS_BAR)
        self.CZIViewerButton = self.add_helper_frame("CZIViewer", self.CZIViewerFrame)
        # LabelOCR Frame
        self.LabelOCRFrame = LabelOCRFrame(self.main_frame, self.PROGRESS_BAR)
        self.label_ocr_button = self.add_helper_frame("LabelOCR", self.LabelOCRFrame)

        self.show_frame("Start")

    # ---------------  Callback Functions  --------------------
    def clear_files(self):
        self.files_window.configure(state="normal")  # configure textbox to be read-write
        self.files_window.insert("0.0", "  No active files... ")
        self.files_window.textbox.delete("0.0", "end")
        self.files_window.configure(state="disabled")  # configure textbox to be read-only
        self.active_files = {}
        self.CZIViewerFrame.set_active_files({})
        self.LabelOCRFrame.set_active_files({})
        for key in self.selected_files_of_type.keys():
            self.selected_files_of_type[key] = {}
            # self.active_files_of_type_str[key] = ""

    def display_files(self):
        self.files_window.configure(state="normal")  # configure textbox to be read-write
        self.files_window.textbox.delete("0.0", "end")
        file_str = ""
        for file in self.selected_files_of_type[self.file_type_option.get()].values():
            file_str += file.display_string
        self.files_window.insert("0.0", file_str)
        self.files_window.configure(state="disabled")  # configure textbox to be read-only

    def choose_file_type(self, file_type):
        #print("chose filter: ", file_type)
        self.active_files = self.selected_files_of_type[file_type]
        self.CZIViewerFrame.set_active_files(self.active_files)
        self.CZIViewerFrame.active_file_type = file_type
        self.LabelOCRFrame.set_active_files(self.active_files)
        self.LabelOCRFrame.active_file_type = file_type
        #print(self.active_files)
        #print(self.selected_files_of_type)
        self.display_files()

    def add_folder(self):
        dirname = fd.askdirectory(title="Select File or Folder")
        if not dirname:
            print("Nothing selected!")
            pass
        all_files = os.listdir(dirname)
        for filename in all_files:
            file_path = f"{dirname}/{filename}"
            if file_path in self.active_files.keys() or \
                    file_path.split(".")[-1] not in self.selected_files_of_type_str.keys():
                continue
            new_file = File(file_path)
            self.selected_files_of_type[new_file.type][file_path] = new_file
            self.selected_files_of_type["All"][file_path] = new_file
            self.active_files[file_path] = new_file
        self.CZIViewerFrame.set_active_files(self.active_files)
        self.LabelOCRFrame.set_active_files(self.active_files)
        self.display_files()

    def add_files(self):
        file_path = fd.askopenfilename(title="Select one file")
        if not file_path or file_path in self.active_files.keys():
            pass
        elif file_path.split(".")[-1] not in self.selected_files_of_type_str.keys():
            pass
        else:
            new_file = File(file_path)
            self.selected_files_of_type[new_file.type][file_path] = new_file
            self.selected_files_of_type["All"][file_path] = new_file
            self.active_files[file_path] = new_file
            self.CZIViewerFrame.set_active_files(self.active_files)
            self.LabelOCRFrame.set_active_files(self.active_files)
            self.display_files()

    def add_helper_frame(self, helper_name, helper_frame_obj):
        next_button_location = len(self.frames.keys())
        self.frames[helper_name] = helper_frame_obj
        self.top_bar_frame.columnconfigure(next_button_location, weight=0)
        self.top_bar_frame.columnconfigure(next_button_location + 1, weight=1)
        helper_frame_obj.grid(row=0, column=0, pady=0, padx=0, sticky="nsew")
        helper_frame_obj.rowconfigure(0, weight=1)
        helper_frame_obj.columnconfigure(0, weight=1)
        helper_button = CTkButton(master=self.top_bar_frame, command=lambda: self.show_frame(helper_name),
                                  text=helper_name, fg_color=None, corner_radius=0)
        helper_button.grid(row=0, column=next_button_location, padx=0, pady=0, sticky="nsew")
        return helper_button

    def show_frame(self, frame_id):
        f = self.frames[frame_id]
        # print("showing frame: ", frame_id, "of type", type(self.frames[frame_id]))
        # print("with master: ", id(f.master))
        if frame_id:
            frame = self.frames[frame_id]
            frame.tkraise()
            self.active_frame = frame
        else:
            print("No such frame!")

    def get_center_window_offsets(self):
        # get screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        # calculate position x and y coordinates
        x = (screen_width / 2) - (self.WIDTH / 2)
        y = (screen_height / 2) - (self.HEIGHT / 2)
        return x, y

    def next_new_image(self):
        if not self.active_files:
            yield None
        for path in self.active_files.keys():
            yield path

    def conversion_callback(self):
        if self.convert_type_var.get() == "Don't convert":
            print("No conversion selected!")
        elif self.convert_type_var.get() == "CZI to TIFF":
            print(f"Converting: {self.active_files.keys()}!")
            self.batch_process_czi(self.active_files.keys(), self.tiff_dir)
            self.LabelOCRFrame.set_active_files(self.active_files)
            print("\n##################################\n")
            print("##      DONE CONVERTING!        ##")
            print("##     Starting: renaming       ##")
            print("\n##################################\n")
            #self.CZIViewerFrame.set_active_files(self.active_files)
            #print(f"Done converting all {self.convert_type_var.get()}!")
        else:
            print(f"Conversion {self.convert_type_var.get()} not yet implemented!")

    def switch_dark_mode(self):
        set_appearance_mode(self.switch_var.get())

    def on_closing(self, event=0):
        self.destroy()

    # ------------------ Conversion ------------------
    def show_progress(self, done):
        self.PROGRESS_BAR.set(done)

    # @staticmethod
    def batch_process_czi(self, czi_file_list, tiff_dir):
        total = len(czi_file_list)
        done = 0
        with concurrent.futures.ProcessPoolExecutor() as exe:
            results = [exe.submit(self.save_image_with_label, czi, tiff_dir) for czi in czi_file_list]
            for future in concurrent.futures.as_completed(results):
                done += future.result()
                self.PROGRESS_BAR.set(done / total)
            self.PROGRESS_BAR.set(0)

    @staticmethod
    def save_image_with_label(czi_path, tiff_dir):
        """
        Goes through all active files and, if they are .czi files, checks for attachments with
        the word "Label" in the name. All such files and their labels will be
        saved to .tif format in a "tiff_image_*filenum*" directory for further processing.

        :return: None
        """
        # for i, main_czi_path in enumerate(self.active_files):
        print("\n\nCurrent CZI:  ", czi_path)
        with CziFile(czi_path) as cf:
            for att in cf.attachments():
                print(str(att))
            for att in cf.attachments():
                label_path = att.attachment_entry.filename
                tiff_and_label_id = str(label_path).split("@")[-1].split(".")[0]
                tiff_and_label_dir = f"{tiff_dir}\\Image_no_{tiff_and_label_id}"
                label_czi_path = f"{tiff_and_label_dir}\\{label_path}"
                if "Label" not in str(att) or os.path.exists(label_czi_path):
                    print("Label not in att!", str(att))
                    continue
                # If it gets here it must be a new file, so we nee to process it
                os.makedirs(tiff_and_label_dir)
                # need to save it first in order to access it. TODO: Must be a better way!
                print("Label czi path: ", label_czi_path)
                att.save(label_czi_path)
                out_tif_path = f"{tiff_and_label_dir}\\{label_path.split('.')[0]}.tif"
                # Save label as tif
                czi2tif(os.path.abspath(label_czi_path), out_tif_path)
                czi2tif(czi_path, f"{tiff_and_label_dir}\\tiff_image_{tiff_and_label_id}.tif")
        # Save image_file as tif
        return 1

        """
        except FileNotFoundError as fnfe:
            print("File does not exist!\n", fnfe)
            return 0
        except Exception as e:
            print("Something went wrong... but file exists at least!\n")
            print(e)
            return 0
        """
