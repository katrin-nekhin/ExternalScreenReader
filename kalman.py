import cv2
import numpy as np
import math
import screen_reader as sr
import threading

THRESHOLD = 20

global kalman, counter, dest, pred_dest, curr_pos, check, run


def corrector():
    global dest, pred_dest, curr_pos, check, run

    while run:
        if check:
            if curr_pos[0] in range(dest[0], dest[0] + dest[2]) and curr_pos[1] in range(dest[1], dest[1] + dest[3]):
                sr.say_print("Spot")
            else:
                vector_progress = [int(pred_dest[0]) - int(curr_pos[0]), int(pred_dest[1]) - int(curr_pos[1])]
                vector_expected = [dest[0] - int(curr_pos[0]), dest[1] - int(curr_pos[1])]

                # Calculate angle between wanted and actual progress vector
                A = math.sqrt(vector_progress[0] ** 2 + vector_progress[1] ** 2)
                B = math.sqrt(vector_expected[0] ** 2 + vector_expected[1] ** 2)
                numerator = vector_progress[0] * vector_expected[0] + vector_progress[1] * vector_expected[1]
                denominator = A * B
                if denominator > 0.00001:
                    angle = math.acos(numerator / denominator)
                    if angle > 0.6 and counter == 0:
                        correction = place_me(curr_pos, vector_expected, vector_progress, dest)
                        if correction != "":
                            sr.say_print(correction)
            check = False
    sr.say_print("Page changed")


def place_me(curr_pos, expected_vec, actual_vec, final_dest):
    correction = ""
    fin_left_X = final_dest[0]
    fin_right_X = final_dest[0] + final_dest[2]
    fin_up_Y = final_dest[1]
    fin_down_Y = final_dest[1] + final_dest[3]

    if actual_vec[0] != 0:
        actual_slope = actual_vec[1] / actual_vec[0]
        expected_slope = expected_vec[1] / expected_vec[0]

        if int(curr_pos[0]) < int(fin_left_X) and int(curr_pos[1]) < int(fin_up_Y):
            if abs(actual_slope) > abs(expected_slope):
                correction = "right"
            else:
                correction = "down"
        elif int(curr_pos[0]) > int(fin_right_X) and int(curr_pos[1]) > int(fin_down_Y):
            if abs(actual_slope) > abs(expected_slope):
                correction = "left"
            else:
                correction = "up"
        elif int(curr_pos[0]) > int(fin_right_X) and int(curr_pos[1]) < int(fin_up_Y):
            if abs(actual_slope) > abs(expected_slope):
                correction = "left"
            else:
                correction = "down"
        elif int(curr_pos[0]) < int(fin_left_X) and int(curr_pos[1]) > int(fin_down_Y):
            if abs(actual_slope) > abs(expected_slope):
                correction = "right"
            else:
                correction = "up"
    return correction


def kalman_init(dest_in):
    global kalman, counter, dest, check, run

    counter = 0
    check = False
    run = True
    dest = dest_in
    kalman = cv2.KalmanFilter(4, 2)
    kalman.measurementMatrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], np.float32)
    kalman.transitionMatrix = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32)
    kalman.processNoiseCov = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32) * 0.03

    t1 = threading.Thread(target=corrector, args=[])
    t1.start()
    return t1


def kalman_predict(pos):
    global counter, dest, pred_dest, curr_pos, check

    x, y = pos

    counter = 0

    curr_pos = np.array([[np.float32(x)], [np.float32(y)]])
    kalman.correct(curr_pos)
    pred_dest = kalman.predict()
    check = True


def kalman_stop():
    global run
    run = False

