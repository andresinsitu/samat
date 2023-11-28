import numpy as np
import cv2
import os

def create_mask(image_path: str, autoseg_path: str, threshold: int):
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    #filtro gaussiano
    #img  = cv2.GaussianBlur(img_gray,(5,5),0)

    ret,img = cv2.threshold(img,threshold,255,cv2.THRESH_BINARY)

    img = np.uint8(img)

    cv2.imwrite(autoseg_path, img)