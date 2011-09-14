'''
Created on Mar 5, 2011

@author: lkreczko
'''
from __future__ import division
from ROOT import *
from testDict import addMultiVarToEvent, addSimpleMultiVarToEvent
from couch.Couch import CouchServer

if __name__ == '__main__':
    gROOT.SetBatch(1);
    chain = TChain("rootTupleTree/tree");

    chain.Add("/storage/TopQuarkGroup/mc/fall10_7TeV_v1_e25skim/TTJets_TuneD6T_7TeV-madgraph-tauola_Fall10-START38_V12-v2/nTuple_ttjet_merged_1.root");
    chain.SetBranchStatus("*", 1);

    vars = [branch.GetName() for branch in chain.GetListOfBranches()]
    
    newvars = []
    for var in vars:
        if 'PFElectron' in var:
            newvars.append(var)
        if 'PF2PATJet' in var:
            newvars.append(var)
        if 'PFMET' in var:
            newvars.append(var)
        if 'Vertex.' in var:
            newvars.append(var)
        if 'HLTResult' in var:
            newvars.append(var)  
    vars = newvars
    print vars
    counter = 1
    start = 180
    db = CouchServer().connectDatabase('ttbar')
    totalEvents = chain.GetEntries()
    print 'Total number of events', totalEvents
    
    queue = db.queue
    for event in chain:
        myevent = {}
        getVar = event.__getattr__
        for var in vars:
            value = getVar(var)
            if '.' in var and not 'bool' in str(value):
                addMultiVarToEvent(myevent, var, value)
            elif not '.' in var:
                addSimpleMultiVarToEvent(myevent, var, value)
                
        queue(myevent, viewlist=['analysis/pf_e_count_cut30'])
        if counter % 1000 == 0:
#                db.commit()
            print counter, ' events done (%f.2' % counter/totalEvents*100 , '%)'
        counter += 1


    db.commit()
    print "I've done something!"
