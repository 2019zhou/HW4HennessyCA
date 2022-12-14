import copy

class foo:
    def __init__(self):
        self.a = 1
        self.b = 2
        self.c = 4
        
    def next(self):
        self.c = 5
        self.d = 4
        
    


class foo2:
    def __init__(self, f: foo):
        self.ref_f = f
        self.tmp_f = f
        self.e =6
    
    def next(self):
        self.tmp_f = copy.deepcopy(self.ref_f)
        self.e = 8
        

f111 = foo()
f999 = foo2(f111)
f999.ref_f.c = 1000
print(f111.c)
f111.d = 9
print(f999.ref_f.d)