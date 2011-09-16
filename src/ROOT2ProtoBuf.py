'''
Created on Jul 13, 2011

@author: Lukasz Kreczko

Email: Lukasz.Kreczko@cern.ch
'''
from optparse import OptionParser
import sys
from ROOT import *
import EventCollection_pb2

import gzip

def fillElectron(electron, data, prefix, index):
    if prefix == 'selectedPatElectrons':
        electron.type = EventCollection_pb2.Electron.Calo
        
    if prefix == 'selectedPatElectronsLoosePFlow':
        electron.type = EventCollection_pb2.Electron.ParticleFlow
        
        
    variables = ['Energy','Px','Py','Pz','Charge','Mass',
                 'Eta', 'Phi', 'Pt', 'CaloEnergy', 'HoE', 'eSeedClusterOverPout', 'EoverP', 'fbrem', 'SigmaEtaEta', 'SigmaIEtaIEta', 
                 'DeltaPhiTrkSC', 'DeltaEtaTrkSC', 'TrkIso03', 'EcalIso03', 'HcalIso03', 'TrkIso', 'EcalIso', 'HcalIso', 'dB', 
                 'closestCtfTrackRef', 'shFracInnerHits', 'EcalIsoHeep', 'HcalIsoD1Heep', 'HcalIsoD2Heep', 'TrkIsoHeep', 'MissingHits', 'Dist', 
                 'DCotTheta', 'SCEta', 'SCPhi', 'SCPt', 'SCRawEnergy', 'VtxIndex', 'VtxDistXY', 'VtxDistZ', 'PassID', 'PfChargedHadronIso', 
                 'PfNeutralHadronIso', 'PFGammaIso'
                 ]
    
    setVar = electron.__setattr__
    getVar = data.__getattr__
    
    for var in variables:
        datavar = prefix + '.' + var
        if hasattr(data, datavar):
            setVar(var, getVar(datavar)[index])
            
    electron.VertexX = getVar(prefix + '.Vertex.X')[index]
    electron.VertexY = getVar(prefix + '.Vertex.Y')[index]
    electron.VertexZ = getVar(prefix + '.Vertex.Z')[index]
    
    electron.GSFTrack.d0 = getVar(prefix + '.GSFTrack.d0')[index]
    electron.GSFTrack.Eta = getVar(prefix + '.GSFTrack.Eta')[index]
    electron.GSFTrack.Phi = getVar(prefix + '.GSFTrack.Phi')[index]
    electron.GSFTrack.Theta = getVar(prefix + '.GSFTrack.Theta')[index]
    electron.GSFTrack.Charge = getVar(prefix + '.GSFTrack.Charge')[index]
    electron.GSFTrack.Pt = getVar(prefix + '.GSFTrack.Pt')[index]

def fillElectrons(event, data):
    nCaloEle = len(data.__getattr__('selectedPatElectrons.Energy'))
    for index in range(0,nCaloEle):
        fillElectron(event.selectedPatElectrons.add(), data, 'selectedPatElectrons', index)
        
    nPFEle = len(data.__getattr__('selectedPatElectronsLoosePFlow.Energy'))
    for index in range(0,nPFEle):
        fillElectron(event.selectedPatElectronsLoosePFlow.add(), data, 'selectedPatElectronsLoosePFlow', index)

def fillMET(met, data, prefix, index):
    if prefix == 'patMETs':
        met.type = EventCollection_pb2.MET.Calo
        
    if prefix == 'patMETsPFlow':
        met.type = EventCollection_pb2.MET.ParticleFlow
        
        
    variables = ['Ex','Ey','Pz', 'ET', 'Phi', 'SumET', 'Significance', 'ETUncorr', 'PhiUncorr', 'SumETUncorr'
                 ]
    
    setVar = met.__setattr__
    getVar = data.__getattr__
    
    for var in variables:
        datavar = prefix + '.' + var
        if hasattr(data, datavar):
            setVar(var, getVar(datavar)[index])

