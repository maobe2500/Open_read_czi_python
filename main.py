import os

import czifile
from czifile import CziFile

from GUI.YLHStudioGUI import YLHStudio
import tifffile as tf


def main():
    YLHS = YLHStudio()
    #p = "TESING\\test.tif"
    #c = "C:\\Users\\maobe\\OneDrive\\Dokument\\MATLAB\\Yumi_stuff\\Open_read_czi_python\\TESING\\2022_11_14__2239-1.czi"
    #c1 = "C:\\Users\\maobe\\OneDrive\\Dokument\\MATLAB\\Yumi_stuff\\Open_read_czi_python\\TESING\\2022_11_14__2239.czi"
    #c_mdim = "C:\\Users\\maobe\\OneDrive\\Dokument\\MATLAB\\Yumi_stuff\\Open_read_czi_python\\TESING\\2022_11_14__2239-1.czi"
    #YLHS.save_image_with_label("C:\\Users\\maobe\\OneDrive\\Dokument\\MATLAB\\Yumi_stuff\\Open_read_czi_python\\TESING\\2022_11_14__2239.czi", "TESING\\test.tif")
    #print("\n############ CZI #############\n")
    #with CziFile(c1) as cf:
    #    print(cf.shape, cf.dtype, cf.axes)

        #czifile.czi2tif(c, p)  # Save
    #with CziFile(c1) as cf:
    #    print(cf.shape, cf.dtype)
        #czifile.czi2tif(c, p)  # Save
    #print("\n############ TIFF #############\n")
    #with tf.TiffFile(p) as tif:
    #    for page in tif.pages:
    #        print(page.dtype)
    #        print(page.shape)
    #        print(page)

    YLHS.mainloop()

if __name__ == "__main__":
    main()
