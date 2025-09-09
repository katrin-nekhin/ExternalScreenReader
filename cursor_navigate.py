import cv2
import imutils

import Init
import image_proc
import numpy as np
import kalman as kal
import requests

import screen_reader

logger = None
itter = None
dest = []

MAX_FEATURES = 500
GOOD_MATCH_PERCENT = 0.15
RADIUS = 40
RE_WIDTH = 1000


def frame_slicing(location, limits):
    """
    This function slices the frame to narrow down the options.
    :return: cursor's location
    """
    x1, x2, y1, y2 = (location[0] - RADIUS), (location[0] + location[2] + RADIUS), (location[1] - RADIUS), (location[1] + location[3] + RADIUS)
    return max(x1, 0), min(x2, limits[1]), max(y1, 0), min(y2, limits[0])

def locate_cursor(curr_frame, prev_frame, prev_loc):
    """
    Located cursor in a particular slice in the frame.
    :return: cursor's location
    """
    x, y, w, h = None, None, None, None

    # compute the absolute difference between the current frame and previous frame
    if prev_loc is None:
        x1, y1 = 0, 0
        prev_temp = imutils.resize(prev_frame, width=500)
        curr_temp = imutils.resize(curr_frame, width=500)
    else:
        x1, x2, y1, y2 = frame_slicing(prev_loc, curr_frame.shape)
        prev_temp = prev_frame[y1:y2, x1:x2]
        curr_temp = curr_frame[y1:y2, x1:x2]

    frameDelta = cv2.absdiff(prev_temp, curr_temp)

    thresh = cv2.threshold(frameDelta, 30, 255, cv2.THRESH_BINARY)[1]

    # dilate the thresholded image to fill in holes, then find contours on thresholded image
    thresh = cv2.dilate(thresh, None, iterations=2)

    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    # If more than 3 objects detected - say page changed and quit navigation
    if len(cnts) > 6:
        return x, y, w, h, True

    elif len(cnts) > 0:

        # compute the bounding box for the contour
        (x, y, w, h) = cv2.boundingRect(cnts[0])
        x, y = (x + x1), (y + y1)

        if prev_loc is None:
            x, y = int(x*RE_WIDTH/500), int(y*RE_WIDTH/500)
    else:
        x, y, w, h = None, None, None, None

    return x, y, w, h, False


def capNproc(first_iter=False):
    """
    This function captures and processes image
    :return: processed image
    """
    global dest
    # Capture image from phone
    frame = Init.get_frame()

    # Frame wrap resize
    frame = image_proc.warp_w_last_scale(frame)
    if first_iter:
        h, w = frame.shape[:2]
        dest = [int(x * (RE_WIDTH/w)) for x in dest]

    frame = imutils.resize(frame, width=RE_WIDTH)
    frame = cv2.rectangle(frame, (dest[0], dest[1]), (dest[0] + dest[2], dest[1] + dest[3]), (255, 0, 0), 2)

    # Convert frame image to gray and blured
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    return gray, frame


def navigation_Init():
    """
    Navigation initialization function
    :return: None
    """
    global speach_thread, dest

    speach_thread = kal.kalman_init(dest)
    cv2.namedWindow("preview")



def navigate2dest(dest_in):
    """
    Main navigation function, sets the destination
    :return: None
    """
    global speach_thread, dest

    # Init
    dest = dest_in

    prev_gray_frame, temp = capNproc(True)  # Save frame as (next) prev_gray_frame
    navigation_Init()
    prev_loc = None

    while True:

        if not speach_thread.is_alive():
            break

        gray, colored_gray = capNproc()

        # For visual show
        if prev_loc is not None:
            x1, x2, y1, y2 = (prev_loc[0] - RADIUS), (prev_loc[0] + prev_loc[2] + RADIUS), (prev_loc[1] - RADIUS), (prev_loc[1] + prev_loc[3] + RADIUS)
        else:
            x1, x2, y1, y2 = 0, colored_gray.shape[1], 0, colored_gray.shape[0]

        cv2.rectangle(colored_gray, (x1, y1), (x2, y2), (0, 0, 255), 2)

        # Locate cursor on screen
        x, y, w, h, abort = locate_cursor(gray, prev_gray_frame, prev_loc)

        if abort:
            kal.kalman_stop()
            break

        if x is not None and y is not None:

            prev_loc = (x, y, w, h)
            cv2.rectangle(colored_gray, (x, y), (x + w, y + h), (0, 255, 0), 2)

            kal.kalman_predict((x, y))

        else:
            prev_loc = None

        # Save gray as (next) prev_gray_frame
        prev_gray_frame = gray

        # show the frame. Quit if the user presses a key
        cv2.imshow("preview", colored_gray)

        key = cv2.waitKey(1)
        if key == ord('q'):  # exit on ESC
            input("Press Enter to continue...")

    cv2.destroyWindow("preview")

    return
