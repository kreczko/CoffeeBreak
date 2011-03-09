'''
Created on Mar 5, 2011

@author: lkreczko
'''

from ROOT import *

class Event:
    def __init__(self, eventNumber, run, lumisection):
        self.number = eventNumber
        self.run = run
        self.lumiSection = lumisection
        
        self.electrons = []
    
    def json(self):
        js = {'run':self.run, 'event': self.number, 'lumiSection': self.lumiSection}
        jsElectrons = []
        app = jsElectrons.append
        for electron in self.electrons:
            app(electron.json())
        js['electrons'] = jsElectrons
        return js
    
class Particle:
    def __init__(self, energy, px, py, pz):
        self.energy = energy
        self.px = px
        self.py = py
        self.pz = pz
        
        self.mass = 0
        self.charge = 0
        
    def json(self):
        js = {'energy': self.energy, 'px':self.px, 'py':self.py, 'pz':self.pz}
        js['mass'] = self.mass
        js['charge'] = self.charge
        return js
        
class Electron(Particle):
    def __init__(self, energy, px, py, pz):
        Particle.__init__(self, energy, px, py, pz)
        
        self.d0 = 0
        
    def json(self):
        js = Particle.json(self)
        js['d0'] = self.d0
        return js



if __name__ == '__main__':
    gROOT.SetBatch(1);
    chain = TChain("rootTupleTree/tree");

    chain.Add("/storage/top/mc/fall10_7TeV_v1_e25skim/TTJets_TuneD6T_7TeV-madgraph-tauola_Fall10-START38_V12-v2/nTuple_ttjet_merged_1.root");
    chain.SetBranchStatus("*", 0);

    chain.SetBranchStatus("Electron.Energy", 1);
#    chain.SetBranchStatus("els_px", 1);
#    chain.SetBranchStatus("els_py", 1);
#    chain.SetBranchStatus("els_pz", 1);
    chain.SetBranchStatus("run", 1);
#    chain.SetBranchStatus("lumiBlock", 1);
#    chain.SetBranchStatus("event", 1);
#    chain.SetBranchStatus("Nels", 1);
    
    print chain.GetEntries()
    events = []
    app = events.append
    chain.Print()
#    for event in chain:
##        pass
##        print event.__getattr__('run')
#        print len(event.__getattr__('Electron.Energy'))
#        print len(event.Electron.Energy())
#        #print event.Electron.Energy
#        ev = Event(event.event, event.run, event.lumiBlock)
#        for electron in range(0, event.Nels):
#            ev.electrons.append(Electron(event.els_energy[electron], event.els_px[electron], event.els_py[electron], event.els_pz[electron]))
#        app(ev)
    
#    i = 0
#    for event in events:
#        if i> 10:
#            break;
#        i+= 1
#        print event.json()
