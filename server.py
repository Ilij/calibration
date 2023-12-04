import argparse
import asyncio
import json
import logging
import os
import ssl
import cv2
from threading import Thread
from time import sleep
from collections import  defaultdict

from aiohttp import web
from aiohttp.web_request import Request
from aiortc import (VideoStreamTrack, 
                    RTCDataChannel,
                    RTCPeerConnection, 
                    RTCSessionDescription)
from aiortc.rtcrtpsender import RTCRtpSender
from av import VideoFrame

from cameras import PBC_camera
import daheng_cam
import basler_cam
import hikvision_cam

from KA import CalibrationKA, state_attr, messages
import json 
import janus

# Attention: Add camera vendors HERE
cam_vendor_list = [daheng_cam.Daheng_camera,
                   basler_cam.Basler_camera]# ,
                #    hikvision_cam.Hikvision_camera]

ROOT = os.path.dirname(__file__)
routes = web.RouteTableDef()

# GLOBALS
capture_last_frame_storage = dict()
current_stage = "stage_setup"
current_device_sn = None
pcs = dict()

def grab_thread(cam_id, camera:PBC_camera, app):
    global capture_last_frame_storage
    while not 'queue' in app:
        sleep(1)
    sync_q = app['queue'].sync_q
    print(f"Start grabbing trheed for camera: {cam_id}...\n")
    try:
        while True:
            if camera.isGrabbing(): 
                image = camera.grab(10000)
                capture_last_frame_storage[cam_id] = image
                if sync_q.empty():
                    sync_q.put((messages.Image, image))
            else:
                sleep(0.1)
    except Exception as e:
        print(f"Except {e} on cam {cam_id}: {camera}")


class StreamVideoTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()  # Initialize the base class
        # TODO: move to PBC_camera (a la mode)
        self.crop_x = 0.25
        self.crop_y = 0.25
        self.crop_w = 0.5
        self.crop_h = 0.5

    async def recv(self):
        global capture_last_frame_storage, current_device_sn
        pts, time_base = await self.next_timestamp()
        image = capture_last_frame_storage.get(current_device_sn, PBC_camera.dummy_image)
        # crop
        # cx = int(image.shape[1] * self.crop_x)
        # cy = int(image.shape[0] * self.crop_y)
        # cw = int(image.shape[1] * self.crop_w)
        # ch = int(image.shape[0] * self.crop_h)
        # image = image[cy:cy+ch, cx:cx+cw]
        frame = cv2.resize(image, (480, 320), interpolation=cv2.INTER_NEAREST)
        frame = VideoFrame.from_ndarray(frame, format="rgb24")
        frame.pts = pts
        frame.time_base = time_base
        return frame

def force_codec(pc, sender, forced_codec):
    kind = forced_codec.split("/")[0]
    codecs = RTCRtpSender.getCapabilities(kind).codecs
    transceiver = next(t for t in pc.getTransceivers() if t.sender == sender)
    transceiver.setCodecPreferences(
        [codec for codec in codecs if codec.mimeType == forced_codec]
    )

# ROUTES

@routes.get('/')
async def index(request: Request):
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


@routes.post('/switch_camera')
async def switch_camera(request: Request):    
    global current_device_sn
    select_camera_sn = await request.text()
    if select_camera_sn != current_device_sn:
        devices_descriptions[current_device_sn].stop()
        current_device_sn = select_camera_sn
        devices_descriptions[current_device_sn].start()
        await request.app['queue'].async_q.put((messages.CameraChange, select_camera_sn))
    return web.Response(status=200)


@routes.post('/switch_mode')
async def switch_mode(request: Request):    
    mode = await request.text();
    await request.app["queue"].async_q.put((messages.ModeChange, mode));
    return web.Response(status=200)


@routes.post('/switch_stage')
async def switch_mode(request: Request):    
    stage = await request.text()
    await request.app["queue"].async_q.put((messages.StageChange, stage))
    return web.Response(status=200)


@routes.post('/accept')
async def accept(request:Request):
    await request.app["queue"].async_q.put((messages.Accept, None))
    return web.Response(status=200)


def responce_state(app:web.Application):
    global current_device_sn, current_stage

    cameras = defaultdict(list)
    for sn, mnfc in sorted(app["devices_descriptions"].items()):
        cameras[mnfc.vendor()].append(sn)

    ka = app["KA"]
    return {
        "cameras": cameras,
        "current_device" : current_device_sn,
        "current_device_mode" : app["devices_descriptions"][current_device_sn].mode,
        "stage" : current_stage,
        "acceptable": state_attr.accept in ka[current_stage],
        "KA": {v["name"]:k  for k, v in ka.items() if state_attr.help_link in v},
        **{ k: v for k, v in ka[current_stage].items() if k in [state_attr.name,
                                                                state_attr.help_link,
                                                                state_attr.hint,
                                                                state_attr.prefered_mode]}}

@routes.post('/config')
async def fetch_state(request:Request):
    return web.json_response( responce_state(request.app))

async def send_pings(channel, message):
    # while True:
    channel.send(message)


