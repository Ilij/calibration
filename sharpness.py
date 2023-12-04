import cv2
import numpy as np

def sharpness(img):
    kernel = np.array([[0, -1, 0], 
                       [-1, 5, -1],
                       [0, -1, 0]])
    frame = cv2.filter2D(src=img, ddepth=-1, kernel=kernel)
    return np.max(frame)

