'''
Created on Mar 5, 2011

@author: lkreczko
'''

from ROOT import *
from testDict import addMultiVarToEvent, addSimpleMultiVarToEvent
from couch.Couch import CouchServer

if __name__ == '__main__':
    gROOT.SetBatch(1);
    chain = TChain("rootTupleTree/tree");

    chain.Add("/storage/TopQuarkGroup/mc/fall10_7TeV_v1_e25skim/TTJets_TuneD6T_7TeV-madgraph-tauola_Fall10-START38_V12-v2/nTuple_ttjet_merged_1.root");
    chain.SetBranchStatus("*", 1);

    vars = [branch.GetName() for branch in chain.GetListOfBranches()]
  
    counter = 1
    
    db = CouchServer().connectDatabase('my_analysis')
    
    for event in chain:
        myevent = {}
        for var in vars:
            value = event.__getattr__(var)
            if '.' in var and not 'bool' in str(value):
                addMultiVarToEvent(myevent, var, value)
                
#            if var == 'Vertex.IsFake':
#                print var
#                if value.size() > 0:
#                    print value.size()
#                    
#                    print value.begin()
#                print '\n'.join(dir(value))
#                print value.pop_back()
#                print value.size()
#                help(value)
                
        db.queue(myevent)
        if counter % 10 == 0:
            print counter, ' events done'
            db.commit()
        counter += 1


    db.commit()
    print "I've done something!"
