class B:
    def __init__(self):
        self.y=20
    
    def move(self,func):
        print(func(self.y))

class A:
    def __init__(self):
        self.x=10
        self.b=B()

    def is10(self):
        return self.x==10

    def oper(self):
        self.b.move(self.is10)


a=A()
a.oper()