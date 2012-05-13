'''
Created on 13 May 2012

@author: vangelis
'''

class FileInstance(object):

    def __init__(self):
        self.id = None # URL
        self.version = None # String or Number
        self.context = {} # Context of file creation. Application running state
        
    def get(self):
        return file
    
    def put(self):
        return self.version, self.id
    
    def getID(self):
        return self.id
    
    def setID(self, newid):
        self.id = newid

    def setContext(self, context):
        self.context = context
        
    def getContext(self):
        return self.context
    
    def setVersion(self, newversion):
        self.version = newversion
        
    
    
class FileResource(object):

    def __init__(self):
        self.id = None
        self.versions = None # Array of file versions
        self.context = {} # Context of provider application. Configuration parameters
        
    def get(self, version):
        if version==None:
            return latest
        else:
            return version
        
    def put(self):
        copy file on destination
    

        