'''
Created on 17 Apr 2012

@author: vangelis
'''

__author__ = 'vangelis'

import web
import json
import os
import time

import Utility

from ApplicationRun import Application
from ApplicationRun import AppState

urls = (
    '/apprun', 'runner',
    '/apprun/output', 'appoutput',
    '/apprun/error', 'apperror',
    '/apprun/stream/([A-Za-z0-9_.\-]+)', 'streamer'
    )

app = Application()

os.chdir(os.environ["APPLICATION_WORKSPACE"])

class runner:
        
    def GET(self):
        msg = {"State": app.getState()}
        return json.dumps(msg) + "\n"

    def PUT(self):        
        # Retrieve and set the storage access options
        try:
            objectStorage = web.ctx.env['HTTP_OBJECT_STORAGE']
        except KeyError:
            # Default object storage if none is defined is Pithos+
            objectStorage = "pithos+"
        
        if objectStorage == "pithos+":
            try:
                storageToken = web.ctx.env['HTTP_STORAGE_TOKEN']
            except KeyError:
                return "Required header STORAGE_TOKEN is needed for storage " + objectStorage + "\n"
        else:
            return "None supported object storage provided" + "\n"
                
            
        app.setStorageOptions(objectStorage, storageToken)
        
        # Retrieve and set the input/output endpoints
        body = web.data()
        decoder = json.JSONDecoder()
        param = decoder.decode(body)
        
        appConfig = param.get("application")
        
        infilelist = appConfig.get("inputFiles")
        outfilelist = appConfig.get("outputFiles")
        streamfilelist = appConfig.get("streamedOutput")
        paramslist = appConfig.get("applicationSpecificParameters")
        
        app.setInputData(Utility.list2dic(infilelist))
        app.setOutputData(Utility.list2dic(outfilelist))
        app.setParams(Utility.list2dic(paramslist))
        app.setStreamedOutput(Utility.list2dic(streamfilelist))
        
        app.setState(AppState.PRIMED)
        
        msg = {"State": app.getState()}
        return json.dumps(msg) + "\n"

    def POST(self):
        try:
            action = web.ctx.env['HTTP_ACTION']
        except KeyError:
            action = None

        if action==None or action=="RUN":
            app.prepareInput()
            app.run()
            
        elif action=="RESET":
            print "Not implemented"
            
        elif action=="SUSPEND":
            print "Not implemented"
            
        else:
            print "No valid action clause provided"
            
        msg = {"State": app.getState()}
        return json.dumps(msg) + "\n"

    def DELETE(self):
        app.kill()
        msg = {"State": app.getState()}
        return json.dumps(msg) + "\n"
    

class appoutput:
    def GET(self):       
        # These headers make it work in browsers
        web.header('Content-type','text/plain')
        
        if app.getState() == AppState.INIT or app.getState() == AppState.PROLOG or app.getState() == AppState.READY:
            yield "No standard output available yet\n"
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
                yield "Standard output not available\n"
                
class apperror:
    def GET(self):      
        # These headers make it work in browsers
        web.header('Content-type','text/plain')
        
        if app.getState() == AppState.INIT or app.getState() == AppState.PROLOG or app.getState() == AppState.READY:
            yield "No standard error available yet\n"
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
                yield "Standard error not available\n"

                
class streamer:
    def GET(self, filename):      
        web.header('Content-type','text/plain')
        
        if app.getState() != AppState.RUNNING and app.getState() != AppState.DONE and app.getState()!=AppState.CLEARED:
            yield "Data not ready for streaming." + "\n"
        else:
            if filename not in app.getStreamedOutput():
                yield "Data not in declared streamed output list" + "\n"
            else:
                try:
                    f = open(filename,"r")
                    eof = False
                    while not eof:
                        line = f.readline()
                        if line!='':
                            yield line
                        else:
                            time.sleep(5)
                except: 
                    yield "Error streaming requested output \n"
            

if __name__ == "__main__":
    webapp = web.application(urls, globals())
    webapp.run()