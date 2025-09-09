from DataTypes import Object, Main_object
import cv2
import numpy as np
import imutils
import os
global M, maxWidth, maxHeight

contourArea_vec = np.vectorize(cv2.contourArea)

def getCotours(img,imgContour):
    contours, hierarchy = cv2.findContours(img,cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    areas = contourArea_vec(contours)
    cnt = contours[np.argmax(areas)]
    cv2.drawContours(imgContour, cnt, -1, (255, 0, 255), 7)
    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

    return approx

def warp_w_last_scale(img):
    return cv2.warpPerspective(img, M, (maxWidth, maxHeight))


def warp(img, pts):
    global M, maxWidth, maxHeight
    rect = np.zeros((4, 2), dtype="float32")

    # the top-left point has the smallest sum whereas the
    # bottom-right has the largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # compute the difference between the points -- the top-right
    # will have the minumum difference and the bottom-left will
    # have the maximum difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    # multiply the rectangle by the original ratio
    rect *= (max(img.shape)/500)

    # now that we have our rectangle of points, let's compute
    # the width of our new image
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))

    # ...and now for the height of our new image
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))

    # take the maximum of the width and height values to reach
    # our final dimensions
    maxWidth = max(int(widthA), int(widthB))
    maxHeight = max(int(heightA), int(heightB))

    # construct our destination points which will be used to
    # map the screen to a top-down, "birds eye" view
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    # calculate the perspective transform matrix and warp
    # the perspective to grab the screen
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(img, M, (maxWidth, maxHeight))

def warp_screen_img(img_orig):
    img = imutils.resize(img_orig, width=500)
    imgContour = img.copy()
    blurImg = cv2.GaussianBlur(img, (11, 11), 1)
    thresh1 = 150
    thresh2 = 250
    cannyImg = cv2.Canny(blurImg, thresh1, thresh2)

    kernel = np.ones((5, 5))
    imgDil = cv2.dilate(cannyImg, kernel, iterations=1)

    area_of_interest = getCotours(imgDil, imgContour)
    (a, b, c) = area_of_interest.shape
    area_of_interest = area_of_interest.reshape(a, 2)

    return warp(img_orig, area_of_interest)


def create_db(img_loc_l, dataset):

    if len(img_loc_l) == 0:
        return

    try:
        os.mkdir(dataset)
    except OSError as error:
        pass #print(error)

    # cv2.namedWindow("preview")
    # db =[]
    i = 0
    for img, data_l in img_loc_l:
        proc_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret3, proc_img = cv2.threshold(proc_img, 127, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        for data in data_l:
            x0, y0, x1, y1 = data.loc
            cropped = proc_img[y0:y1, x0:x1]
            # db.append([cropped, label])
            cv2.imwrite("{}/{}__{}.png".format(dataset, i, data.label), cropped)
            i += 1
            if type(data) == Main_object:

                try:
                    os.mkdir("./{}/{}".format(dataset, data.label))
                except OSError as error:
                    print(error)

                for obj in data.objects:
                    x0, y0, x1, y1 = obj.loc
                    cropped = proc_img[y0:y1, x0:x1]
                    # db.append([cropped, label])
                    cv2.imwrite("{}/{}/{}__{}.png".format(dataset, data.label, i, obj.label), cropped)
                    i += 1

            # while True:
            #     frame = cropped.copy()
            #     cv2.putText(frame, label, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            #     cv2.imshow("preview", frame)
            #
            #     # when pressed c - stop showing
            #     key = cv2.waitKey(1)
            #     if key == ord('c'):
            #         break

    # cv2.destroyWindow("preview")




