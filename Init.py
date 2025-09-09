import cv2
import requests
import numpy as np
import imutils
import validators

import screen_reader
import image_proc

url = ""


def cam_calib(mode='u'):
    """
    Camera calibration.
    input:
    u - calibration on start (returns url)
    f - calibration for database creation (returns frame)
    :return:
    url when mode='u'
    final frame when mode='f'
    """
    global url

    if mode == 'u':
        set_url()

    # Set preview window
    cv2.namedWindow("preview")

    while True:

        # Capture image from phone
        full_frame = get_frame()

        # preview camera shot
        frame = image_proc.warp_screen_img(full_frame)
        frame = imutils.resize(frame, width=1500)
        cv2.imshow("preview", frame)

        # when pressed q - quit calibration
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    cv2.destroyWindow("preview")

    if mode == 'u':
        return url
    elif mode == 'f':
        return full_frame


def get_frame():
    """
    This function captured image from phone
    :return: Captured image
    """
    img_resp = requests.get(url)
    img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
    frame = cv2.imdecode(img_arr, -1)

    return frame


def set_url():
    """
    This function sets camera's url
    """
    global url
    valid = False

    while not valid:
        # Get camera url from user
        screen_reader.say_print("Enter IP address used by camera: http://")
        ip_num = input()
        url = "http://" + ip_num + "/shot.jpg"

        valid = validators.url(url)

        if not valid:
            screen_reader.say_print("IP address not valid")
        else:
            try:
                requests.get(url)
            except:
                screen_reader.say_print("Something went wrong, try again")
                valid = False
