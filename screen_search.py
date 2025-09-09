# imports
import screen_reader as sr
import Init
import image_proc
import pytesseract
from pytesseract import Output


def search_on_screen():
    """
    Ask input from user of keyword they would like to search
    :return: abort - True or False to abort action, dest - found destination object
    """

    dest_loc, dest_name = None, None

    # Capture image from phone
    frame = Init.get_frame()

    # Image processing -  warp image
    # img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = image_proc.warp_w_last_scale(frame)
    data = find_all_words(img)
    # print(data["text"])  # for debug

    sr.say_print("enter word to search: ")
    chosen_word = input()

    list_of_cord = find_word(data, chosen_word)

    abort = len(list_of_cord) == 0

    if abort is False:
        dest_loc = list_of_cord[0]  # x,y,w,h
        dest_name = chosen_word
    else:
        sr.say_print(chosen_word + " was not found")

    return abort, dest_loc, dest_name


def find_all_words(img, lng='mix'):
    """
    This function finds words in image using pytesseract
    :return: Found data
    """
    
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
    if lng == 'mix':
        cong = r' --oem 3 --psm 1 -l heb+eng'
    elif lng == 'eng':
        cong = r' --oem 3 --psm 1 -l eng'
    data = pytesseract.image_to_data(img, config=cong, output_type=Output.DICT)

    return data


def find_word(data, chosen_word):

    # Create list of possible outputs for same word (errors)
    change_list = [chosen_word]
    chosen_word_1 = chosen_word.replace('ח', 'ת')  # replace ח and ת
    change_list.append(chosen_word_1)
    chosen_word_2 = chosen_word.replace('כ', 'ב')  # replace כ and ב
    change_list.append(chosen_word_2)
    chosen_word_3 = chosen_word.replace('ה', 'ב')  # replace ה and ב
    change_list.append(chosen_word_3)

    words_text_list = data["text"]
    words_text_list = [x.lower() for x in words_text_list]  # all list in lowercase

    list_of_cord = []

    for changes_word in change_list:
        for word in words_text_list:
            if changes_word in word:
                index_list = [i for i in range(len(words_text_list)) if words_text_list[i] in [word]]
                for i in index_list:
                    pos = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                    if pos not in list_of_cord:
                        list_of_cord.append(pos)

    return list_of_cord
