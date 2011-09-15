'''
Created on 15 Sep 2011

@author: kreczko
'''
import EventCollection_pb2
from optparse import OptionParser

def ListEvents(eventCollection):
    for event in eventCollection.event:
        print "Event"
        print "  Number:", event.Number
        print "  Run:", event.Run
        if event.HasField('rho'):
            print "  Rho:", event.rho
        ListJets(event.goodPatJets)
            
def ListJets(jets):
    for jet in jets:
        print 'Jet'
        print '   Energy:', jet.basic.fourVector.energy
        print '   px:', jet.basic.fourVector.px
        print '   py:', jet.basic.fourVector.py
        print '   pz:', jet.basic.fourVector.pz
        print '   charge:', jet.basic.charge
        print '   mass:', jet.basic.mass
        print '   ChargedMultiplicity:', jet.ChargedMultiplicity
      
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i", "--inputFile", dest="inputFile",
                  help="read data from FILE", metavar="IFILE")
    (options, args) = parser.parse_args()
    if not options.inputFile == "":
        eventCollection = EventCollection_pb2.EventCollection()
        #    Read the existing address book.
        f = open(options.inputFile, "rb")
        eventCollection.ParseFromString(f.read())
        f.close()

        ListEvents(eventCollection)