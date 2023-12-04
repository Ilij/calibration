import os
import cv2
import numpy as np
from enum import Enum
from cameras import PBC_camera
from datetime import datetime
from collections import OrderedDict

from types import SimpleNamespace

messages = SimpleNamespace()
messages.Image = "Image"
messages.Accept = "Accept"
messages.CameraChange = "CameraChange"
messages.ModeChange = "ModeChange"
messages.StageChange = "StageChange"

modes = SimpleNamespace()
modes.Auto = "auto"
modes.Work = "work"


state_attr = SimpleNamespace()
state_attr.name = "name"
state_attr.help_link = "help_link"
state_attr.hint = "hint"
state_attr.check_image = "check_image"
state_attr.prefered_mode = "prefered_mode"
state_attr.check_success = "check_success"
state_attr.fail_check = "fail_check"
state_attr.cam_change = "cam_change"
state_attr.cam_mode_change = "cam_mode_change"
state_attr.accept = "accept"
state_attr.on_accept = "on_accept"

# Функции состояний
def save_image(stage, sn, suffix=None, image=None) -> bool:
    if not os.path.exists(f'{stage}'):
        os.mkdir(f'{stage}')
    filename = datetime.now().strftime( "_".join([s for s in [sn, "%y-%m-%d_%H-%M-%S", suffix] if s is not None]))
    cv2.imwrite(f'{stage}/{filename}.png', image)
    return True

def save_chesboard(camera: PBC_camera, images: list) -> bool:
    return save_image("chessboard", camera.serial_number, image=images[0])

def save_common(camera: PBC_camera, images: list) -> bool:
    return save_image("common", camera.serial_number, image=images[0])

def save_pallet(camera: PBC_camera, images: list) -> bool:
    return save_image("pallet", camera.serial_number, image=images[0])

def save_odometry_bind(camera: PBC_camera, images: list) -> bool:
    return save_image("odometry", camera.serial_number, image=images[0])

def save_laser_bind(camera: PBC_camera, images: list) -> bool:
    return save_image("odometry", camera.serial_number, image=images[0])

def save_offset(camera: PBC_camera, images: list) -> bool:
    return save_image("offset", camera.serial_number, image=images[0])


def KA_check_position(camera: PBC_camera, images: list) -> bool:
    return True

def KA_check_RGB_mode(camera: PBC_camera, images: list):
    return camera.mode == "RGB"

def KA_check_Laser_mode(camera: PBC_camera, images: list):
    return camera.mode == "Laser"

def KA_check_sharpness(camera: PBC_camera, images: list) -> bool:
    if camera.mode == "RGB":
        kernel = np.array([[0, -1, 0], 
                        [-1, 5, -1],
                        [0, -1, 0]])
        frame = cv2.filter2D(src=images[-1], ddepth=-1, kernel=kernel)
        return np.max(frame) > 0.5 # TODO: need update 0.5 value
    
    return False

def KA_check_chessboard(camera: PBC_camera, images: list) -> bool:
    # читаемость шахматной доски
    gray = cv2.cvtColor(images[0], cv2.COLOR_BAYER_RG2GRAY)
    ret, _ = cv2.findChessboardCornersSB(gray, (30, 23))
    return ret

def KA_check_common(camera: PBC_camera, images: list) -> bool:
    if camera.mode == "Laser":
        return True
    # наличие "лазерных полок" не с самого края кадра
    return False

def KA_check_pallet(camera: PBC_camera, images: list) -> bool:
    # наличие непрерывной лазерной отметки
    return True

def KA_check_bind_laser(camera: PBC_camera, images: list) -> bool:
    return True

def KA_check_bind_odometry(camera: PBC_camera, images: list) -> bool:
    return True


def KA_True(camera: PBC_camera, images: list) -> bool:
    return True

