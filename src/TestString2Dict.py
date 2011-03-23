'''
Created on Mar 16, 2011

@author: lkreczko
'''
import unittest
from String2Dict import StringToObject, groupObjects

class Test(unittest.TestCase):


    def testStringToObject(self):
        s = 'Electron.Track.Et'
        exp = {'Electron': {'Track': {'Et': 10}}}
        self.assertEquals(exp, StringToObject(s, 10))

    def testStringToVar(self):
        s = 'run'
        exp = {'run': 1}
        self.assertEquals(exp, StringToObject(s, 1))
        
        
    def testGroupSameObjects(self):
        s1 = 'Electron.Track.Pt'
        s2 = 'Electron.Track.Eta'
        s3 = 'Electron.Pt'
        s4 = 'run'
        s5 = 'Muon.Eta'
        s6 = 'Muon.Pt'
        all = [s1, s2, s3, s4, s5, s6]
#        obj1 = {'Electron': {'Pt': 20}}
#        obj2 = {'Electron': {'Track': {'Eta': 10}}}
#        obj3 = {'Electron': {'Track': {'Phi': 1}}}
        exp = {'Electron': [{'Track': ['Pt', 'Eta']}, 'Pt'], 'run': [], 'Muon':['Eta', 'Pt']}
#        listOfObjects = [obj1, obj2, obj3]
        self.assertEquals(exp, groupObjects(all))

if __name__ == "__main__":
    import sys;sys.argv = ['', 'Test.testName']
    unittest.main()