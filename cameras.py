from abc import abstractmethod
import cv2


class PBC_camera():
    dummy_image = cv2.imread('resources/no-image.png', cv2.IMREAD_COLOR)
    last_image = dummy_image

    def __init__(self, serial_number) -> None:
        self.serial_number = serial_number
        self.camera = None
        self.last_image = None
        self.mode = "auto"

    @staticmethod   
    def enumerate_cameras()->dict:
        return dict()


    @staticmethod
    @abstractmethod
    def vendor():
        pass


    @abstractmethod
    def start(self):
        pass


    @abstractmethod
    def stop(self):
        pass


    @abstractmethod
    def isGrabbing(self) -> bool:
        pass


    @abstractmethod
    def grab(self, timeout):
        return self.dummy_image


# class property:
#     pget: Callable[[Any], Any] | None
#     pset: Callable[[Any, Any], None] | None
#     pwritable: Callable[]

#     __isabstractmethod__: bool
#     def __init__(
#         self,
#         fget: Callable[[Any], Any] | None = ...,
#         fset: Callable[[Any, Any], None] | None = ...,
#         fdel: Callable[[Any], None] | None = ...,
#         doc: str | None = ...,
#     ) -> None: ...
#     def getter(self, __fget: Callable[[Any], Any]) -> property: ...
#     def setter(self, __fset: Callable[[Any, Any], None]) -> property: ...
#     def deleter(self, __fdel: Callable[[Any], None]) -> property: ...
#     def __get__(self, __instance: Any, __owner: type | None = None) -> Any: ...
#     def __set__(self, __instance: Any, __value: Any) -> None: ...
#     def __delete__(self, __instance: Any) -> None: ...

    

# class Feature:
#     def __init__(self, handle, feature):
#         """
#         :param  handle:      The handle of the device
#         :param  feature:     The feature code ID
#         """
#         self.__handle = handle
#         self.__feature = feature
#         self.feature_name = self.get_name()

#     def get_name(self):
#         """
#         brief:  Getting Feature Name
#         return: Success:    feature name
#                 Failed:     convert feature ID to string
#         """
#         status, name = gx_get_feature_name(self.__handle, self.__feature)
#         if status != GxStatusList.SUCCESS:
#             name = (hex(self.__feature)).__str__()

#         return name

#     def is_implemented(self):
#         """
#         brief:  Determining whether the feature is implemented
#         return: is_implemented
#         """
#         status, is_implemented = gx_is_implemented(self.__handle, self.__feature)
#         if status == GxStatusList.SUCCESS:
#             return is_implemented
#         elif status == GxStatusList.INVALID_PARAMETER:
#             return False
#         else:
#             StatusProcessor.process(status, 'Feature', 'is_implemented')

#     def is_readable(self):
#         """
#         brief:  Determining whether the feature is readable
#         return: is_readable
#         """
#         implemented = self.is_implemented()
#         if not implemented:
#             return False

#         status, is_readable = gx_is_readable(self.__handle, self.__feature)
#         StatusProcessor.process(status, 'Feature', 'is_readable')
#         return is_readable

#     def is_writable(self):
#         """
#         brief:  Determining whether the feature is writable
#         return: is_writable
#         """
#         implemented = self.is_implemented()
#         if not implemented:
#             return False

#         status, is_writable = gx_is_writable(self.__handle, self.__feature)
#         StatusProcessor.process(status, 'Feature', 'is_writable')
#         return is_writable