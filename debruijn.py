import math
import random
from sys import argv
import sys
from time import time
from Tkinter import Canvas, CENTER, FLAT, HORIZONTAL, LEFT, Scale, Tk


#input Constants
fileIndex = 1
kIndex = 2

#Input field set in first read of sequences
kInput = None

#Size of the Tkinter Screen
width=1000
height=700

#Physics constants. Initial values reset by sliders
SPRING_CONSTANT = 0.01 # Contant for sprint force
COULOMB_CONSTANT = 0.01 # Constant for coulomb force
WALL_CONSTANT = 0.250 # Static constant used for a wall force to center the nodes
TIME_CONSTANT = 1.0 # Time constant for speed of forces
DECAY_CONSTANT = 1.0 # Speed of damping both overall force and velocity

#Initializes the Tkinter frame and sliders
root = Tk()
#Adds horizontal sliders at the bottom for FDL constants
timeInput = Scale(root, from_=1, to=500,orient=HORIZONTAL,label="Time",relief = FLAT)
springInput = Scale(root, from_=1, to=1000,orient=HORIZONTAL,label="Spring",relief = FLAT)
coulombInput = Scale(root, from_=1, to=1000,orient=HORIZONTAL,label="Coulomb",relief = FLAT)
decayInput = Scale(root, from_=0, to=100,orient=HORIZONTAL,label="Decay",relief = FLAT)

#Sets initial FDL constant values
timeInput.set(100)
springInput.set(250)
coulombInput.set(500)
decayInput.set(90)

#Initializes the canvas for animation 
canvas = Canvas(width=width, height=height, bg="#f0f0f0")
canvas.pack(fill = "both", expand = 1, padx=50)

#Adds teh sliders to the tkinter frame after the canvas for positioning
timeInput.pack(side=LEFT, padx=50, pady=10)
springInput.pack(side=LEFT, padx=50, pady=10)
coulombInput.pack(side=LEFT, padx=50, pady=10)
decayInput.pack(side=LEFT, padx=50, pady=10)

#Smallest node size in pixels
RADIUS = 5


#Calculates the euclidean distance between an oval and a point
def distance(x,y, coords):
    x0, y0, x1, y1 = coords # tuple (x0,y0,x1,y1)
    x2 = (x0 + x1) / 2.0
    y2 = (y0 + y1) / 2.0
    return ( (x - x2)**2 + (y - y2)**2 ) ** 0.5

#Global values used for dragging functionality
DRAGITEM  = None
DRAGITEMX = 0
DRAGITEMY = 0

def OnButtonPress(event):
    global DRAGITEM
    global DRAGITEMX
    global DRAGITEMY
    # record the item and its location
    nodes = canvas.find_withtag("fdlnode") #Finds all fdl nodes
    #Finds the closest node to the click point
    closest = sorted([(node,distance(event.x,event.y,canvas.coords(node))) for node in nodes], key=lambda x:x[1])[:1]
    #If the closest node is within 10 pixels begins draggin
    if closest[0][1] > 10:
        return
    #sets the drag information
    DRAGITEM = closest[0][0]
    DRAGITEMX = event.x
    DRAGITEMY = event.y
 
def OnButtonRelease(event):
    global DRAGITEM
    global DRAGITEMX
    global DRAGITEMY
    # reset the drag information
    DRAGITEM = None
    DRAGITEMX = 0
    DRAGITEMY = 0
 
def OnMotion(event):
    global DRAGITEM
    global DRAGITEMX
    global DRAGITEMY
    if not DRAGITEM:
        return
    # compute how much this object has moved
    delta_x = event.x - DRAGITEMX
    delta_y = event.y - DRAGITEMY
    # move the object the appropriate amount
    canvas.move(DRAGITEM, delta_x, delta_y)
    # record the new position
    DRAGITEMX = event.x
    DRAGITEMY = event.y

#Binds the dragging events to the left click button
canvas.bind("<ButtonPress-1>", OnButtonPress)
canvas.bind("<ButtonRelease-1>", OnButtonRelease)
canvas.bind("<B1-Motion>", OnMotion)


#Function to determine if a node is being dragged
def isDragged(node):
    return DRAGITEM and DRAGITEM == node._index



