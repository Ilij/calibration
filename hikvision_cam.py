import cameras
import sys
sys.path.append("./MvImport")
from MvCameraControl_class import *
from ctypes import *
import numpy as np

class Hikvision_camera(cameras.PBC_camera):
    
    @staticmethod
    def get_hik_serial_number(dev_info):
        serial_number = ''
        for p in dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
            if p == 0:
                break
            serial_number += chr(p)
        return serial_number

    @staticmethod
    def _inner_enumerator() -> dict:
        deviceList = MV_CC_DEVICE_INFO_LIST()
        tlayerType = MV_USB_DEVICE
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
        if ret != 0:
            print ("enum devices fail! ret[0x%x]" % ret)
            return {}
        if deviceList.nDeviceNum == 0:
            print ("find no device!")
            return {}
        return {Hikvision_camera.get_hik_serial_number(cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents): cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents for i in range(0, deviceList.nDeviceNum)}

    def __init__(self, serial_number) -> None:
        super().__init__(serial_number=serial_number)
        self.camera = MvCamera()
        mvcc_dev_info = Hikvision_camera._inner_enumerator()[serial_number]
        self.camera.MV_CC_CreateHandle(mvcc_dev_info)
        ret = self.camera.MV_CC_OpenDevice(MV_ACCESS_Control, 0)
        if ret != 0:
            print ("open device fail! ret[0x%x]" % ret)
            sys.exit()

        stParam =  MVCC_INTVALUE()
        memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))

        ret = self.camera.MV_CC_GetIntValue("PayloadSize", stParam)
        if ret != 0:
            print ("get payload size fail! ret[0x%x]" % ret)
            sys.exit()
        self.nPayloadSize = stParam.nCurValue
        self.data_buf = (c_ubyte * self.nPayloadSize)()

    @staticmethod
    def enumerate_cameras():
        return Hikvision_camera._inner_enumerator().keys()
   
 
    @staticmethod
    def vendor():
        return "Hikrobot"


    def start(self):
        self._isGrabbing = True
        self.camera.MV_CC_StartGrabbing()


    def stop(self):
        self._isGrabbing = False
        self.camera.MV_CC_StopGrabbing()


    def grab(self, timeout):
        stFrameInfo = MV_FRAME_OUT_INFO_EX()
        memset(byref(stFrameInfo), 0, sizeof(stFrameInfo))
        ret = self.camera.MV_CC_GetOneFrameTimeout(self.data_buf, self.nPayloadSize, stFrameInfo, timeout)
        if ret != 0:
            return super(Hikvision_camera, self).grab(timeout)
        height = stFrameInfo.nHeight
        width = stFrameInfo.nWidth
        return np.reshape(np.frombuffer(buffer=self.data_buf, dtype=uint8_t).copy(), (height, width))

