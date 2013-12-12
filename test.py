class TestFunc:

    def __init__(self, func):
        self.func = func

    def start(self):
        self.func()

def test1():
    print 'test1'

def test2():
    print 'test2'

if __name__ == "__main__":
    testfunc = TestFunc(test1)
    testfunc.start()

    testfunc = TestFunc(test2)
    testfunc.start()