def fillMETs(event, data):
    nCaloMETs = len(data.__getattr__('patMETs.Ex'))
    for index in range(0,nCaloMETs):
        fillMET(event.patMETs.add(), data, 'patMETs', index)
        
    nPFMETs = len(data.__getattr__('patMETsPFlow.Ex'))
    for index in range(0,nPFMETs):
        fillMET(event.patMETsPFlow.add(), data, 'patMETsPFlow', index)

def fillMuon(muon, data, prefix, index):
    if prefix == 'selectedPatMuons':
        muon.type = EventCollection_pb2.Muon.Default
        
    if prefix == 'selectedPatMuonsLoosePFlow':
        muon.type = EventCollection_pb2.Muon.ParticleFlow
        
        
    variables = ['Energy','Px','Py', 'Pz', 'Charge', 'Mass', 
                 'TrkIso03', 'EcalIso03', 'HcalIso03', 'isGoodGlobalMuon', 'PfChargedHadronIso', 'PfNeutralHadronIso', 'PFGammaIso', 
                 'Eta', 'Phi', 'Pt', 'P', 'TrkHits', 'TrkD0', 'TrkD0Error', 'TrkDz', 'TrkDzError', 'GlobalChi2', 'TrkIso', 
                 'EcalIso', 'HcalIso', 'HOIso', 'VtxIndex', 'VtxDistXY', 'VtxDistZ', 'CocktailEta', 'CocktailPhi', 
                 'CocktailPt', 'CocktailP', 'CocktailCharge', 'CocktailTrkHits', 'CocktailTrkD0', 'CocktailTrkD0Error', 
                 'CocktailTrkDz', 'CocktailTrkDzError', 'CocktailGlobalChi2'
                 ]
    
    setVar = muon.__setattr__
    getVar = data.__getattr__
    
    for var in variables:
        datavar = prefix + '.' + var
        if hasattr(data, datavar):
            setVar(var, getVar(datavar)[index])

def fillMuons(event, data):
    nDefMuons = len(data.__getattr__('selectedPatMuons.Energy'))
    for index in range(0,nDefMuons):
        fillMuon(event.selectedPatMuons.add(), data, 'selectedPatMuons', index)
        
    nPFMuons = len(data.__getattr__('selectedPatMuonsLoosePFlow.Energy'))
    for index in range(0,nPFMuons):
        fillMuon(event.selectedPatMuonsLoosePFlow.add(), data, 'selectedPatMuonsLoosePFlow', index)

def fillJet(jet, data, prefix, index):
    if prefix == 'goodPatJets':
        jet.type = EventCollection_pb2.Jet.Calo_AntiKT_Cone05
        
    if prefix == 'goodPatJetsCA8PF':
        jet.type = EventCollection_pb2.Jet.CA08PF
        
    if prefix == 'goodPatJetsPFlow':
        jet.type = EventCollection_pb2.Jet.PF2PAT
        
    variables = ['Energy','Px','Py','Pz','Charge','Mass',
                 'Eta', 'Phi', 'Pt', 'PtRaw', 'EnergyRaw', 'PartonFlavour', 'JECUnc', 'L2L3ResJEC', 'L3AbsJEC', 
                 'L2RelJEC', 'L1OffJEC', 'EMF', 'resEMF', 'HADF', 'n90Hits', 'fHPD', 'fRBX', 'SigmaEta', 'SigmaPhi', 'TrackCountingHighEffBTag', 
                 'TrackCountingHighPurBTag', 'SimpleSecondaryVertexHighEffBTag', 'SimpleSecondaryVertexHighPurBTag', 'JetProbabilityBTag', 
                 'JetBProbabilityBTag', 'SoftElectronBJetTag', 'SoftMuonBJetTag', 'SoftMuonNoIPBJetTag', 'CombinedSVBJetTag', 'CombinedSVMVABJetTag', 
                 'PassLooseID', 'ChargedEmEnergyFraction', 'ChargedHadronEnergyFraction', 'ChargedMuEnergyFraction', 'ElectronEnergyFraction', 
                 'MuonEnergyFraction', 'NeutralEmEnergyFraction', 'NeutralHadronEnergyFraction', 'PhotonEnergyFraction', 
                 'ChargedHadronMultiplicity', 'ChargedMultiplicity', 'ElectronMultiplicity', 'MuonMultiplicity', 'NeutralHadronMultiplicity', 
                 'NeutralMultiplicity', 'PhotonMultiplicity', 'NConstituents', 'ChargedEmEnergyFractionRAW', 'ChargedHadronEnergyFractionRAW', 
                 'NeutralEmEnergyFractionRAW', 'NeutralHadronEnergyFractionRAW']
    
    setVar = jet.__setattr__
    getVar = data.__getattr__
    
    for var in variables:
        datavar = prefix + '.' + var
        if hasattr(data, datavar):
            setVar(var, getVar(datavar)[index])
            
        
    

