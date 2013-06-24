'''
Created on 2 May 2012

Utility funcions used by other modules

@author: vangelis
'''

import string
import random
    
def list2dic(inlist):
    outdic = {}
    for itemdic in inlist:
        for (key, value) in itemdic.iteritems():
            outdic[key]=value
    
    return outdic

def id_generator(size=20, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))
        
            