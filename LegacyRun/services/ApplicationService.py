'''
Created on 17 Apr 2012

@author: vangelis
'''

__author__ = 'vangelis'

import web
import json
import time

from ApplicationRun import Application
from ApplicationRun import AppState

urls = (
    '/apprun', 'runner',
    '/apprun/output', 'appoutput',
    '/apprun/error', 'apperror'
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
        return json.dumps(msg) + "\n"

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
        return json.dumps(msg) + "\n"
    
    def list2dic(self, inlist):
        outdic = {}
        for itemdic in inlist:
            for (key, value) in itemdic.iteritems():
                outdic[key]=value
        
        return outdic

class appoutput:
    def GET(self):
        # These headers make it work in browsers
        web.header('Content-type','text/plain')
        #web.header('Transfer-Encoding','chunked') 
        if app.getState() == AppState.INIT or app.getState() == AppState.PROLOG or app.getState() == AppState.READY:
            yield "File not ready for output"
        else:
            try:
                f = open("/tmp/app-stdout.txt","r")
                eof = False
                while not eof:
                    line = f.readline()
                    if line!='':
                        yield line
                    else:
                        time.sleep(5)
            except: 
                yield "Output not available"
                
class apperror:
    def GET(self):
        # These headers make it work in browsers
        web.header('Content-type','text/plain')
        #web.header('Transfer-Encoding','chunked') 
        if app.getState() == AppState.INIT or app.getState() == AppState.PROLOG or app.getState() == AppState.READY:
            yield "File not ready for error"
        else:
            try:
                f = open("/tmp/app-stderr.txt","r")
                eof = False
                while not eof:
                    line = f.readline()
                    if line!='':
                        yield line
                    else:
                        time.sleep(5)
            except: 
                yield "Error not available"
            

if __name__ == "__main__":
    webapp = web.application(urls, globals())
    webapp.run()