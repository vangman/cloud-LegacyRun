'''
Created on 17 Apr 2012

@author: vangelis
'''

__author__ = 'vangelis'

import web
import json

from ApplicationRun import Application
#from ApplicationRun import AppState

urls = (
    '/apprun', 'runner',
#    '/(\w+)', 'handleApplication',
#    '/(\w+)/(\d+)', 'handleInstance',
#    '/(\w+)/(\d+)/input', 'inputData',
#    '/(\w+)/(\d+)/output', 'outputData'
    )

app = Application()

class runner:
        
    def GET(self):
        msg = {"State": app.getState()}
        return json.dumps(msg) + "\n"

    def PUT(self):
        body = web.data()
        decoder = json.JSONDecoder()
        param = decoder.decode(body)
        
        appConfig = param.get("application")
        
        infilelist = appConfig.get("inputFiles")
        outfilelist = appConfig.get("outputFiles")
        
        app.setInputData(self.list2dic(infilelist))
        app.setOutputData(self.list2dic(outfilelist))
        app.prepareInput()
        
        msg = {"State": app.getState()}
        return json.dumps(msg)

    def POST(self):
        #msg = {}
        #body = web.data()
        #decoder = json.JSONDecoder()
        #msg = decoder.decode(body)
        #print msg.get("applicationPath")
        app.run() 
            
        msg = {"State": app.getState()}
        return json.dumps(msg) + "\n"

    def DELETE(self):
        self.app.kill()
        msg = {"State": app.getState()}
        return json.dumps(msg)
    
    def list2dic(self, inlist):
        outdic = {}
        for itemdic in inlist:
            for (key, value) in itemdic.iteritems():
                outdic[key]=value
        
        return outdic

if __name__ == "__main__":
    webapp = web.application(urls, globals())
    webapp.run()