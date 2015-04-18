from Tkinter import Scale,Tk,Canvas,HORIZONTAL,FLAT,LEFT,RIGHT,CENTER
from constants import width, height

SPRINT_CONSTANT = 0.001
ELECT_CONSTANT = 0.1


root = Tk()
timeInput = Scale(root, from_=1, to=100,orient=HORIZONTAL,label="Time",relief = FLAT)
forceInput = Scale(root, from_=1, to=100,orient=HORIZONTAL,label="Force",relief = FLAT)
decayInput = Scale(root, from_=1, to=100,orient=HORIZONTAL,label="Decay",relief = FLAT)

timeInput.set(10)
forceInput.set(50)
decayInput.set(90)

canvas = Canvas(width=width, height=height, bg="#f0f0f0")
canvas.pack(fill = "both", expand = 1, padx=50)
timeInput.pack(side=LEFT, padx=50, pady=10)
forceInput.pack(side=LEFT, padx=50, pady=10)
decayInput.pack(side=LEFT, padx=50, pady=10)

RADIUS = 5

class fdlNode(object):
    """Represents a node in the force directed graph"""

    def __init__(self,name):
        self.name = name
        self.linked = [] #List of FDLNode -- direction agnostic
        self.branch = False #Used for de Bruijn Graph methods
        self.__fx = 0
        self.__fy = 0
        self.__t = 1
        self.__decay = 0.9

    def addCanvas(self,canv, x, y, mass, color):
        self.x, self.y = x, y
        self._canvas = canv
        self.mass = mass
        coord = (self.x)-RADIUS, (self.y)-RADIUS, (self.x)+RADIUS, (self.y)+RADIUS
        self._index = canv.create_oval(coord, fill=color)
        self._vx = 0
        self._vy = 0

    
    def __repr__(self):
        s = "\n{}\nBranch: {}\nLinked to {}:\n".format(self.name,self.branch,len(self.linked))
        for n in self.linked:
            s += n.name + "\n"
        return s

    def addForce(self,node):
        #called on each node before motion
        #ADD ELECTRICAL FORCE
        dx = (node.x - self.x) if (node.x - self.x) != 0 else 0.01
        dy = (node.y - self.y) if (node.y - self.y) != 0 else 0.01
        dfx = (ELECT_CONSTANT * node.mass * self.mass ) / dx
        dfy = (ELECT_CONSTANT * node.mass * self.mass ) / dy

        self.__fx += dfx
        self.__fy += dfy

        if node in self.linked:
            self.__fx += SPRINT_CONSTANT * (node.x - self.x)
            self.__fy += SPRINT_CONSTANT * (node.y - self.y)

        
    def update(self):
        self.__decay = decayInput.get() / 100.0
        self.__t = timeInput.get() / 10.0
        self.__fx *= self.__decay
        self.__fy *= self.__decay
        ax = self.__fx / self.mass
        ay = self.__fy / self.mass
        self._vx += ax * self.__t
        self._vy += ay * self.__t
        self._vx *= self.__decay
        self._vy *= self.__decay
        self.__fx = 0
        self.__fy = 0

    def move(self):
        self.update()
        x1, y1, x2, y2 = self._canvas.coords(self._index)
        root_w = self._canvas.winfo_width()
        root_h = self._canvas.winfo_height()
        if root_w == 1:
            return
        if x2 > root_w or x1 < 0:
            if x1 < 0:
                dx = 0 - x1
            else:
                dx = root_w - x2 
            self._canvas.move(self._index, dx, 0)
            self._vx *= -1
        if y2 > root_h or y1 < 0:
            if y1 < 0:
                dy = 0 - y1
            else:
                dy = root_h - y2 
            self._canvas.move(self._index, 0, dy)
            self._vy *= -1
        dx = self._vx * self.__t
        dy = self._vy * self.__t
        print self._vy

        self._canvas.move(self._index, dx, dy)
        tempX1, tempY1, tempX2, tempY2 = self._canvas.coords(self._index)
        self.x = tempX1 + RADIUS
        self.y = tempY1 + RADIUS
    


def move_nodes(nodes, lines, root):
    for ni in nodes:
        for nj in nodes:
            if ni != nj:
                ni.addForce(nj)
    for n in nodes:
        n.update()
        n.move()
    for line in lines:
        lid = line[0]
        n1 = line[1]
        n2 = line[2]
        canvas.coords( lid, n1.x, n1.y, n2.x, n2.y  )
    root.after(1 , lambda: move_nodes(nodes, lines, root))


def getCanvas():
    return canvas

def FDL(fdlNodes):
    lines = []
    pairs = {}
    for ni in fdlNodes:
         for nj in ni.linked:
            if ni not in pairs:
                pairs[ni] = [nj]
                l = canvas.create_line( ni.x,ni.y,nj.x,nj.y , fill="#000")
                lines.append( (l, ni, nj) )
            elif nj not in pairs[ni]:
                pairs[ni] = pairs[ni] + [nj]
                l = canvas.create_line(ni.x,ni.y,nj.x,nj.y, fill="#000")
                lines.append( (l, ni, nj)   )
                
    move_nodes(fdlNodes, lines, root)
    root.mainloop()