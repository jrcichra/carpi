from karmen import Karmen
import threading
import queue
import logging
import time
import os
import datetime
from common import isCI

if isCI():
    import mockcamera as picamera
else:
    import picamera
##get_new_filename##
camera = None


def getserial():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        f = open("/proc/cpuinfo", "r")
        for line in f:
            if line[0:6] == "Serial":
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"

    return cpuserial


def get_new_filename():
    return (
        "travel__"
        + datetime.datetime.now().strftime("%Y--%m--%d__%H--%M--%S")
        + "__"
        + str(getserial())
        + ".h264"
    )


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)d:LINE %(lineno)d:TID %(thread)d:%(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)


def start_preview(params, result):
    logging.info("Starting the preview...")
    try:
        global camera
        # Cheat and place the preview inside a window that the GUI will have a black box around
        camera.start_preview(fullscreen=False, window=(100, 100, 400, 600))
        # camera.start_preview()
        # The preview alpha has to be set after the preview is already active
        camera.preview.alpha = 128
    except Exception as e:
        logging.error(e)
        result.code = 500
    result.code = 200


def stop_preview(params, result):
    logging.info("Stopping the preview...")
    try:
        global camera
        camera.stop_preview()
    except Exception as e:
        logging.error(e)
        result.code = 500
        return
    result.code = 200


def start_recording(params, result):
    logging.info(f"params for start_recording are: {params}")
    HRES = int(params.get("hres", 1280))
    VRES = int(params.get("vres", 720))
    ROT = int(params.get("rot", 0))
    FRAMERATE = int(params.get("framerate", 10))
    logging.info("Starting the recording...")
    # try:
    global camera
    # Do all the camera setup
    camera = picamera.PiCamera()  # the camera object
    camera.resolution = (HRES, VRES)
    # annotations
    camera.annotate_foreground = picamera.Color("white")
    camera.annotate_background = picamera.Color("black")
    camera.annotate_frame_num = True
    camera.annotate_text_size = 48
    camera.annotate_text = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    # set the framerate
    camera.framerate = FRAMERATE
    # set the rotation
    camera.rotation = ROT
    try:
        camera.start_recording(f"/recordings/{get_new_filename()}", sps_timing=True)
    except Exception as e:
        logging.error(e)
        result.code = 500
        return
    # spawn a thread that handles updating the time/frame counter
    threading.Thread(target=update_annotations).start()
    result.code = 200


def stop_recording(params, result):
    logging.info("Stopping the recording...")
    try:
        global camera
        camera.stop_recording()
        camera.close()
    except Exception as e:
        logging.error(e)
        result.code = 500
        return
    result.code = 200


def update_annotations():
    global camera
    while True:
        try:
            camera.annotate_text = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        except Exception as e:
            logging.error(e)
            break
        time.sleep(0.2)


###MAIN###
k = Karmen(hostname="karmen")
k.addAction(start_recording, "start_recording")
k.addAction(stop_recording, "stop_recording")
k.addAction(start_preview, "start_preview")
k.addAction(stop_preview, "stop_preview")
k.register()

while True:
    time.sleep(10)