def open_file(fName):
    """Returns the open file or None on IOError"""
    try:
        return open(fName)
    except IOError:
        return None

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
        """Takes in canvas and puts the fdlnode on the canvas"""
        self.x, self.y = x, y
        self._canvas = canv
        coord = (self.x)-self.r, (self.y)-self.r, (self.x)+self.r, (self.y)+self.r
        self._index = canv.create_oval(coord, fill=color,tags=("token","fdlnode"))
        self._vx = 0
        self._vy = 0
    
    def __repr__(self):
        s = "\n{}\nBranch: {}\nLinked to {}:\n".format(self.name,self.branch,len(self.linked))
        for n in self.linked:
            s += n.name + "\n"
        return s

    def addForce(self,node):
        """Adds all appropriate forces associated with the given node"""
        #If either node is being dragged ignore all forces
        if isDragged(self) or isDragged(node):
            return 
        # find delta x and y, any value |v| < 1 is replaced with 1
        dx = (node.x - self.x) 
        dx = dx if abs(dx) >= 1 else 1.0
        dy = (node.y - self.y)
        dy = dy if abs(dy) >= 1 else 1.0
        #Calculate the coulomb force
        dfx = (COULOMB_CONSTANT * node.mass * self.mass ) / (dx ** 2)
        dfy = (COULOMB_CONSTANT * node.mass * self.mass ) / (dy ** 2)
        #Sets the sign of forces to the appropriate direction
        if node.x > self.x:
            dfx *= -1
        if node.y > self.y:
            dfy *= -1
        #updates net node force
        self.__fx += dfx
        self.__fy += dfy
        #Adds spring force if the nodes are linked
        if node in self.linked:
            self.__fx += SPRING_CONSTANT * (node.x - self.x)
            self.__fy += SPRING_CONSTANT * (node.y - self.y)

        
    def __update(self):
        """Updates the node's velocity from the forces and resets the forces to 0"""
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
        #Decays the forces to speed convergence
        self.__fx *= DECAY_CONSTANT
        self.__fy *= DECAY_CONSTANT
        #Calculates acceleration from force
        ax = self.__fx / self.mass
        ay = self.__fy / self.mass
        #Calculates net velocity from acceleration
        self._vx += ax * TIME_CONSTANT
        self._vy += ay * TIME_CONSTANT
        #Decays the velocity to speed convergence
        self._vx *= DECAY_CONSTANT
        self._vy *= DECAY_CONSTANT
        #Resets forces
        self.__fx = 0
        self.__fy = 0

    def move(self):
        """Uses the node's velocity to update the node's location"""
        #updates the velocity from the force
        self.__update()
        #gets the current location
        x1, y1, x2, y2 = self._canvas.coords(self._index)
        root_w = self._canvas.winfo_width()
        root_h = self._canvas.winfo_height()
        #The tkinter's frame will be 1 while initializing
        if root_w == 1:
            return
        #If the node is outside of the canvas flips velocity and places back
        #   inside the canvas
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
        #Caluclates net distance from velocity
        dx = self._vx * TIME_CONSTANT
        dy = self._vy * TIME_CONSTANT
        #Moves if the node is not being dragged
        if not isDragged(self):
            self._canvas.move(self._index, dx, dy)
        #Resets the nodes x and y to current position
        tempX1, tempY1, tempX2, tempY2 = self._canvas.coords(self._index)
        self.x = tempX1 + self.r
        self.y = tempY1 + self.r


#Normalization classes and function

class ZNorm:
    """Used to normalize a list of numbers"""
    def __init__(self, num_list):
        self.avg = mean(num_list)
        self.std_dev = std_dev(num_list, self.avg)

    def norm(self, num):
        if self.std_dev == 0:
            return 0
        return (num - self.avg) / self.std_dev

def mean(num_list):
    """Calculates the average of the given list. Return 0 on an empty list"""
    if len(num_list) == 0:
        return 0
    sm = 0
    for num in num_list:
        sm += num
    mean = sm / len(num_list)
    return mean

def std_dev(num_list, avg):
    """Retruns the standard deviation of the list with the given mean. Returns 0 on
        an empty list."""
    if len(num_list) == 0:
        return 0
    var = 0
    for num in num_list:
        var += ((num - avg) ** 2)
    var /= (len(num_list) - 1)
    std = math.sqrt(var)
    return std

#End of Normalization classes and function



