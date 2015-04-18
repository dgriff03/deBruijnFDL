from sys import argv
import sys
from time import time
from FDL import FDL,fdlNode, canvas
from constants import width, height
import random
fileIndex = 1
kIndex = 2

DEBUG = True
#Note: functions are _ seperated, variables are cammel case


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
                fdlNodes[name] = fdlNode(name)
            temp = fdlNodes[name]
            temp.branch = n.branch
            allConnections = list(set(n.ins + n.outs))
            for kmer in allConnections:
                if kmer not in fdlNodes:
                    fdlNodes[kmer] = fdlNode(kmer)
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


def timer():
    """Creates a time instance that will report the runtime between the last
        time it was called and the total time of its existance if global DEBUG true"""
    start = [time()]
    old = [time()]
    def t(title):
        if DEBUG:
            print title 
            print "Time since start: {}".format(time() - start[0])
            print "Time since last call: {}".format(time() - old[0])
            print ""
            old[0] = time()
    return t


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


def main():
    t = timer()
    #Initialization
    ##Ensures the correct number of parameters
    if len(argv) != 3:
        sys.exit("{} usage: python {} [filename] [kvalue]".format(argv[0],argv[0]))
    ##Retrieves file
    f = open_file(argv[fileIndex])
    if not f:
        sys.exit("{}: Must target a valid file".format(argv[0]))
    ##Gets all sequences and removes endline character
    sequences = [line.strip() for line in f.readlines() if len(line.strip()) > 0]
    ##Gets K value and exits if non-integer, k must be atleast 3
    try:
        k = int(argv[kIndex])
    except ValueError:
        sys.exit("{}: K value must be an integer".format(argv[0]))
    if k < 3:
        sys.exit("{}: K value must be atleast 3".format(argv[0]))
    t("Initialization Complete")
    #Removes all sequences with erroneous data (subsquences of length k that occur once)
    ##Generates all subsequnces of length k with count  
    subDict = {}
    subSequences = {}
    seqs = []
    for seq in sequences:
        s = Sequence(seq,k)
        #Skips sequences smaller than a kmer
        if len(s.subs) == 0:
            continue
        seqs.append(s)
    #   for sub in s.subs:
    #       if sub in subSequences:
    #           subSequences[sub].append(s)
    #       else:
    #           subSequences[sub] = [s]
    #       subDict[sub] = subDict.get(sub,0) + 1
    # t("Subsequences generation Complete")
    # ##Captures all subsequences that occur only once
    # UniqueSubs = [ x[0] for x in filter(lambda (k,v): v == 1, subDict.iteritems() ) ]
    # ##Removes all sequences which have unique subsequences
    # t("Unique contiguous sub-sequences found")
    # errorSequences = []
    # ###obtains all sequences which contain a unique subsequence
    # for sub in UniqueSubs:
    #   errorSequences += subSequences[sub]
    # badSequences = set(errorSequences) # A set of all sequences with an error
    # allSequences = set(seqs)           # A set of all sequences
    # ### The differnce of the sets are the sequences without an error
    # correctSequences = list( set.difference(  allSequences ,badSequences ) ) 
    correctSequences = seqs
    t("Collected non-damaged sequences")
    #Build the De Bruign Graph
    graph = deBruijn()
    for s in correctSequences:
        subs = s.subs
        #Expects a sequence of atleast length k + 1
        if len(subs) < 2:
            continue
        graph.add(subs[0])
        for i in range(1, len(s.subs)):
            graph.add(subs[i], subs[i - 1])
    graph.update() #Marks all branching nodes
    fdlNodes = graph.getFDLNodeList()
    for n in fdlNodes:
        x = int( random.random() * width  )
        y = int( random.random() * height  )
        n.addCanvas(canvas, x, y, 1, 1, "green")
    FDL(fdlNodes)

if __name__ == "__main__":
    main()