def fillVertex(vertex, data, prefix, index):
    variables = ['X', 'Y', 'Z', 'XErr', 'YErr', 'ZErr', 'Rho', 'Chi2', 'NDF', 'NTracks', 'NTracksW05', 'IsFake']
    setVar = vertex.__setattr__
    getVar = data.__getattr__
    
    for var in variables:
        datavar = prefix + '.' + var
        if hasattr(data, datavar):
            setVar(var, getVar(datavar)[index])

def fillVertices(event, data):
    nVertex = len(data.__getattr__('goodOfflinePrimaryVertices.NDF'))
    for index in range(0,nVertex):
        fillVertex(event.goodOfflinePrimaryVertices.add(), data, 'goodOfflinePrimaryVertices', index)

def fillJets(event, data):
    ncaloJets =  len(data.__getattr__('goodPatJets.Energy'))
    for index in range(0,ncaloJets):
        fillJet(event.goodPatJets.add(), data, 'goodPatJets', index)
        
    nPF2PATJets = len(data.__getattr__('goodPatJetsPFlow.Energy'))
    for index in range(0,nPF2PATJets):
        fillJet(event.goodPatJetsPFlow.add(), data, 'goodPatJetsPFlow', index)
    
    nPFCA08Jets = len(data.__getattr__('goodPatJetsCA8PF.Energy'))
    for index in range(0,nPFCA08Jets):
        fillJet(event.goodPatJetsCA8PF.add(), data, 'goodPatJetsCA8PF', index)

def fillEvent(event, data):
    getData = data.__getattr__
    setVar = event.__setattr__
    
    variables = ['MagneticField', 'Run', 'Number', 'Bunch', 'LumiSection', 'Orbit', 'Time', 'isData', 'rho']
    
    for var in variables:
        datavar = 'Event.' + var
        if hasattr(data, datavar):
            setVar(var, getData(datavar))
    
    fillJets(event, data)
    fillVertices(event, data)
    fillElectrons(event, data)
    fillMETs(event, data)
    fillMuons(event, data)
    fillBeamSpot(event, data)
    fillTrigger(event, data)

def fillBeamSpot(event, data):
    getData = data.__getattr__
    setVar = event.beamSpot.__setattr__
    
    variables = ['WidthX', 'WidthXError', 'WidthY', 'WidthYError', 'X0', 'X0Error', 'Y0', 'Y0Error', 'Z0', 'Z0Error', 
                 'dxdz', 'dxdzError', 'dydz', 'dydzError', 'sigmaZ', 'sigmaZError']
    for var in variables:
        datavar = 'BeamSpot.' + var
        if hasattr(data, datavar):
            setVar(var, getData(datavar)[0])
        
