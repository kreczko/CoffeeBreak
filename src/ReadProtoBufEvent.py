'''
Created on 15 Sep 2011

@author: kreczko
'''
import EventCollection_pb2
from optparse import OptionParser
import gzip

def ListEvents(eventCollection):
    for event in eventCollection.event:
        print "Event"
        print "  Number:", event.Number
        print "  Run:", event.Run
        if event.HasField('rho'):
            print "  Rho:", event.rho
            
        print "  MagneticField:", event.MagneticField
        print "  Bunch:", event.Bunch
        print "  LumiSection:", event.LumiSection
        print "  Orbit:", event.Orbit
        print "  Time:", event.Time
        print "  isData:", event.isData
        
        
        print 'Number of goodPatJets:', len(event.goodPatJets)
        print 'Number of goodPatJetsPFlow:', len(event.goodPatJetsPFlow)
        print 'Number of goodPatJetsCA8PF:', len(event.goodPatJetsCA8PF)
        #electrons
        print 'Number of selectedPatElectrons:', len(event.selectedPatElectrons)
        print 'Number of selectedPatElectronsLoosePFlow:', len(event.selectedPatElectronsLoosePFlow)
        #vertices
        print 'Number of goodOfflinePrimaryVertices:', len(event.goodOfflinePrimaryVertices)
        #muons
        print 'Number of selectedPatMuons:', len(event.selectedPatMuons)
        print 'Number of selectedPatMuonsLoosePFlow:', len(event.selectedPatMuonsLoosePFlow)
        #MET
        print ' patMETs:', event.patMETs[0]
        print ' patMETsPFlow:', event.patMETsPFlow[0]
        #Beamspot & trigger
        ListBeamSpot(event.beamSpot)
        ListTrigger(event.trigger)
        
#        ListJets(event.goodPatJets)
            
def ListJets(jets):
    for jet in jets:
        print 'Jet'
        print '   Energy:', jet.Energy
        print '   px:', jet.Px
        print '   py:', jet.Py
        print '   pz:', jet.Pz
        print '   charge:', jet.Charge
        print '   mass:', jet.Mass
        print '   ChargedMultiplicity:', jet.ChargedMultiplicity
        
def ListTrigger(trigger):
    if len(trigger.HLTResults) > 0:
        print 'trigger present'
    else:
        print 'trigger not present'

def ListBeamSpot(spot):
    if spot.X0:
        print 'beamspot present'
    else:
        print 'beamspot not present'

def ListGenEvents(eventCollection):
    for event in eventCollection.genEvent:
        print "GenEvent"
        print "  ProcessID:", event.ProcessID
        print "  PtHat:", event.PtHat
        print "  GenMetExTrue:", event.GenMETExTrue
        print "  GenMetEyTrue:", event.GenMETEyTrue
        
        
        print 'Number of PDFWeights:', len(event.PDFWeights)
        print 'Number of PileUpInteractions:', len(event.PileUpInteractions)
        print 'Number of PileUpOriginBX:', len(event.PileUpOriginBX)
        #jets
        print 'Number of genJets:', len(event.genJets)
        #particles
        print 'Number of genParticles:', len(event.genParticles)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-i", "--inputFile", dest="inputFile",
                  help="read data from FILE", metavar="IFILE")
    (options, args) = parser.parse_args()
    if not options.inputFile == "":
        eventCollection = EventCollection_pb2.EventCollection()
        #    Read the existing address book.
        f = gzip.open(options.inputFile, "rb")
        eventCollection.ParseFromString(f.read())
        f.close()

        ListEvents(eventCollection)
        ListGenEvents(eventCollection)