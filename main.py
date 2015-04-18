from sys import argv
fileIndex = 1
kIndex = 2

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