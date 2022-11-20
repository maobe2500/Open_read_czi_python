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
