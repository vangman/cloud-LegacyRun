'''
Created on 2 May 2012

Utility funcions used by other modules

@author: vangelis
'''

    
def list2dic(self, inlist):
    outdic = {}
    for itemdic in inlist:
        for (key, value) in itemdic.iteritems():
            outdic[key]=value
    
    return outdic
        
            