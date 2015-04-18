from constants import width, height


kInput = None

SPRING_CONSTANT = 0.01
COULOMB_CONSTANT = 0.01
DAMPING_CONSTANT = 3.6
WALL_CONSTANT = 0.25
TIME_CONSTANT = 1.0
DECAY_CONSTANT = 1.0


root = Tk()
timeInput = Scale(root, from_=1, to=1000,orient=HORIZONTAL,label="Time",relief = FLAT)
springInput = Scale(root, from_=1, to=1000,orient=HORIZONTAL,label="Spring",relief = FLAT)
coulombInput = Scale(root, from_=1, to=1000,orient=HORIZONTAL,label="Coulomb",relief = FLAT)
decayInput = Scale(root, from_=1, to=1000,orient=HORIZONTAL,label="Decay",relief = FLAT)

timeInput.set(100)
springInput.set(250)
coulombInput.set(500)
decayInput.set(90)

canvas = Canvas(width=width, height=height, bg="#f0f0f0")
canvas.pack(fill = "both", expand = 1, padx=50)
timeInput.pack(side=LEFT, padx=50, pady=10)
springInput.pack(side=LEFT, padx=50, pady=10)
coulombInput.pack(side=LEFT, padx=50, pady=10)
decayInput.pack(side=LEFT, padx=50, pady=10)

RADIUS = 4

class fdlNode(object):
    """Represents a node in the force directed graph"""

    def __init__(self,name,mass):
        self.r = RADIUS + mass
        self.name = name
        self.linked = [] #List of FDLNode -- direction agnostic
        self.branch = False #Used for de Bruijn Graph methods
        self.__fx = 0
        self.__fy = 0
        self.mass = mass

    def addCanvas(self,canv, x, y, color):
        self.x, self.y = x, y
        self._canvas = canv
        coord = (self.x)-self.r, (self.y)-self.r, (self.x)+self.r, (self.y)+self.r
        self._index = canv.create_oval(coord, fill=color)
        self._vx = 0
        self._vy = 0

    
    def __repr__(self):
        s = "\n{}\nBranch: {}\nLinked to {}:\n".format(self.name,self.branch,len(self.linked))
        for n in self.linked:
            s += n.name + "\n"
        return s

    def addForce(self,node):
        dx = (node.x - self.x) 
        dx = dx if abs(dx) >= 1 else 1.0
        dy = (node.y - self.y)
        dy = dy if abs(dy) >= 1 else 1.0
        dfx = (COULOMB_CONSTANT * node.mass * self.mass ) / (dx ** 2)
        dfy = (COULOMB_CONSTANT * node.mass * self.mass ) / (dy ** 2)
        if node.x > self.x:
            dfx *= -1
        if node.y > self.y:
            dfy *= -1
        self.__fx += dfx
        self.__fy += dfy

        if node in self.linked:
            self.__fx += SPRING_CONSTANT * (node.x - self.x)
            self.__fy += SPRING_CONSTANT * (node.y - self.y)

        
    def __update(self):
        
        #Add wall forces to center
        root_w = self._canvas.winfo_width()
        root_h = self._canvas.winfo_height()
        d1 = self.y # dsitance from top wall
        d2 = abs(root_h - self.y) * -1 # distance from bottom wall (-)
        d3 = self.x # distance from left wall
        d4 = abs(self.x - root_w) * -1; # distance from right wall (-)
        d1 = d1 if d1 != 0 else 0.1 
        d2 = d2 if d2 != 0 else -0.1 
        d3 = d3 if d3 != 0 else 0.1 
        d4 = d4 if d4 != 0 else -0.1 
        self.__fy += WALL_CONSTANT * COULOMB_CONSTANT / d1 # Top wall force
        self.__fy += WALL_CONSTANT * COULOMB_CONSTANT / d2 # Bottom Wall force
        self.__fx += WALL_CONSTANT * COULOMB_CONSTANT / d3 # Left Wall force
        self.__fx += WALL_CONSTANT * COULOMB_CONSTANT / d4 # Right Wall force

        self.__fx *= DECAY_CONSTANT
        self.__fy *= DECAY_CONSTANT
        ax = self.__fx / self.mass
        ay = self.__fy / self.mass
        self._vx += ax * TIME_CONSTANT
        self._vy += ay * TIME_CONSTANT
        self._vx *= DECAY_CONSTANT
        self._vy *= DECAY_CONSTANT
        self.__fx = 0
        self.__fy = 0

    def move(self):
        self.__update()
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
        dx = self._vx * TIME_CONSTANT
        dy = self._vy * TIME_CONSTANT

        self._canvas.move(self._index, dx, dy)
        tempX1, tempY1, tempX2, tempY2 = self._canvas.coords(self._index)
        self.x = tempX1 + self.r
        self.y = tempY1 + self.r
  

def update():
    global COULOMB_CONSTANT
    global SPRING_CONSTANT
    global TIME_CONSTANT
    global DECAY_CONSTANT
    COULOMB_CONSTANT = coulombInput.get() / 0.05
    SPRING_CONSTANT = springInput.get() / 10000.0
    DECAY_CONSTANT = decayInput.get() / 1000.0
    TIME_CONSTANT = timeInput.get() / 100.0  


def move_nodes(nodes, lines, root):
    update()
    for ni in nodes:
        for nj in nodes:
            if ni != nj:
                ni.addForce(nj)
    for n in nodes:
        n.move()
    for line in lines:
        lid = line[0]
        n1 = line[1]
        n2 = line[2]
        canvas.coords( lid, n1.x, n1.y, n2.x, n2.y  )
    root.after(1 , lambda: move_nodes(nodes, lines, root))



def FDL(k,fName):
    fdlNodes,minSeqLen = getFDLNodes(k,fName)
    lines = []
    pairs = {}

    if not kInput:
        minSeqLen = minLen -1 
        kInput = Scale(root, from_=3, to=end,orient=HORIZONTAL,label="K",relief = FLAT)
        kInput.set(k)
        kInput.pack(side=LEFT, padx=50, pady=10)
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