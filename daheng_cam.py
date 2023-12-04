import cameras
import gxipy as gx


def Daheng_callback_service(callback_function):
    def Daheng_callback_service_decorator(function):
        def wrapper(raw_image):
            return callback_function(function(raw_image))
        return wrapper
    return Daheng_callback_service_decorator


def Daheng_capture_callback(raw_image:gx.RawImage):
    rgb_image = raw_image.convert("RGB")
    if rgb_image is None:
        print('Failed to convert RawImage to RGBImage')
        return None
    return rgb_image.get_numpy_array()


class Daheng_camera(cameras.PBC_camera):
    factory = gx.DeviceManager()

    def __init__(self, serial_number) -> None:
        super().__init__(serial_number=serial_number)
        self.camera: gx.Device = self.factory.open_device_by_sn(serial_number)
        self._isGrabbing = False
        self.mode = "RGB"                
        self.camera.TriggerMode.set(0)
        self.camera.data_stream[0].StreamBufferHandlingMode.set(3)


    @staticmethod
    def enumerate_cameras():
        dev_num, dev_info_list = __class__.factory.update_device_list()
        if dev_num == 0:
            return []
        return [dev['sn'] for dev in dev_info_list]

    @staticmethod
    def vendor():
        return "Daheng"

    def start(self):
        self._isGrabbing = True
        self.camera.stream_on()


    def stop(self):        
        self._isGrabbing = False
        self.camera.stream_off()


    def isGrabbing(self) -> bool:
        return self._isGrabbing


    def grab(self, timeout):
        raw_image: gx.RawImage = self.camera.data_stream[0].get_image(timeout)
        if raw_image is None:
            return super(Daheng_camera, self).grab(timeout)
        rgb_image = raw_image.convert("RGB")
        return rgb_image.get_numpy_array()

