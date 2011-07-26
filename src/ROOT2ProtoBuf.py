'''
Created on Jul 13, 2011

@author: Lukasz Kreczko

Email: Lukasz.Kreczko@cern.ch
'''
from optparse import OptionParser
import sys
from ROOT import *

def getEventCollection(file):
    pass

def addEvent(eventCollection):
    pass

def fillElectron(electron, vars, index):
    pass

def fillJet(electron, vars, index):
    pass

def fillVertex(vertex, vars, index):
    pass

def readROOT(file):
    gROOT.SetBatch(1);
    chain = TChain("rootTupleTree/tree");

    chain.Add(file);
    chain.SetBranchStatus("*", 1);

    vars = [branch.GetName() for branch in chain.GetListOfBranches()]
#main
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i", "--inputFile", dest="inputFile",
                  help="read data from FILE", metavar="FILE")
    parser.add_option("-o", "--outputFile", dest="outputFile",
                  help="write data into FILE", metavar="FILE")
    parser.add_option("-s", "--outputFileSize", dest="outputFileSize",
                  help="maximal file size of FILE", metavar="FILE", default = 900000)
    (options, args) = parser.parse_args()
    
#    if options != 3:
#        print "Usage:", sys.argv[0], "ROOT_INPUT_FILE", "ProtoBuf_OUTPUT_FILE"
#        sys.exit(-1)
    