import cameras
from pypylon import pylon

converter = pylon.ImageFormatConverter()
converter.OutputPixelFormat = pylon.PixelType_BGR8packed
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

class ImageEventHandler(pylon.ImageEventHandler):
    def __init__(self, callback, *args):
        self.callback =  callback
        super().__init__(*args)


    def OnImageGrabbed(self, camera: pylon.InstantCamera, grabResult: pylon.GrabResult):
        self.callback( grabResult.GetArray())
        return super().OnImageGrabbed(camera, grabResult)


class Basler_camera(cameras.PBC_camera):
    factory = pylon.TlFactory.GetInstance()

    def __init__(self, serial_number) -> None:
        super().__init__(serial_number=serial_number)
        for device in __class__.factory.EnumerateDevices():
            if device.GetSerialNumber() == serial_number:
                self.camera = pylon.InstantCamera()
                self.camera.Attach(__class__.factory.CreateDevice(device))
                self.camera.Open()
                self.mode = "RGB"                
                return
        raise Exception(f"Can't find camera with serial number: {serial_number}")


    @staticmethod
    def enumerate_cameras():
        return [x.GetSerialNumber() for x in __class__.factory.EnumerateDevices()]

    @staticmethod
    def vendor():
        return "Basler"

    def start(self):
        self.camera.StartGrabbing()


    def stop(self):
        self.camera.StopGrabbing()


    def isGrabbing(self) -> bool:
        return self.camera.IsGrabbing()


    def grab(self, timeout):
        global converter
        try:
            grabResult: pylon.GrabResult = self.camera.RetrieveResult(timeout)
            # grabResult: pylon.GrabResult = self.camera.RetrieveResult(timeout, pylon.TimeoutHandling_ThrowException)
            if grabResult.GrabSucceeded():
                return converter.Convert(grabResult).GetArray()
            else:
                raise Exception
        except:
            return super(Basler_camera, self).grab(timeout)
