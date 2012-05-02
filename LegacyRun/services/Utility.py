'''
Created on 2 May 2012

Utility funcions used by other modules

@author: vangelis
'''
import time

def list2dic(inlist):
    outdic = {}
    for itemdic in inlist:
        for (key, value) in itemdic.iteritems():
            outdic[key]=value
    
    return outdic
    
def webStream(infile, refreshrate):
    f = open(infile,"r")
    eof = False
    while not eof:
        line = f.readline()
        if line!='':
            yield line
        else:
            time.sleep(refreshrate)