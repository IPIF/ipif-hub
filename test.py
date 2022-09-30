class Thing:
    def __set_name__(*args):
        print(args)


class Stuff:
    thing = Thing()
