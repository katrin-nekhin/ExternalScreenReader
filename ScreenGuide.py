# imports
import os
import screen_reader as sr
import screen_search as ss
import cursor_navigate as cn
import Init
import study_gui
import image_proc
import cv2


def ask_for_action(main=True):
    """
    Asks user to choose next action.
    ----------------
    Types of actions:
        In main:
        - Hear full description of the screen
        - Search for an object on the screen
        - Settings

        In settings:
        - Train for new DB
        - Select DB

    :return: Chosen action
    """
    action = None

    while action is None:
        if main:
            text = "Choose next action (0 - Settings, 1 - Screen description, 2 - Search): "
        else:
            text = "Choose next action (1 - Set Dataset, 2 - Study, 3 - Calibrate camera): "
        sr.say_print(text)
        action_in = input()

        # if input is invalid - ask again
        if action_in in ["0", "1", "2", "3", "q"]:
            action = action_in
        else:
            sr.say_print("Invalid input")

    return action


def settings(url):
    """
    Program flow in settings mode
    ----------------
    User choices:
        1 - Set Dataset: 
        Allows user to choose Dataset from existing list (taken from folder).
        2 - Study:
        Sends the user to a Training GUI.

    :return: Dataset name
    """
    action = ask_for_action(False)

    if action == "1":       # Set Dataset

        # Get all directories in the folder
        dir_list = [x for x in next(os.walk('.'))[1] if x[0] != '.']

        valid = False

        while not valid:

            # Print dataset options
            sr.say_print("Select data set from the list below: \n{}".format(dir_list))

            # Let user choose dataset
            dataset_name = input()

            if dataset_name in dir_list:
                valid = True
            else:
                sr.say_print("Invalid input, try again")
        
        # Set dataset (load data)
        sr.set_data(dataset_name)
        
    elif action == "2":     # Study
        
        # Start Training Gui
        img_loc_l, dataset_name = study_gui.start(url)
        
        # Organize and save Database
        image_proc.create_db(img_loc_l, dataset_name)

        # Set dataset (load data)
        sr.set_data(dataset_name)

    elif action == "3":  # Calibrate camera

        Init.cam_calib('f')
        
    elif action == "q":
        return

    return


def main_flow():
    
    # Camera Calibration and URL set
    url = Init.cam_calib()
    
    # Get wanted dataset from user and load it   
    settings(url)
    
    while True:
        action = ask_for_action()

        if action == "0":   # Settings

            abort, dest_loc, dest_name = [True, None, None]
            settings(url)

        elif action == "1":  # Describe

            abort, dest_loc, dest_name = sr.describe_screen()

        elif action == "2":  # Search

            abort, dest_loc, dest_name = ss.search_on_screen()

        elif action == "q":

            print("Goodbye!")
            return

        if not abort:
            while action != "y" and action != "n":
                sr.say_print("You have chosen {}. Continue?".format(dest_name))
                action = input()
            if action == "y":
                cn.navigate2dest(dest_loc)
                    


if __name__ == "__main__":
    main_flow()
