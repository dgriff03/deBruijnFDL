import sys
from time import time
from constants import width, height
from Tkinter import Scale,Tk,Canvas,HORIZONTAL,FLAT,LEFT,RIGHT,CENTER
import random
import math
from sys import argv
fileIndex = 1
kIndex = 2

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



DEBUG = True
#Note: functions are _ seperated, variables are cammel case




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

class ZNorm:
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




class Sequence(object):
    """Used to represent a single sequence"""

    def __init__(self,s,k):
        self.seq = s
        self.subs = sub_sequences(s,k)


class deBruijn(object):
    """Represents a de Bruijn graph using the node class below. Allows kmer addtion and traversal"""


    # Node Class used for building and traversing de Bruign graph #
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


    #Contig class will be used to build the contigs from nodes#
    class Contig(object):
        """Used to build a contig during the de Bruijn graph traversal"""

        def __init__(self):
            self.contig = []
            self.branch_node = None

        def add(self,kmer):
            """Builds the contig string, expects additions to be sequential"""
            if not self.contig:
                self.contig = list(kmer)
            else:
                self.contig.append(kmer[-1])

        def build(self):
            """returns the contig string"""
            return ''.join(self.contig)



    # end of Contig Class #

    def __init__(self):
        self.graph = {}

    def add(self,s,previous = None):
        """Adds a kmer to the graph"""
        #Assumes that previous node exists
        if s not in self.graph:
            n = deBruijn.Node(s)
        else:
            n = self.graph[s]
        n.count += 1
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
        self.update()
        fdlNodes = {}
        for n in self.graph.values():
            name = n.kmer
            if name not in fdlNodes:
                fdlNodes[name] = fdlNode(name,n.count)

            temp = fdlNodes[name]
            allConnections = list(set(n.ins + n.outs))
            for kmer in allConnections:
                if kmer not in fdlNodes:
                    fdlNodes[kmer] = fdlNode(kmer,self.graph[kmer].count)
                if kmer != n.kmer:
                    temp.linked.append(fdlNodes[kmer])
            fdlNodes[name] = temp
        return fdlNodes.values()


    def __get_contig(self,start):
        """Takes a start node and returns a list of contigs from iterating from
            the provided start node. Will mark nodes while iterating"""
        c = deBruijn.Contig()
        n = start
        break_out = False
        while not n.branch and not n.marked:
            n.marked = True
            c.add( n.kmer )
            if not n.outs:
                break_out = True
                break
            n = self.graph[ n.outs[0] ]
        n.makred = True
        if not break_out and not n.branch: #Discards ambiguous sections
            return []
        c.add( n.kmer )
        c.branch_node = n.kmer
        return [c.build()]

    def __get_contig_path(self,start):
        """Takes a start node and returns a list of contigs from iterating from
            the provided start node. Will mark nodes while iterating"""
        c = deBruijn.Contig()
        n = start
        while not n.marked and not n.branch:
            c.add( n.kmer )
            n.marked = True
            if not n.outs:
                break
            n = self.graph[ n.outs[0] ]
        return [c.build()]



    def contigs(self):
        """Returns a list of contigs generated from the graph"""
        contigs = []
        nodes = self.graph.values()
        zero_in = filter(lambda x: len(x.ins) == 0 ,nodes)
        non_branching = sorted( 
                filter(
                    lambda x: len(x.ins) == 1 and self.graph[x.ins[0]].branch,nodes)
                , key=lambda x: len(x.ins))
        for n in zero_in:
            if n.marked: #Skip all nodes that are already marked
                continue
            contigs += self.__get_contig(n)
        for n in non_branching:
            if n.marked: #Skip all nodes that are already marked
                continue
            contigs += self.__get_contig_path(n)
        return contigs


def open_file(fName):
    """Returns the open file or None on IOError"""
    try:
        return open(fName)
    except IOError:
        return None

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


def getFDLNodes(k,fName):
    #Removes all sequences with erroneous data (subsquences of length k that occur once)
    ##Generates all subsequnces of length k with count  
    f = open_file(fName)
    sequences = [line.strip() for line in f.readlines() if len(line.strip()) > 0]
    f.close()
    subDict = {}
    subSequences = {}
    seqs = []
    minSeqLen = 100000
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

    fdlNodes = graph.getFDLNodeList()
    masses = map( lambda x: x.mass, fdlNodes )
    norm = ZNorm(masses)
    norm_masses = map( lambda x: norm.norm(x), masses )
    min_mass = min(norm_masses)

    for n in fdlNodes:
        n.mass = norm.norm(n.mass) - min_mass + 1 #makes min mass 1
        x = int( random.random() * width  )
        y = int( random.random() * height  )
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
    return fdlNodes,minSeqLen


  

def update():
    global COULOMB_CONSTANT
    global SPRING_CONSTANT
    global TIME_CONSTANT
    global DECAY_CONSTANT
    COULOMB_CONSTANT = coulombInput.get() / 0.05
    SPRING_CONSTANT = springInput.get() / 10000.0
    DECAY_CONSTANT = decayInput.get() / 1000.0
    TIME_CONSTANT = timeInput.get() / 100.0  



def move_nodes(nodes, previous, k, lines, root, fName):

    if previous != k:
        canvas.delete("all")
        nodes,_ = getFDLNodes(k,fName)
        lines = addLines(nodes)
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
    root.after(1 , lambda: move_nodes(nodes, k, kInput.get(), lines, root, fName))


def addLines(fdlNodes):
    pairs = {}
    lines = []
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
    global kInput
    fdlNodes,minSeqLen = getFDLNodes(k,fName)  
    if not kInput:
        minSeqLen -= 1 
        kInput = Scale(root, from_=3, to=minSeqLen,orient=HORIZONTAL,label="K",relief = FLAT)
        kInput.set(k)
        kInput.pack(side=LEFT, padx=50, pady=10)
    
    lines = addLines(fdlNodes)

    move_nodes(fdlNodes, kInput.get(), kInput.get(), lines, root,fName)
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
    ##Gets all sequences and removes endline character
    ##Gets K value and exits if non-integer, k must be atleast 3
    try:
        k = int(argv[kIndex])
    except ValueError:
        sys.exit("{}: K value must be an integer".format(argv[0]))
    if k < 3:
        sys.exit("{}: K value must be atleast 3".format(argv[0]))
    FDL(k,fName)

if __name__ == "__main__":
    main()