def sub_sequences(s,k):
    """Returns all contiguous subsquences of length k in order within s"""
    length = len(s) #string length
    substrings = length - k + 1 #number of contiguous substrings
    if substrings <= 0:
        return []
    seqs = []
    for i in range(substrings):
        seqs.append( s[i: i + k]  )
    return seqs


class Sequence(object):
    """Used to represent a single sequence"""
    def __init__(self,s,k):
        self.seq = s
        self.subs = sub_sequences(s,k)


class deBruijn(object):
    """Represents a de Bruijn graph using the node class below.
     Allows kmer addtion and conversion to fdlnode list."""

    # Node Class used for building the de Bruign graph #
    class Node(object):
        """Represents a node in the de Bruign graph"""

        def __init__(self,s):
            self.kmer = s
            self.ins = []
            self.outs = []
            self.marked = False
            self.branch = False
            self.count = 0

        def __repr__(self):
            return "{}: \nIns: {}\nOuts: {}\nMarked: {}\nBranch: {}\nCount: {}\n".format(
                self.kmer, self.ins, self.outs, self.marked,self.branch,self.count)

    # end of Node class #

    def __init__(self):
        self.graph = {}

    def add(self,s,previous = None):
        """Adds a kmer to the graph"""
        #Assumes that previous node exists
        if s not in self.graph:
            n = deBruijn.Node(s)
        else:
            n = self.graph[s]
        n.count += 1 #increases coverage
        if previous:
            self.graph[previous].outs.append(s)
            n.ins.append(previous)
        self.graph[s] = n

    def update(self):
        """Updates all nodes to indicate if they are a branch or not"""
        for n in self.graph.values():
            n.ins = list(set(n.ins))
            n.outs = list(set(n.outs))
            n.branch = len(n.ins) > 1 or len(n.outs) > 1

    def getFDLNodeList(self):
        """retuns a list of FDL nodes from the de Bruign graph"""
        self.update() #Updates the graph to exclude duplicates
        fdlNodes = {}
        #Iterates through all nodes of the graph and builds the
        #   FDL node equivalent
        for n in self.graph.values():
            name = n.kmer
            if name not in fdlNodes:
                #Uses the coverage for the fdl node mass
                fdlNodes[name] = fdlNode(name,n.count)

            temp = fdlNodes[name]
            allConnections = list(set(n.ins + n.outs))
            for kmer in allConnections:
                #Constructs fdl node if not present
                if kmer not in fdlNodes:
                    fdlNodes[kmer] = fdlNode(kmer,self.graph[kmer].count)
                #Ensures the fdl node will not point to itself
                if kmer != n.kmer:
                    #adds the fdl node to the list of linked nodes
                    temp.linked.append(fdlNodes[kmer])
            #adds the new fdl node to the hash
            fdlNodes[name] = temp
        return fdlNodes.values()




def getFDLNodes(k,fName):
    """Opens file of sequences and returns all fdlnodes for the associated 
    de Bruijn Graph for the given k value"""
    #Gets all the sequences
    f = open_file(fName)
    sequences = [line.strip() for line in f.readlines() if len(line.strip()) > 0]
    f.close()
    subDict = {}
    subSequences = {}
    seqs = []
    minSeqLen = 100000 #used to determine the shortest sequence length
    for seq in sequences:
        if len(seq) < minSeqLen:
            minSeqLen = len(seq)
        s = Sequence(seq,k)
        #Skips sequences smaller than a kmer
        if len(s.subs) == 0:
            continue
        seqs.append(s)
    #Build the De Bruign Graph
    graph = deBruijn()
    for s in seqs:
        subs = s.subs
        #Expects a sequence of atleast length k + 1
        if len(subs) < 2:
            continue
        graph.add(subs[0])
        for i in range(1, len(s.subs)):
            graph.add(subs[i], subs[i - 1])
    graph.update() #Marks all branching nodes
    #Gets all the FDL nodes
    fdlNodes = graph.getFDLNodeList()
    #gets a list of masses
    masses = map( lambda x: x.mass, fdlNodes )
    #Normalizes all of the masses
    norm = ZNorm(masses)
    norm_masses = map( lambda x: norm.norm(x), masses )
    #Records smallest normalized value
    min_mass = min(norm_masses)

    for n in fdlNodes:
        #Uses normalized mass shifted to have a minumum mass of 1
        n.mass = norm.norm(n.mass) - min_mass + 1
        #Starts nodes at random locations
        x = int( random.random() * width  )
        y = int( random.random() * height  )

        #sets the node color based on the nodes properties
        #One link (a start node) is blue
        #Two links (an intermediate node) is green
        #Three or more links (a branching node) is red 
        n.linked = set(n.linked)
        num_connections = len(n.linked)
        if num_connections == 1:
            #START
            n.addCanvas(canvas, x, y, "blue")
        elif num_connections == 2:
            #INTERMEDIATE
            n.addCanvas(canvas, x, y, "green")
        else:
            #BRANCH
            n.addCanvas(canvas, x, y, "red")
    #Retunds the list of FDL nodes and the minimum sequence length
    return fdlNodes,minSeqLen

