from tkinter import *
from PIL import ImageTk, Image, ImageDraw
import image_proc
from DataTypes import Main_object, Object
import cv2
import numpy as np
import requests
import imutils

import Init
global img_obj_l

MINI_WIDTH = 1200

## Popup window
class popupWindow(object):
    def __init__(self,master, text):
        top=self.top=Toplevel(master)
        self.l=Label(top,text=text)
        self.l.pack()
        self.e=Entry(top)
        self.e.pack()
        self.b=Button(top,text='Ok',command=self.cleanup)
        self.b.pack({"side": "left"})
        self.c = Button(top, text='cancel', command=self.cancel)
        self.c.pack({"side": "left"})
    def cleanup(self):
        self.value=self.e.get()
        self.top.destroy()
    def cancel(self):
        self.value = False
        self.top.destroy()


## Application
class Application(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master)
        # Init values
        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0
        self.draw_en = False
        self.img_obj_l = []
        self.obj_l = []
        self.section = None
        self.vc = None
        self.img_orig = None
        self.img = None
        self.img_temp = None
        self.image_on_canvas = None

        self.pack()
        self.createWidgets(master)

    def popup(self, button, text):
        input = popupWindow(self.master, text)
        self.buttons_active(False)
        self.master.wait_window(input.top)
        self.buttons_active(True)
        return input.value

    def save_and_quit(self):
        global img_obj_l
        if self.section != None:
            self.obj_l.append(self.section)
        if self.obj_l != []:
            self.img_obj_l.append([self.img_orig, self.obj_l])
        img_obj_l = self.img_obj_l
        self.quit()

    def set_canvas(self, vc):
        self.vc = vc
        img_resp = requests.get(self.vc)
        img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
        frame = cv2.imdecode(img_arr, -1)
        frame = image_proc.warp_screen_img(frame)
        self.img_orig = frame.copy()
        ORIG_WIDTH = self.img_orig.shape[1]
        self.scale = ORIG_WIDTH / MINI_WIDTH
        smaller_frame = imutils.resize(frame, width=MINI_WIDTH)
        self.img_curr = Image.fromarray(smaller_frame)
        self.img = ImageTk.PhotoImage(self.img_curr)
        self.image_on_canvas = self.canvas.create_image(0, 10, anchor=NW, image=self.img)

    def take_frame(self):
        if self.section != None:
            self.obj_l.append(self.section)
        if self.obj_l != []:
            self.img_obj_l.append([self.img_orig, self.obj_l])
        self.section = None
        self.obj_l = []
        frame = Init.cam_calib('f')
        frame = image_proc.warp_screen_img(frame)
        self.img_orig = frame.copy()
        ORIG_WIDTH = self.img_orig.shape[1]
        self.scale = ORIG_WIDTH / MINI_WIDTH
        smaller_frame = imutils.resize(frame, width=MINI_WIDTH)
        self.img_curr = Image.fromarray(smaller_frame)
        self.img = ImageTk.PhotoImage(self.img_curr)
        self.canvas.itemconfig(self.image_on_canvas, image=self.img)


    def draw(self):
        img = self.img_curr.copy()
        draw = ImageDraw.Draw(img)

        loc = [self.x0, self.y0, self.x1, self.y1]
        draw.rectangle(loc, outline=50)
        self.curr_loc = loc
        self.img_temp = img.copy()

        del draw
        self.img = ImageTk.PhotoImage(img)

        self.canvas.itemconfig(self.image_on_canvas, image=self.img)


    def add_obj_f(self):
        self.buttons_active(False)
        self.add_obj["text"] = "Selecting object"
        self.draw_en = "start"


    def add_sect_f(self):
        self.buttons_active(False)
        self.add_sect["text"] = "Selecting section"
        self.draw_en = "start"

    
    def select(self, event):
        if self.draw_en == "start":
            self.x0, self.y0 = event.x - 2, event.y - 9
            self.draw_en = "drag"
        elif self.draw_en == "drag":
            self.x1, self.y1 = event.x - 2, event.y - 9
            self.draw()

    def release(self, event):
        if self.draw_en != False:

            input = self.popup(self.add_obj, "Type name:")

            if input == False or (self.add_sect["text"] == "Selecting section" and input == "None"):
                self.img = ImageTk.PhotoImage(self.img_curr)
                self.canvas.itemconfig(self.image_on_canvas, image=self.img)

            if input != False:

                if self.add_obj["text"] == "Selecting object":

                    self.img_curr = self.img_temp
                    loc = [int(element * self.scale) for element in self.curr_loc]
                    new_object = Object(label=input, loc=loc)
                    if self.section == None:
                        self.obj_l.append(new_object)
                    else:
                        self.section.add_obj(new_object)

                elif self.add_sect["text"] == "Selecting section":

                    if self.section != None:
                        self.obj_l.append(self.section)

                    if input != "None":
                        self.img_curr = self.img_temp
                        loc = [int(element * self.scale) for element in self.curr_loc]
                        self.section = Main_object(label=input, loc=loc)
                    else:
                        self.section = None

                    self.l["text"] = "Section = {}".format(input)


            if self.add_obj["text"] == "Selecting object":
                self.add_obj["text"] = "Add Object"
            if self.add_sect["text"] == "Selecting section":
                self.add_sect["text"] = "Add Section"

            self.buttons_active(True)

        self.draw_en = False

    def clear_draw(self):
        self.obj_l = []
        self.section = None
        smaller_img = imutils.resize(self.img_orig, width=MINI_WIDTH)
        self.img_curr = Image.fromarray(smaller_img)
        self.img = ImageTk.PhotoImage(self.img_curr)
        self.canvas.itemconfig(self.image_on_canvas, image=self.img)

    def buttons_active(self, active=False):
        if active == False:
            mode = "disabled"
        else:
            mode = "normal"

        self.add_sect["state"] = mode

        self.add_obj["state"] = mode

        self.clr["state"] = mode


    def createWidgets(self, master):
        self.topframe = Frame(self)
        self.topframe.pack({"side": "top"})

        self.bottomframe = Frame(self)
        self.bottomframe.pack({"side": "bottom"})

        self.QUIT = Button(self.topframe)
        self.QUIT["text"] = "QUIT"
        self.QUIT["fg"]   = "red"
        self.QUIT["command"] =  self.save_and_quit

        self.QUIT.pack({"side": "left"})

        self.frame = Button(self.topframe)
        self.frame["text"] = "Next Picture"
        self.frame["command"] = self.take_frame

        self.frame.pack({"side": "left"})

        self.l = Label(self.topframe, text="Section = None")
        self.l.pack({"side": "left"})

        self.add_sect = Button(self)
        self.add_sect["text"] = "Add Section"
        self.add_sect["command"] = self.add_sect_f

        self.add_sect.pack({"side": "left"})

        self.add_obj = Button(self)
        self.add_obj["text"] = "Add Object"
        self.add_obj["command"] = self.add_obj_f

        self.add_obj.pack({"side": "left"})

        self.clr = Button(self)
        self.clr["text"] = "Clear selection"
        self.clr["command"] = self.clear_draw

        self.clr.pack({"side": "left"})

        self.canvas = Canvas(master, width=1300, height=700)
        self.canvas.pack()
        self.canvas.bind('<ButtonPress-1>', self.select)
        self.canvas.bind('<ButtonRelease-1>', self.release)
        self.canvas.bind('<B1-Motion>', self.select)



def start(vc):
    global img_obj_l
    dataset = input("Input data set name: ")
    root = Tk()
    app = Application(master=root)
    app.set_canvas(vc=vc)
    app.mainloop()
    root.destroy()
    return [img_obj_l, dataset]