def fillGenEvent(event, data):
    getData = data.__getattr__

    event.ProcessID = getData('Event.ProcessID')
    event.PtHat = getData('Event.PtHat')
    event.GenMETExTrue.extend(getData('GenMETExTrue'))
    event.GenMETEyTrue.extend(getData('GenMETEyTrue'))
    event.PDFWeights.extend(getData('Event.PDFWeights'))
    event.PileUpInteractions.extend(getData('Event.PileUpInteractions'))
    event.PileUpOriginBX.extend(getData('Event.PileUpOriginBX'))
        
    fillGenParticles(event, data)
    fillGenJets(event, data)
    
def fillGenParticles(event, data):
    nParticles = len(data.__getattr__('GenParticle.Energy'))
    
    for index in range(0, nParticles):
        fillGenParticle(event.genParticles.add(), data, 'GenParticle', index)

def fillGenParticle(particle, data, prefix, index):
    getData = data.__getattr__
    setVar = particle.__setattr__
    
    variables = ['Energy', 'Px', 'Py', 'Pz', 'Charge', 'Mass', 
                 'Eta', 'Phi', 'Pt', 'PdgId', 'VX', 'VY', 'VZ', 
                 'NumDaught', 'MotherIndex', 'Status']
    
    for var in variables:
        datavar = prefix + '.' + var
        if hasattr(data, datavar):
            setVar(var, getData(datavar)[index])

def fillGenJets(event, data):
    njets = len(data.__getattr__('GenJet.Energy'))
    
    for index in range(0, njets):
        fillGenJet(event.genJets.add(), data, 'GenJet', index)
        
def fillGenJet(jet, data, prefix, index):
    getData = data.__getattr__
    setVar = jet.__setattr__
    
    variables = ['Energy', 'Px', 'Py', 'Pz', 'Charge', 'Mass', 
                 'Eta', 'Phi', 'Pt', 'EMF', 'HADF']
    
    for var in variables:
        datavar = prefix + '.' + var
        if hasattr(data, datavar):
            setVar(var, getData(datavar)[index])

def fillTrigger(event, data):
    getData = data.__getattr__
    
    event.trigger.L1PhysBits.extend(getData('Trigger.L1PhysBits'))
    event.trigger.L1TechBits.extend(getData('Trigger.L1TechBits'))
    event.trigger.HLTBits.extend(getData('Trigger.HLTBits'))
    event.trigger.HLTResults.extend(getData('Trigger.HLTResults'))
    event.trigger.HLTNames.extend(getData('Trigger.HLTNames'))
    
def convertROOT(inputfile, outputfile, numberOfEventsPerFile, compressionLevel):
    gROOT.SetBatch(1);
    chain = TChain("rootTupleTree/tree");

    chain.Add(inputfile);
    chain.SetBranchStatus("*", 1);

    vars = [branch.GetName() for branch in chain.GetListOfBranches()]
    eventCounter = 0
    eventCollection = EventCollection_pb2.EventCollection()
    
    nFiles = 0
    maxFiles = 10000000000
    for event in chain:
#        print 'Current file:', nFiles
#        print 'current event in this file', eventCounter
        
        if eventCounter >= numberOfEventsPerFile or nFiles >= maxFiles:
            eventCounter = 0
            #write eventCollection
            f = gzip.open("protofiles/%s_%dEventsPerFile_gzip%d_%07d.event" % (outputfile, numberOfEventsPerFile, compressionLevel, nFiles), "wb",compressionLevel)
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
            if 'Event.ProcessID' in vars:
                fillGenEvent(eventCollection.genEvent.add(), event)
            
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
    parser.add_option("-c", "--compressionLevel", dest="compressionLevel",
                  help="level of compression for the output file", metavar="CPMP", default = 7, type='int')
    (options, args) = parser.parse_args()
    
    
    if not options.inputFile == "" and not options.outputFile == "":
        print 'Using Input File', options.inputFile 
        print 'Using Output File', options.outputFile 
        print 'Using max events per file', options.numberOfEventsPerFile
        print 'Using compression level', options.compressionLevel  
        convertROOT(options.inputFile, options.outputFile, int(options.numberOfEventsPerFile), options.compressionLevel)
        
    
    
    