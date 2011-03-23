'''
Created on Mar 16, 2011

@author: Lukasz Kreczko

Email: Lukasz.Kreczko@cern.ch
'''

def StringToObject(str, value):
    if '.' in str:
        result = {}
        token = str.split('.')[0]
        newStr = str.replace(token + '.', '')
        result[token] = StringToObject(newStr, value)
    else:
        result = {str:value}
    
    return result


def groupObjects(listOfObjects):
    pass