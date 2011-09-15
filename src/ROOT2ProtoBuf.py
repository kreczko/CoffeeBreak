'''
Created on Jul 13, 2011

@author: Lukasz Kreczko

Email: Lukasz.Kreczko@cern.ch
'''
from optparse import OptionParser
import sys
from ROOT import *
import EventCollection_pb2

def fillElectron(electron, data, index):
    pass

def fillJet(jet, data,prefix, index):
    getVar = data.__getattr__
    energy = getVar('goodPatJets.Energy')[index]
    px = getVar('goodPatJets.Px')[index]
    py = getVar('goodPatJets.Py')[index]
    pz = getVar('goodPatJets.Pz')[index]
    
    fourVector = jet.basic.fourVector
    fourVector.energy = energy
    fourVector.px = px
    fourVector.py = py
    fourVector.pz = pz

def fillVertex(vertex, data, index):
    pass

def fillJets(event, data):
    ncaloJets =  len(data.__getattr__('goodPatJets.Energy'))
    for index in range(0,ncaloJets):
        fillJet(event.goodPatJets.add(), data, 'goodPatJets', index)

def fillEvent(event, data):
    getData = data.__getattr__
    setVar = event.__setattr__
    
    variables = ['MagneticField', 'Run', 'Number', 'Bunch', 'LumiSection', 'Orbit', 'Time', 'isData', 'rho']
    
    for var in variables:
        setVar(var, getData('Event.' + var))
    
    fillJets(event, data)

def fillGenEvent(event, data):
    pass

def convertROOT(inputfile, outputfile, numberOfEventsPerFile):
    gROOT.SetBatch(1);
    chain = TChain("rootTupleTree/tree");

    chain.Add(inputfile);
    chain.SetBranchStatus("*", 1);

    vars = [branch.GetName() for branch in chain.GetListOfBranches()]
    eventCounter = 0
    eventCollection = EventCollection_pb2.EventCollection()
    
    nFiles = 0
    maxFiles = 10
    for event in chain:
        if eventCounter >= numberOfEventsPerFile or nFiles >= maxFiles:
            eventCounter = 0
            #write eventCollection
            f = open("protofiles/%s_%07d.event" % (outputfile, nFiles), "wb")
            f.write(eventCollection.SerializeToString())
            f.close()
            #create new eventCollection 
            eventCollection = EventCollection_pb2.EventCollection()
            nFiles += 1
            if nFiles >= maxFiles:
                break;
        else:
            #add event content
            fillEvent(eventCollection.event.add(), event)
            #if 'ProcessID' in vars:
            #    fillGenEvent(eventCollection.event.add(), data)
            
            eventCounter += 1
            
            
#main
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i", "--inputFile", dest="inputFile",
                  help="read data from FILE", metavar="IFILE")
    parser.add_option("-o", "--outputFile", dest="outputFile",
                  help="write data into FILE", metavar="OFILE", default = "test")
    parser.add_option("-n", "--numberOfEventsPerFile", dest="numberOfEventsPerFile",
                  help="maximal number of events in outputfile", metavar="NEVT", default = 1)
    (options, args) = parser.parse_args()
    
    if not options.inputFile == "" and not options.outputFile == "":
        convertROOT(options.inputFile, options.outputFile, options.numberOfEventsPerFile)
        
    
    
    