## WEBRTC 
@routes.post('/offer')
async def offer(request: Request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc:RTCPeerConnection = RTCPeerConnection()
    # pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState in ["failed", "closed"]:
            await pc.close()
            # pcs.discard(pc)
            pcs.pop(pc, None)

    @pc.on("datachannel")
    def on_datachannel(channel):
        global pcs
        pcs[pc] = channel
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send(f"client datachannel message {message}")

        @channel.on("open")
        def on_open():
            print("datachannel is open - send current state")
            channel.send(responce_state(request.app))
    

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        if pc.iceConnectionState == "failed":
            await pc.close()
            # pcs.discard(pc)
            pcs.pop(pc, None)

    # open media source
    video_track: StreamVideoTrack = StreamVideoTrack()
    if video_track:
        video_sender = pc.addTrack(video_track)
        if args.video_codec:
            force_codec(pc, video_sender, args.video_codec)
        elif args.play_without_decoding:
            raise Exception("You must specify the video codec using --video-codec")

    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )

pcs = dict()

async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc, _ in pcs.items()]
    await asyncio.gather(*coros)
    pcs.clear()

# KA
class KA_Exception(Exception):
    pass

async def KA(app:web.Application):
    global current_stage, current_device_sn
    ka = app['KA']
    queue = app["queue"].async_q
    while True:
        try:
            message, body = await queue.get()
            brodcast_message = "no changes"
            current_state: dict = ka[current_stage] 
            current_image = capture_last_frame_storage[current_device_sn]
            current_camera = app["devices_descriptions"][current_device_sn]
            if message != messages.Image:
                print(f"KA message: {message}")
            if message == messages.Image:
                if state_attr.check_image in current_state:
                    for fnc in current_state[state_attr.check_image]:
                        if not fnc(current_camera, body):
                            raise KA_Exception()
                if state_attr.check_success in current_state:
                    current_stage = current_state[state_attr.check_success]
                    brodcast_message = json.dumps(responce_state(app))
            elif message == messages.Accept:
                if state_attr.accept in current_state and current_state[state_attr.accept]:
                    if state_attr.on_accept in current_state and current_state[state_attr.on_accept]:
                        current_state[state_attr.on_accept](current_camera, current_image)
                    current_stage = current_state[state_attr.accept]
                brodcast_message = json.dumps(responce_state(app))
            elif message == messages.CameraChange:
                if state_attr.cam_change in current_state and current_state[state_attr.cam_change]:
                    current_stage = current_state[state_attr.cam_change]
                brodcast_message = json.dumps(responce_state(app))
            elif message == messages.ModeChange:
                if state_attr.cam_mode_change in current_state and current_state[state_attr.cam_mode_change]:
                    current_stage = current_state[state_attr.cam_mode_change]
                brodcast_message = json.dumps(responce_state(app))
            elif message == messages.StageChange:
                if body in ka:
                    current_stage = body
                brodcast_message = json.dumps(responce_state(app))
            else:
                print(f"unknown message: {message}")
                continue
                
        except KeyError:
            print(f'KA: key error')
        except KA_Exception:
            if state_attr.fail_check in current_state and current_state[state_attr.fail_check]:
                current_stage = current_stage[state_attr.fail_check]
        except janus.AsyncQueueEmpty:
            pass
        except Exception as e: 
            print(e)

        for dc in app['pcs'].values():
            dc.send(brodcast_message)
        await asyncio.sleep(0.1)


async def start_background_tasks(app):
    app['queue'] = janus.Queue()
    app['KA_task'] = asyncio.get_event_loop().create_task(KA(app))

    for sn, device  in app['devices_descriptions'].items():
        Thread(target=grab_thread, args=( sn, 
                                          device,
                                          app)).start()


async def cleanup_background_tasks(app):
    app['KA_task'].cancel()
    await app['KA_task']
    app.on_cleanup.append(cleanup_background_tasks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cameras calibration tools")
    parser.add_argument("--cert-file", help="SSL certificate file (for HTTPS)")
    parser.add_argument("--key-file", help="SSL key file (for HTTPS)")
    parser.add_argument(
        "--play-without-decoding",
        help=(
            "Read the media without decoding it (experimental). "
            "For now it only works with an MPEGTS container with only H.264 video."
        ),
        action="store_true",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port for HTTP server (default: 8080)"
    )
    parser.add_argument("--verbose", "-v", action="count")
    parser.add_argument(
        "--video-codec", default="video/H264", help="Force a specific video codec (e.g. video/H264)"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    if args.cert_file:
        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(args.cert_file, args.key_file)
    else:
        ssl_context = None

    devices_descriptions = dict()

    for mnfs in cam_vendor_list:
        for sn in mnfs.enumerate_cameras():
            print(f"founded camera {sn} of {mnfs.vendor()}")
            devices_descriptions[sn] = mnfs(sn)

    app = web.Application()
    # Start grabbing the first camera
    current_device_sn = list(devices_descriptions.keys())[0]
    devices_descriptions[current_device_sn].start()

    app['pcs'] = pcs
    app['devices_descriptions'] = devices_descriptions
    app['KA'] = CalibrationKA
    app.on_startup.append(start_background_tasks)
    app.on_shutdown.append(on_shutdown)
    app.add_routes(routes)
    app.add_routes([web.static('/resources', 'resources')])
    web.run_app(app, host=args.host, port=args.port, ssl_context=ssl_context)