def update():
    """Updates all constants based on the sliders"""
    global COULOMB_CONSTANT
    global SPRING_CONSTANT
    global TIME_CONSTANT
    global DECAY_CONSTANT
    #Division constants scale constants to appropriate ranges
    COULOMB_CONSTANT = coulombInput.get() / 0.05
    SPRING_CONSTANT = springInput.get() / 10000.0
    DECAY_CONSTANT = decayInput.get() / 1000.0
    TIME_CONSTANT = timeInput.get() / 100.0  


def move_nodes(nodes, previous, k, lines, root, fName):
    """Redraw function. Moves all nodes appropriately in regards
        to the forces experienced. Handles changing k values"""
    #Regenerates all nodes and links if the k value has changed
    if previous != k:
        canvas.delete("all")
        nodes,_ = getFDLNodes(k,fName)
        lines = addLines(nodes)
    update() #Refreshes all constants
    #Applies all forces to all nodes
    for ni in nodes:
        for nj in nodes:
            if ni != nj:
                ni.addForce(nj)
    #Moves all nodes according to cummulative force
    for n in nodes:
        n.move()
    #Moves all lines according to new node location
    for line in lines:
        lid = line[0]
        n1 = line[1]
        n2 = line[2]
        canvas.coords( lid, n1.x, n1.y, n2.x, n2.y  )
    #recursively recalls the redraw function every 1 millisecond 
    root.after(1 , lambda: move_nodes(nodes, k, kInput.get(), lines, root, fName))


def addLines(fdlNodes):
    """Adds all lines to the canvas based on node links 
        and returns a list of tuples of the form (line id, node 1, node 2)"""
    pairs = {}
    lines = []
    #Iterates through all nodes and adds link pairs with associated lines
    #   if that pair has not already generated a line
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
    return lines


def FDL(k,fName):
    """Infitie loop function which constantly runs the display given
    the file name of the sequences and an initial k"""

    global kInput
    #Gets the initial de Bruijn Graph
    fdlNodes,minSeqLen = getFDLNodes(k,fName)  
    #Sets up kInput to the appriate scale (3 to the shortest length - 1 ) to ensure
    #   all sequence reads are always included
    if not kInput:
        minSeqLen -= 1 
        kInput = Scale(root, from_=3, to=minSeqLen,orient=HORIZONTAL,label="K",relief = FLAT)
        kInput.set(k) #sets the initial k value
        kInput.pack(side=LEFT, padx=50, pady=10)

    #generates all lines from the initial graph    
    lines = addLines(fdlNodes)
    #starts inifinite recursive loop for redraw function
    move_nodes(fdlNodes, kInput.get(), kInput.get(), lines, root,fName)
    #starts display
    root.mainloop()


def main():
    #Initialization
    ##Ensures the correct number of parameters
    if len(argv) != 3:
        sys.exit("{} usage: python {} [filename] [kvalue]".format(argv[0],argv[0]))
    ##Retrieves file
    fName = argv[fileIndex]
    f = open(fName)
    if not f:
        sys.exit("{}: Must target a valid file".format(argv[0]))
    f.close()
    ##Gets K value and exits if non-integer, k must be atleast 3
    try:
        k = int(argv[kIndex])
    except ValueError:
        sys.exit("{}: K value must be an integer".format(argv[0]))
    if k < 3:
        sys.exit("{}: K value must be atleast 3".format(argv[0]))
    #Starts infinite display loop
    FDL(k,fName)

if __name__ == "__main__":
    main()
