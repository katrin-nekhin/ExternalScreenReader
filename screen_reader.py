import Init
import image_proc
import screen_search as ss
from DataTypes import Object
import cv2
import glob
import pyttsx3
from os import path

global Proj_Data_d
Proj_Data_d = {}

# Initiate TTS
engine = pyttsx3.init()
engine.setProperty("rate", 180)  # setting new voice rate slower
engine.setProperty("voice", engine.getProperty("voices")[1].id)  # set another voice


def set_data(dataset_name):
    """
    This function loads dataset into the program in the following format:

    Proj_Data_d is a dictionary of main objects where:
    Key = object's label
    Value = list of [template image, dictionary of sub objects (if the main object is a section)]

    The dictionary of sub objects is of the following format:
    Key = sub object's label
    Value = template image
    """

    global Proj_Data_d
    Proj_Data_d = {}

    # This loop runs over all images (objects) in the chosen dataset path
    for templ_path in glob.glob("./{}/*.png".format(dataset_name)):

        # Extract template name from image name
        t, templ_name = templ_path.split("__")
        label = templ_name[0:-4]

        # Load template image
        templ = cv2.imread(templ_path, 0)

        # If the object is a section, load objects in the section as sub dictionary under same key
        obj_d = {}
        exists = path.exists("./{}/{}".format(dataset_name, label))
        if exists:
            for innr_templ_path in glob.glob("./{}/{}/*.png".format(dataset_name, label)):

                # Extract template name from image name
                t, templ_name = innr_templ_path.split("__")
                innr_label = templ_name[0:-4]

                # Load template image
                innr_templ = cv2.imread(innr_templ_path, 0)

                # Add template
                obj_d[innr_label] = [innr_templ]

        # Add template to Database
        Proj_Data_d[label] = [templ, obj_d]


def say_print(text):
    """
    Uses TTS to say the given text and then print.
    """

    # set text in engine
    engine.say(text)

    # print the text
    print(text)

    # play the speech
    engine.runAndWait()

    if engine._inLoop:
        engine.endLoop()


def describe_screen():
    """
    Scans screen's image, detects objects.
    ----------
    Asks user to choose destination object.
    ----------
    :return: abort - True if none was chosen else False, dest - destination object
    """

    dest_loc, dest_name = None, None

    # Capture image from phone and warp
    image = Init.get_frame()
    image = image_proc.warp_w_last_scale(image)

    # Scan screen and get objects
    main_objects_l, sub_obj_d = screen_scan(image)

    if len(main_objects_l) == 0:
        say_print("No objects were found")
        return True, None, None

    read_objects(main_objects_l)

    abort, obj = object_select(main_objects_l)

    if abort is False:

        # If the selected object is a section - list and select sub object
        sub_objects_l = sub_obj_d.get(obj.label)
        if sub_objects_l is not None:

            read_objects(sub_objects_l)

            abort, obj = object_select(sub_objects_l)

        # If the chosen object is a paragraph - read it
        if obj.label == "paragraph":
            action = None
            while action != "y" and action != "n":
                say_print("read text?")
                action = input()
            if action == "y":
                read_paragraph(image, obj.loc)
            abort = True

        else:
            dest_loc, dest_name = obj.loc, obj.label

    return abort, dest_loc, dest_name


def object_select(objects):
    """
    Selects destination from objects according to user input.
    If chk_section is True, the function checks
    :return: abort - True if not selected, dest - selected destination
    """

    chosen_obj = None

    selected_num = input()

    if selected_num == "-1":
        abort = True
    else:
        abort = False
        chosen_obj = objects[int(selected_num)]

    return abort, chosen_obj


def screen_scan(screen_img):
    """
    Scans for objects from Image
    :return: objects
    """

    global Proj_Data_d

    if len(Proj_Data_d) == 0: #TODO
        set_data("migdalor")

    # Image processing - color to gray
    screen_img = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
    ret3, binary_img = cv2.threshold(screen_img, 127, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    main_objects_l = []
    sub_obj_d = {}
    
    for label in Proj_Data_d:
        
        # Get template image
        templ = Proj_Data_d[label][0]
        
        # Find match for template in the image
        result = cv2.matchTemplate(binary_img, templ, cv2.TM_CCORR_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val > 0.95:
            
            # Get objects shape and set location
            w, h = templ.shape[::-1]
            obj_loc = [max_loc[0], max_loc[1], w, h]
            
            # Add object to main_objects_l list
            main_objects_l.append(Object(label, obj_loc))
            
        # If the object is a section, load sub objects as sub objects dictionary
        data_dict = Proj_Data_d[label][1]
        if len(data_dict) > 0:
            
            # Create list
            sub_obj_d[label] = []
            
            # Run over all sub objects
            for label2 in data_dict:

                # Get template image
                templ = data_dict[label2][0]

                # Find match for template in the image
                result = cv2.matchTemplate(binary_img, templ, cv2.TM_CCORR_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                if max_val > 0.95:
                    # Get objects shape and set location
                    w, h = templ.shape[::-1]
                    sub_obj_loc = [max_loc[0], max_loc[1], w, h]
                    
                    # Add object to sub dictionary
                    sub_obj_d[label].append(Object(label2, sub_obj_loc))

    return main_objects_l, sub_obj_d


def read_objects(objects):
    """
    Describes the objects on the screen to user
    :return: none
    """

    text = "Choose object number:\n"
    for i in range(len(objects)):
        obj_name = objects[i].label
        obj_name = obj_name.replace('_', ' ')
        text += "{} - {}\n".format(i, obj_name)

    text += "(-1) - Abort action"

    say_print(text)

    return


def read_paragraph(img, loc):
    """
    The function reads to user the found paragraph
    **** Can read only in English
    :return: none
    """
    x1, y1, w, h = loc

    paragraph = img[y1:y1 + h, x1:x1 + w]
    data = ss.find_all_words(paragraph, 'eng')
    words_list = data["text"]

    flag = False

    for i in reversed(range(len(words_list))):

        if words_list[i] == '':
            if flag:
                if i != 0:
                    words_list = words_list[0:i - 1] + words_list[i + 1::]
                else:
                    words_list = words_list[i + 1::]
            else:
                words_list[i] = '\n'
                flag = True
        else:
            if flag:
                flag = False

    say_print(' '.join(words_list))

    return
