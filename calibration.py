# Intrinsic calibration
from glob import glob
import numpy as np
from tqdm import tqdm
import cv2
import os 

save_fld = 'saved_images/intrinsik_10-10-23/'
imgs_paths = glob(os.path.join(save_fld, '*.bmp'))

cameras_imgs = {}
for img_path in imgs_paths:
    cam_id = os.path.basename(img_path).split('_')[0]
    if cam_id not in cameras_imgs:
        cameras_imgs[cam_id] = []
    cameras_imgs[cam_id].append(img_path)
    
objp = np.zeros((30*23,3), np.float32)
objp[:,:2] = np.mgrid[0:30,0:23].T.reshape(-1,2)
objp *= 10
calibration_result = {}
for cam_id, img_paths in cameras_imgs.items():
    imgpoints = []
    objpoints = []
    for img_path in tqdm(img_paths):
        img = cv2.imread(img_path, 0)
        img = cv2.cvtColor(img, cv2.COLOR_BAYER_RG2GRAY)
        ret, corners = cv2.findChessboardCornersSB(img, (30, 23))
        if ret == True:
            objpoints.append(objp)
            imgpoints.append(corners)
        elif img.mean() > 10:
            print('no points')
        else:
            print('dark')
#             print('ERRROR', img_path)
    print(imgpoints, objpoints)
    print('calibrating...', cam_id)
    print(img.shape[::-1])
    if imgpoints:
        calibration_result[cam_id] = (cv2.calibrateCamera(objpoints, imgpoints, img.shape[::-1], None, None))

matrix_save_fld = './matrices/'
for cam_id, calib in calibration_result.items():
    _, mtx, dist, _, _ = calib
    np.savez(os.path.join(matrix_save_fld, '{}_camera_matrix.npz'.format(cam_id)), mtx)
    np.savez(os.path.join(matrix_save_fld, '{}_dist.npz'.format(cam_id)), dist)
    print(os.path.join(matrix_save_fld, '{}_camera_matrix.npz'.format(cam_id)))
    print(os.path.join(matrix_save_fld, '{}_dist.npz'.format(cam_id)))


#extrinsic calibration