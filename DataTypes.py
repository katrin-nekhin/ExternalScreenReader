


class Object:
    def __init__(self, label, loc):
        self.label  = label
        self.loc    = loc

class Main_object:
    def __init__(self, label, loc):
        self.label   = label
        self.loc     = loc
        self.objects = []

    def add_obj(self, obj):
        self.objects.append(obj)