"""
Предположение: Возможны 5 входных сигналов:
- Текущее изображение с камеры (Image)
- Смена камеры - (Cam_switch)
- Смена режима работы камеры (Cam mode)
- Сигнал "Принять" (Gui - Accept)
- Сигнал "Сброс" (Gui - Reset)

Шаблон состояния:
{ "%Состояние%": { "name" : "%Название%", - отображается на странице
                   state_attr.help_link: "%ссылка на файл с описанием%", - загружается в фрейм
                   state_attr.hint: "%короткое напоминание что нужно делать%", - отображается на странице
                   "check_image": [%список функций для проверки входящего изображения%], - выполняются последовательно
                   state_attr.prefered_mode: "%modes: требуемый режим работы камеры (auto/work)%", - при входе переключает камеру ???
                   "check_success": "%состояние при удачной проверке%", - следующее состояние при удачной проверке
                   "fail_check": "%состояние при неудачной проверке%", - следующее состояние при неудачной провеке 
                   "cam_change": "%состояние при переключении камеры%", - следующее состояние при смене камеры 
                   "cam_mode_change": "%состояние при переключении режима работы камеры%",
                   state_attr.accept: "%состояние при применении%",
                   state_attr.on_accept: %function(cam_sn, image) - вызов функции при применении% 
}
"""
CalibrationKA = OrderedDict({ 
    "stage_setup": { 
        state_attr.name: "расстановка камер",
        state_attr.help_link: "/resources/step_0_setup_help.html",
        state_attr.hint: "расстановка камер",
        state_attr.prefered_mode: modes.Auto,
        state_attr.accept: "stage_sharpness"
    },
    "stage_sharpness" : { 
        state_attr.name: "резкость",
        state_attr.help_link: "/resources/sharpness_help.html",
        state_attr.hint: "подстройка резкости",
        state_attr.prefered_mode: modes.Auto,
        state_attr.accept: "stage_chessboard_0"
    },
    # CHESSBOARD
    "stage_chessboard_0": { 
        state_attr.name: "шахматная доска - 0",
        state_attr.help_link: "/resources/stage-1_chessboard-help.html",
        state_attr.hint: "СAM-0 съемка лазера на шахматной доске на максимальной высоте",
        state_attr.check_image: [KA_check_chessboard],
        state_attr.prefered_mode: modes.Work,
        state_attr.accept : "stage_chessboard_1",
        state_attr.on_accept: save_chesboard
    },
    "stage_chessboard_1": { 
        state_attr.name: "шахматная доска - 1",
        state_attr.help_link: "/resources/stage-1_chessboard-help.html",
        state_attr.hint: "СAM-0 съемка шахматной доски на максимальной высоте",
        state_attr.check_image: [KA_check_chessboard],
        state_attr.prefered_mode: modes.Auto,
        state_attr.accept : "stage_chessboard_2",
        state_attr.on_accept: save_chesboard
    },
    "stage_chessboard_2": { 
        state_attr.name: "шахматная доска - 2",
        state_attr.help_link: "/resources/stage-1_chessboard-help.html",
        state_attr.hint: "СAM-0 съемка лазера на шахматной доске на поддоне",
        state_attr.check_image: [KA_check_chessboard],
        state_attr.prefered_mode: modes.Work,
        state_attr.accept : "stage_chessboard_3",
        state_attr.on_accept: save_chesboard
    },
    "stage_chessboard_3": { 
        state_attr.name: "шахматная доска - 3",
        state_attr.help_link: "/resources/stage-1_chessboard-help.html",
        state_attr.hint: "СAM-0 съемка шахматной доски на поддоне",
        state_attr.check_image: [KA_check_chessboard],
        state_attr.prefered_mode: modes.Auto,
        state_attr.accept : "stage_common_0",
        state_attr.on_accept: save_chesboard
    },
    # ...
    "stage_common_0": {       
        state_attr.name: "общие снимки - 1",
        state_attr.help_link: "/resources/stage-2_common-help.html",
        state_attr.hint: "СAM-0 съемка лазера на верхней ступени",
        state_attr.prefered_mode: modes.Work,
        state_attr.check_image: [KA_check_common],
        state_attr.accept : "stage_common_1",
        state_attr.on_accept: save_common
    },
    "stage_common_1": {       
        state_attr.name: "общие снимки - 2",
        state_attr.help_link: "/resources/stage-2_common-help.html",
        state_attr.hint: "СAM-1 съемка лазера на верхней ступени",
        state_attr.prefered_mode: modes.Work,
        state_attr.check_image: [KA_check_common],
        state_attr.accept : "stage_common_2",
        state_attr.on_accept: save_common
    },
    "stage_common_2": {       
        state_attr.name: "общие снимки - 3",
        state_attr.help_link: "/stage-2_common-help.html",
        state_attr.hint: "СAM-0 съемка лазера на второй ступени",
        state_attr.prefered_mode: modes.Work,
        state_attr.check_image: [KA_check_common],
        state_attr.accept : "stage_common_3",
        state_attr.on_accept: save_common
    },
    "stage_common_3": {       
        state_attr.name: "общие снимки - 4",
        state_attr.help_link: "/stage-2_common-help.html",
        state_attr.hint: "СAM-1 съемка лазера на второй ступени",
        state_attr.prefered_mode: modes.Work,
        state_attr.check_image: [KA_check_common],
        state_attr.accept : "stage_pallet_0",
        state_attr.on_accept: save_common
    },
    # ...
    "stage_pallet_0": { 
        state_attr.name: "уровень поддона - 0",
        state_attr.help_link: "/stage-5_pallet-help.html",
        state_attr.hint: "СAM-0 съемка лазера на поддоне",
        state_attr.prefered_mode: modes.Work,
        state_attr.check_image: [KA_check_pallet],
        state_attr.accept : "stage_pallet_1",
        state_attr.on_accept: save_pallet
    },
    "stage_pallet_1": { 
        state_attr.name: "уровень поддона - 1",
        state_attr.help_link: "/stage-5_pallet-help.html",
        state_attr.hint: "СAM-1 съемка лазера на поддоне",
        state_attr.prefered_mode: modes.Work,
        state_attr.check_image: [KA_check_pallet],
        state_attr.accept : "stage_pallet_2",
        state_attr.on_accept: save_pallet
    },
    "stage_pallet_2": { 
        state_attr.name: "уровень поддона - 2",
        state_attr.help_link: "/stage-5_pallet-help.html",
        state_attr.hint: "СAM-2 съемка лазера на поддоне",
        state_attr.prefered_mode: modes.Work,
        state_attr.check_image: [KA_check_pallet],
        state_attr.accept : "stage_offset_0",
        state_attr.on_accept: save_pallet
    },
    ## OFFSET 
    "stage_offset_0" : {
        state_attr.name: "направлени движения поддона - 0",
        state_attr.help_link: "/stage-4_offset-help.html",
        state_attr.hint: "снимок начала поддона",
        state_attr.prefered_mode: modes.Auto,
        state_attr.check_image: [KA_check_chessboard],
        state_attr.accept: "stage_offset_1",
        state_attr.on_accept: save_offset
    },
    "stage_offset_1" : {
        state_attr.name: "направлени движения поддона - 1",
        state_attr.help_link: "/stage-4_offset-help.html",
        state_attr.hint: "снимок начала поддона",
        state_attr.prefered_mode: modes.Auto,
        state_attr.check_image: [KA_check_chessboard],
        state_attr.accept: "stage_odometry_0",
        state_attr.on_accept: save_offset
    },
    ## ODOMETRY
    "stage_odometry_0": {
        state_attr.name: "связываение лазерный камер с одометрией - 1",
        state_attr.help_link: "/...html",
        state_attr.hint: "снимок лазерной камеры",
        state_attr.check_image: [KA_check_chessboard],
        state_attr.prefered_mode: modes.Auto,
        state_attr.accept: "stage_odometry_1",
        state_attr.on_accept: save_odometry_bind
    },
    "stage_odometry_1": {
        state_attr.name: "связываение лазерный камер с одометрией - 2",
        state_attr.help_link: "/...html",
        state_attr.hint: "снимок камерой дефектоскопии",
        state_attr.check_image: [KA_check_chessboard],
        state_attr.prefered_mode: modes.Auto,
        state_attr.accept: "stage_odometry_2",
        state_attr.on_accept: save_odometry_bind
    },
    "stage_odometry_2": {
        state_attr.name: "связываение лазерный камер с одометрией - 3",
        state_attr.help_link: "/...html",
        state_attr.hint: "снимок камерой дефектоскопии №1",
        state_attr.check_image: [KA_check_chessboard],
        state_attr.prefered_mode: modes.Auto,
        state_attr.accept: "stage_odometry_3",
        state_attr.on_accept: save_odometry_bind
    },
    "stage_odometry_3": {
        state_attr.name: "связываение лазерный камер с одометрией - 4",
        state_attr.help_link: "/...html",
        state_attr.hint: "снимок камерой дефектоскопии №2",
        state_attr.check_image: [KA_check_chessboard],
        state_attr.prefered_mode: modes.Auto,
        state_attr.accept: "finish",
        state_attr.on_accept: save_odometry_bind
    },
    "finish": {
        state_attr.name: "Завершение",
        state_attr.help_link: "/...html",
        state_attr.hint: "Сделаны все снимки для калибровки",
        state_attr.accept: "finish",
    }
})

