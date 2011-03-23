'''
Created on Mar 21, 2011

@author: Lukasz Kreczko

Email: Lukasz.Kreczko@cern.ch
'''
from ROOT import *
#def addToEvent(event, var, value):
#    curr = event
#    
#    vars = var.split('.')
#    var = vars[-1]
#    
#    for token in vars[0:-1]:
#        if not curr.has_key(token):
#            curr[token] = {}
#        curr = curr[token]
#    curr[var] = value

def addMultiVarToEvent(event, var, values):
    curr = event
    if not '.' in var:
        addSimpleMultiVarToEvent(event, var, values)
        return
    vars = var.split('.')
    obj = vars[0]
    var = vars[-1]
    
    if not curr.has_key(obj):
        curr[obj] = []
    
    counter = 1
    for value in values:
        objdict = {}
        for token in vars[1:-1]:
            if not objdict.has_key(token):
                objdict[token] = {}
            objdict = objdict[token]
        objdict[var] = value
        if not len(curr[obj]) >= counter:
            curr[obj].append(objdict)
        else:
            curr[obj][counter - 1].update(objdict)
        counter += 1

def addSimpleMultiVarToEvent(event, var, values):
    if not event.has_key(var):
        event[var] = []
    for value in values:
        event[var].append(value)       

#event = {}
#
#exp1 = {'Electron': {'Track': {'Pt': 10}}}
##exp2 = {'Charge':-1}
##exp3 = {'Electron': {'Charge':-1}}
##
#event.update(exp1)
##event['Electron']['Track'].update(exp2)
##event['Electron'].update(exp2)
##print event
#
#var = 'Electron.Track.Charge'
##exp2 = StringToObject(var, -1)
#
#curr = event
#vars = var.split('.')
#for token in vars[0:-1]:
#    if not curr.has_key(token):
#        curr[token] = {}
#    curr = curr[token]
#curr[vars[-1]] = -1
#
#print event
#
#def addToEvent(var, value):
#    pass

if __name__ == '__main__':
    event = {}
    addMultiVarToEvent(event, 'Electron.Charge', [-1,+1,-1])
    addMultiVarToEvent(event, 'Electron.Pt', [10,20,30])
    addMultiVarToEvent(event, 'HLT', [True,False,True])
#    addToEvent(event, 'Electron.Charge', -1)
#    addToEvent(event, 'Electron.Track.Pt', 20)
#    addToEvent(event, 'Electron.Track.Charge', -1)
    print event
    
