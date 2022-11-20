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

# Remove !
import logging
logging.basicConfig(level=logging.DEBUG)


class ShakespeareanError(Exception):
    def __init__(self):
        """ My tongue will tell the anger of my heart, or else my heart concealing it will break. """
        super(self).__init__()
        self.sonnet29 = "When, in disgrace with fortune and men’s eyes,\n" \
                        "I all alone beweep my outcast state,\n" \
                        "And trouble deaf heaven with my bootless cries,\n" \
                        "And look upon myself and curse my fate,\n" \
                        "Wishing me like to one more rich in hope,\n" \
                        "Featured like him, like him with friends possessed,\n" \
                        "Desiring this man’s art and that man’s scope,\n" \
                        "With what I most enjoy contented least;\n" \
                        "Yet in these thoughts myself almost despising,\n" \
                        "Haply I think on thee, and then my state,\n" \
                        "(Like to the lark at break of day arising\n" \
                        "From sullen earth) sings hymns at heaven’s gate;\n" \
                        "\tFor thy sweet love remembered such wealth brings\n" \
                        "\tThat then I scorn to change my state with kings."

    def __str__(self):
        return self.sonnet29


class LabelOCRFrame(CTkFrame):
    def __init__(self, master, progress_bar, *args, **kwargs):
        CTkFrame.__init__(self, master=master, *args, **kwargs)

        # GUI Stuff
        self.master = master
        self.PROGRESS_BAR = progress_bar
        self.test_label = CTkLabel(master=self, text="OCR FRAME")
        self.test_label.grid(row=0, column=0)
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
        self.edit_mode_btn = CTkButton(master=self, text="Edit Mode", command=self.edit_mode_callback)
        self.edit_mode_btn.grid(row=1, column=2, pady=10, padx=20, sticky="we")
        self.test_OCR_btn = CTkButton(master=self, text="Test OCR", command=self.test_OCR_accuracy)
        self.test_OCR_btn.grid(row=2, column=2, pady=10, padx=20, sticky="we")
        self.name_files_btn = CTkButton(master=self, text="Name files as labels", command=self.name_files_as_labels)
        self.name_files_btn.grid(row=3, column=2, pady=10, padx=20, sticky="we")

        # ============ frame_info ============
        # configure grid layout (1x1)
        self.frame_info.rowconfigure(0, weight=1)
        self.frame_info.columnconfigure(0, weight=1)

        # Sliders
        self.bin_low_slider = CTkSlider(master=self, from_=0, to=127, number_of_steps=128, command=self.update_bin_thresholds)
        self.bin_high_slider = CTkSlider(master=self, from_=128, to=255, number_of_steps=127, command=self.update_bin_thresholds)
        self.bin_low_slider.grid(row=9, column=0, columnspan=2, pady=10, padx=20, sticky="we")
        self.bin_high_slider.grid(row=10, column=0, columnspan=2, pady=10, padx=20, sticky="we")

        # Switches
        self.manual_check = CTkSwitch(master=self, text="Confirm each file manually")
        self.manual_check.grid(row=4, column=2, columnspan=1, pady=20, padx=20, sticky="we")


        # Check box noise
        self.noise_var = tkinter.BooleanVar(master=self, value=False)
        self.check_box_1 = CTkCheckBox(master=self, text="Noise Removal", variable=self.noise_var, command=self.edit_image)
        self.check_box_1.grid(row=6, column=2, pady=10, padx=20, sticky="w")
        # Check box erosion
        self.erod_var = tkinter.BooleanVar(master=self, value=False)
        self.check_box_2 = CTkCheckBox(master=self, text="Erosion", variable=self.erod_var, command=self.edit_image)
        self.check_box_2.grid(row=7, column=2, pady=10, padx=20, sticky="w")
        # Check box grayscale
        self.gray_var = tkinter.BooleanVar(master=self, value=False)
        self.check_box_3 = CTkCheckBox(master=self, text="Grayscale", variable=self.gray_var, command=self.edit_image)
        self.check_box_3.grid(row=8, column=2, pady=10, padx=20, sticky="w")
        # Check box binarization
        self.bin_var = tkinter.BooleanVar(master=self, value=False)
        self.check_box_4 = CTkCheckBox(master=self, text="Binarization", variable=self.bin_var, command=self.edit_image)
        self.check_box_4.grid(row=9, column=2, pady=10, padx=20, sticky="w")

        self.button_5 = CTkButton(master=self, text="Quit", border_width=2, fg_color=None,
                                  command=lambda: print("Nothing"))
        self.button_5.grid(row=10, column=2, columnspan=1, pady=20, padx=20, sticky="we")

        # Image processing stuff

        # Setup folder for the Tiff files with labels
        self.tiff_dir = f"{os.getcwd()}\\TEMP\\tiffs_with_labels"
        if not os.path.exists(self.tiff_dir):
            os.makedirs(self.tiff_dir)

        self.active_files = {}
        self.files_to_preprocess = []
        self.editing_images_files_cache = {}
        self.current_settings = {"Noise Removal": False, "Erosion": False, "Dilation": False,
                                 "Grayscale": False, "Binarization": False}
        self.binarization_threshold_low = 50
        self.bin_low_slider.set(self.binarization_threshold_low)
        self.binarization_threshold_high = 250
        self.bin_high_slider.set(self.binarization_threshold_high)
        self.editing_mode = False
        self.current_image = None
        self.current_file = None
        self.OCR_RESULTS = {}

    def set_active_files(self, files_list):
        self.active_files = files_list
        self.name_files_as_labels()

    def show_progress(self, done):
        self.PROGRESS_BAR.set(done)

    #@staticmethod
    def batch_process_czi(self, czi_file_list, tiff_dir):
        total = len(czi_file_list)
        done = 0
        with concurrent.futures.ProcessPoolExecutor(max_workers=2) as exe:
            results = [exe.submit(self.save_image_with_label, czi, tiff_dir) for czi in czi_file_list]
            for future in concurrent.futures.as_completed(results):
                done += future.result()
                self.PROGRESS_BAR.set(done/total)
            self.PROGRESS_BAR.set(0)

    @staticmethod
    def save_image_with_label(czi_path, tiff_dir):
        """
        Goes through all active files and, if they are .czi files, checks for attachments with
        the word "Label" in the name. All such files and their labels will be
        saved to .tif format in a "tiff_image_*filenum*" directory for further processing.

        :return: None
        """
        #for i, main_czi_path in enumerate(self.active_files):
        #print("\n\nCurrent CZI:  ", czi_path)
        try:
            with CziFile(czi_path) as cf:
                for att in cf.attachments():
                    label_path = att.attachment_entry.filename
                    tiff_and_label_id = str(label_path).split("@")[-1].split(".")[0]
                    tiff_and_label_dir = f"{tiff_dir}\\Image_no_{tiff_and_label_id}"
                    if "Label" not in str(att) or os.path.exists(tiff_and_label_dir):
                        continue
                    # If it gets here it must be a new file, so we nee to process it
                    os.makedirs(tiff_and_label_dir)
                    # need to save it first in order to access it. TODO: Must be a better way!
                    label_czi_path = f"{tiff_and_label_dir}\\{label_path}"
                    att.save(label_czi_path)
                    #print("Label czi path: ", label_czi_path)
                    out_tif_path = f"{tiff_and_label_dir}\\{label_path.split('.')[0]}.tif"
                    os.path.abspath(label_czi_path), out_tif_path
                    czifile.czi2tif(os.path.abspath(label_czi_path), out_tif_path)  # Save label as tif
                    czifile.czi2tif(czi_path, f"{tiff_and_label_dir}\\tiff_image_{tiff_and_label_id}.tif")  # Save image_file as tif
            return 1
        except FileNotFoundError as fnfe:
            print("File does not exist!\n", fnfe)
            return 0
        except Exception as e:
            print("Something went wrong... but file exists at least!\n", e)
            return 0

    def get_jpg_from_tif(self, tiff_file_path, enhance_factor=3.5, save_as=None, return_path=False):
        """
        Creates and enhances a jpeg from the path to a .tif file and stores it
        in a the same folder as the .tif file.

        :param save_as:
        :param enhance_factor:
        :param tiff_file_path:  Path to a tiff file (.tif)
        :return outfile:        The path to the created jpeg file
        TODO Check if images needs to be enhances and determine for each image individually
        """
        #try:
        #if os.path.exists(jpeg_im_path):
        #    return Image.open(jpeg_im_path)
        img = cv.imread(tiff_file_path)               # read tif from file
        im = Image.fromarray(img, mode="RGB")   # read np array into PIL
        enhancer = ImageEnhance.Brightness(im)  # initialize image brightness enhancer
        out = enhancer.enhance(enhance_factor)    # brightens the image by specified factor
        #out.show()
        if save_as:
            jpeg_im_path =  f"{save_as}"
            out.save(jpeg_im_path, "JPEG", quality=100)
            return jpeg_im_path
        return out
        #except Exception as e:
        #    print("Something went wrong while converting from tiff to jpeg!\n", e)
        #    return None

    def is_tiff(self, im):
        return im.split(".")[-1] == "tif"

    def is_label(self, im):
        return im.split("@")[0] == "Label"

    def get_jpgs_to_process(self):
        #try:
        for file_folder in os.listdir(self.tiff_dir):
            image_no_dir = f"{self.tiff_dir}\\{file_folder}"
            #print("IMAG NO DIR", image_no_dir)
            jpeg_im_path = f"{image_no_dir}\\Label@{image_no_dir.split('_')[-1]}_UNPROCESSED.jpeg"
            #print("JPEG DIR", jpeg_im_path)
            for im in os.listdir(image_no_dir):
                #print(im)
                if self.is_tiff(im) and self.is_label(im):
                    jpeg_im = self.get_jpg_from_tif(f"{image_no_dir}\\{im}", save_as=jpeg_im_path)
                    self.files_to_preprocess.append(jpeg_im)
        #except Exception as e:
        #    print("Could not process jpegs...or something? idk.\n", e)

    def image_preprocessing(self, noise_removal=False, erosion=False, dilation=False, max_iter=10_000):
        i = 0
        #try:
        # Setup folder for the files ready for ocr
        while len(self.files_to_preprocess) > 0:
            file_to_process = self.files_to_preprocess.pop()
            #print("File to process", file_to_process)
            #name = file_to_process.split("\\")[-1]
            #logging.debug(f"File name:  {name}")
            img = cv.imread(file_to_process)
            #print("GETTING SKEW ANGLE")
            no_noise = self.noise_removal(img)
            skew_angle = self.getSkewAngle(no_noise)
            #print("SKEW ANGLE IS: ", skew_angle)

            bin_img = self.binarization(self.grayscale(no_noise), low=22, high=130)  # Create black/white image for binarization step to work well
            removed_borders = self.remove_borders(bin_img)
            #cv.imshow("Fixed borders", removed_borders)
            #cv.waitKey(0)
            deskewed_img = self.rotateImage(removed_borders, skew_angle)
            #cv.imshow(f"Fixed rotation, {skew_angle}", deskewed_img)
            #cv.waitKey(0)
            thicker_font = self.thick_font(deskewed_img)
            #cv.imshow(f"Fixed font", thicker_font)
            #cv.waitKey(0)

            #bin_img = self.binarization(self.grayscale(deskewed_img), low=10, high=130)  # Create black/white image for binarization step to work well
            out = Image.fromarray(thicker_font)  # Binarization step, tweak values!
            processed_path = file_to_process.replace("UNPROCESSED", "PREPROCESSED")
            #if not os.path.exists(processed_path):
            out.save(processed_path)
            if i >= max_iter:
                break
            self.PROGRESS_BAR.set(round(i/max(len(self.files_to_preprocess), 1), 3))
            i += 1
        #    print("Files preprocessed!")
        #except Exception as e:
        #    print("Error occured whilst processing images!", e)

    def format_and_save_new_files(self):
        #print("\tRAW_RESULTS:\n")
        Image.MAX_IMAGE_PIXELS = 933120000
        Image.MAX_IMAGE_PIXELS = None
        new_folder_path = f"{os.getcwd()}\\PrincessYumisKingdomOfFiles"
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)
        total = len(self.OCR_RESULTS.keys())
        done = 0
        for image_no, raw_text in self.OCR_RESULTS.items():
            new_filename = ""
            removed_empty = [text for text in raw_text.split("\n") if text]
            #print(removed_empty)
            for line in removed_empty:
                for word in line.split(" "):
                    if word.istitle() or word.isupper() or word.isnumeric():
                        new_filename += f"{word}_"
            #print("image number :  ", image_no)
            src = f"{image_no}\\tiff_image_{image_no.split('_')[-1]}.tif"
            dest = f"{new_folder_path}\\{new_filename}.tif"
            done += 1
            self.PROGRESS_BAR.set(round(done/max(len(self.files_to_preprocess), 1), 3))
            try:
                f = Image.open(src)
                f.save(dest)
                #os.rename(src, dest)
            except FileNotFoundError as fnfe:
                print(fnfe)
                print(os.path.exists(src))
                #print(fnfe)
                continue
            except Exception as e:
                print(e)
                continue

    def name_files_as_labels(self):
        #print("GETTING JPEGS")
        self.get_jpgs_to_process()
        #print("PROCESSING")
        self.image_preprocessing()
        #print("DONE PROCESSING")
        for file_folder in os.listdir(f"{self.tiff_dir}"):
            image_no_dir = f"{self.tiff_dir}\\{file_folder}"
            #print("IMAGEl_NO_DIR:  ", image_no_dir)
            for filename in os.listdir(image_no_dir):
                if "PREPROCESSED" not in filename:
                    continue
                #print("FILE:  ", filename)
                processed_label_jpeg = Image.open(f"{image_no_dir}\\{filename}")
                #processed_label_jpeg.show()
                #print("RUNNING OCR")
                raw_text = tess.image_to_string(processed_label_jpeg)
                #image_no_dir.split('_')[0].split('@')[-1]
                #print(image_no_dir)
                self.OCR_RESULTS[f"{image_no_dir}"] = raw_text
        self.format_and_save_new_files()

    def thick_font(self, image):
        image = cv.bitwise_not(image)
        kernel = np.ones((2, 2), np.uint8)
        image = cv.dilate(image, kernel, iterations=1)
        image = cv.bitwise_not(image)
        return image

    # Deskew image
    def deskew(self, cvImage):
        angle = self.getSkewAngle(cvImage)
        #print("ROTATING by ", angle)
        return self.rotateImage(cvImage, -1.0 * angle)

    def remove_borders(self, image):
        contours, heiarchy = cv.findContours(image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        cntsSorted = sorted(contours, key=lambda x: cv.contourArea(x))
        cnt = cntsSorted[-1]
        x, y, w, h = cv.boundingRect(cnt)
        #return y, y + h, x, x + w
        crop = image[y:y + h, x:x+h]
        return crop

    def getSkewAngle(self, cvImage):
        # Prep image, copy, convert to gray scale, blur, and threshold
        newImage = cvImage.copy()
        gray = cv.cvtColor(newImage, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gray, (9, 9), 0)
        thresh = cv.threshold(blur, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)[1]

        # Apply dilate to merge text into meaningful lines/paragraphs.
        # Use larger kernel on X axis to merge characters into single line, cancelling out any spaces.
        # But use smaller kernel on Y axis to separate between different blocks of text
        kernel = cv.getStructuringElement(cv.MORPH_RECT, (30, 5))
        dilate = cv.dilate(thresh, kernel, iterations=2)

        # Find all contours
        contours, hierarchy = cv.findContours(dilate, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv.contourArea, reverse=True)
        for c in contours:
            rect = cv.boundingRect(c)
            x, y, w, h = rect
            cv.rectangle(newImage, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Find largest contour and surround in min area box
        largestContour = contours[0]
        print(len(contours))
        minAreaRect = cv.minAreaRect(largestContour)
        cv.imwrite("temp/boxes.jpg", newImage)
        # Determine the angle. Convert it to the value that was originally used to obtain skewed image
        angle = minAreaRect[-1]
        if angle < -45:
            angle = 90 + angle
        return -1.0 * angle

    # Rotate the image around its center
    @staticmethod
    def rotateImage(cvImage, angle):
        newImage = cvImage.copy()
        (h, w) = newImage.shape[:2]
        center = (w // 2, h // 2)
        M = cv.getRotationMatrix2D(center, angle, 1.0)
        newImage = cv.warpAffine(newImage, M, (w, h), flags=cv.INTER_CUBIC, borderMode=cv.BORDER_REPLICATE)
        return newImage

    @staticmethod
    def invert(img_data, save_path="temp/g_test.jpeg", overwrite=False):
        inv_img = cv.bitwise_not(img_data)
        inv = Image.fromarray(inv_img)
        #if not os.path.exists(save_path):
        #    inv.save("temp/inv_test.jpeg")
        return inv_img

    @staticmethod
    def grayscale(img_data, save_path="temp/g_test.jpeg", overwrite=False):
        g_img = cv.cvtColor(img_data, cv.COLOR_BGR2GRAY)
        #g = Image.fromarray(g_img)
        #if not os.path.exists(save_path):
        #    g.save("temp/gray_test.jpeg")
        return g_img

    @staticmethod
    def binarization(img_data, low=10, high=130, save_path="temp/bw_test.jpeg", overwrite=False):
        thresh, bw_img = cv.threshold(img_data, low, high, cv.THRESH_BINARY)
        bw = Image.fromarray(bw_img)
        #if not os.path.exists(save_path):
        #    bw.save("temp/bw_test.jpeg")
        return bw_img

    @staticmethod
    def noise_removal(img_data, save_path=f"{os.getcwd()}\\temp\\noise_removal_test.jpeg", overwrite=False):
        kernel = np.ones((1, 1), np.uint8)
        image = cv.dilate(img_data, kernel, iterations=1)
        kernel = np.ones((1, 1), np.uint8)
        image = cv.erode(image, kernel, iterations=1)
        image = cv.morphologyEx(image, cv.MORPH_CLOSE, kernel)
        image = cv.medianBlur(image, 3)
        #if not os.path.exists(save_path):
        #    img_data.save("temp/noise_removal_test.jpeg")
        return image

    @staticmethod
    def dilation(im):
        im_out = im
        return im_out

    @staticmethod
    def erosion(im):
        im_out = im
        return im_out

    def update_bin_thresholds(self, updated_value):
        print(int(updated_value))
        im_in = self.current_file.jpeg
        if self.editing_mode:
            im_out = self.binarization(im_in, low=int(self.bin_low_slider.get()), high=int(self.bin_high_slider.get()))
            self.set_image(im_out)

    def edit_mode_callback(self):
        self.editing_mode = not self.editing_mode
        if not self.editing_mode:
            self.edit_mode_btn.configure(text="Edit", require_redraw=True)
            self.test_OCR_btn.configure(state=tkinter.DISABLED, require_redraw=True)
            self.open_image_btn.configure(state=tkinter.NORMAL, require_redraw=True)
        else:
            self.edit_mode_btn.configure(text="Quit Edit", require_redraw=True)
            self.test_OCR_btn.configure(state=tkinter.NORMAL, require_redraw=True)
            self.open_image_btn.configure(state=tkinter.DISABLED, require_redraw=True)
            self.edit_image()

    def edit_image(self):
        s = self.current_settings
        im = self.current_image
        try:
            if self.noise_var.get():
                self.current_image = self.noise_removal(self.current_image)
            if self.erod_var.get():
                self.current_image = self.erosion(self.current_image)
            #if s["Dilation"]:
            #    self.image_being_edited = self.dilation(self.image_being_edited)
            if self.gray_var.get():
                self.current_image = self.grayscale(self.current_image)
            if self.gray_var.get():
                self.current_image = self.binarization(self.current_image)
            self.set_image(im)
        except Exception as e:
            print("Something went wrong while editing the image...\n", e)

    def test_OCR_accuracy(self):
        test_text = tess.image_to_string(self.current_image)

    def set_image(self, img):
        self.master.update()
        current_size = (self.master.winfo_width(), self.master.winfo_height())
        img.thumbnail(current_size)
        img = img.resize(current_size, Image.ANTIALIAS)
        img = ImageTk.PhotoImage(img)
        self.image_panel = CTkLabel(self.frame_info, image=img)
        self.image_panel.grid(row=0, column=0, pady=5, padx=5, sticky="nsew")
        self.image_panel.image = img

    def open_image(self):
        if self.editing_mode:
            return
        #print("Active: ", self.active_files)
        current_active_file = self.current_image
        if current_active_file.split(".")[-1] == "czi":
            img_path = self.files_to_preprocess[self.img_index]
            self.img_index += 1
            if self.img_index == len(self.active_files):
                self.img_index = 0
            img = Image.open(img_path)
            self.set_image(img)
        else:
            print("Cannot open selected filetype!")


    def quit_app(self):
        self.master.master.destroy()


"""
def main():
    path_tif = "TiffsWithLabels/Image_no_125254720/Label@125254720.tif"

    # Brigthened and fixed image!
    #base_case = cv.imread("/temp/test2.jpg")
    img = cv.imread(get_jpg_from_tif(path_tif))
    #bw_img1 = Image.fromarray(binarization(grayscale(img), low=25, high=75))
    #bw_img2 = Image.fromarray(binarization(grayscale(img), low=20, high=100))
    #bw_img3 = Image.fromarray(binarization(grayscale(img), low=15, high=120))
    bw_img = Image.fromarray(binarization(grayscale(img), low=10, high=130))
    #bw_img_noise_removed = noise_removal(cv.imread("temp/"))
    bw_img.show()
    #bw_img_noise_removed.show()
    print(tess.image_to_string(bw_img))
    #print(tess.image_to_string(bw_img_noise_removed))

main()
"""


