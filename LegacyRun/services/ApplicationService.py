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
    '/apprun/stream/([A-Za-z0-9_.\-]+)', 'streamer',
    '/apprun/myself', 'myself',
    '/apprun/info', 'appinfo',
    '/apprun/profiler', 'profiler',
    '/apprun/parameters', 'parameters'
    )

app = Application()

os.chdir(os.environ["APPLICATION_WORKSPACE"])

class runner:
        
    def GET(self):
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
            app.reset()
            
        elif action=="SUSPEND":
            app.suspend()
            
        elif action=="RESUME":
            app.resume()
            
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
                    
class myself:
    '''
    Self methods should invoked only from inside the host itself
    '''
    def POST(self):
        if web.ctx.env['REMOTE_ADDR']!="127.0.0.1":
            msg = {"Result":"Only local application can call this method"}
            return json.dumps(msg) + '\n'
            
        try:
            action = web.ctx.env['HTTP_ACTION']
        except KeyError:
            action = None
            
        if action==None or action=="NEXTSTEP":
            if app.getState==AppState.RUNNING:
                app.increaseStep()
                msg = {"Result": "Success"}
            else:
                msg = {"Result": "Not in running state"}
        else:
            msg = {"Result": "Fail"}
        
        return json.dumps(msg) + "\n"
    
class appinfo:
    '''
    Returns textual information about the application
    '''
    def GET(self):
        msg = {"Application":"Application"}
        return json.dumps(msg) + '\n'
    
class profiler:
    '''
    Returns performance information of a completed application run
    '''
    def GET(self):
        msg = {"Performance":"Performance"}
        return json.dumps(msg) + '\n'
    
class parameters:
    '''
    Handles the application runtime parameters resource
    '''
    def PUT(self):        
        # Retrieve and set the storage access options
        try:
            objectStorage = web.ctx.env['HTTP_OBJECT_STORAGE']
        except KeyError:
            # Default object storage if none is defined is Pithos+
            objectStorage = None
        
        if objectStorage == "pithos+":
            try:
                storageToken = web.ctx.env['HTTP_STORAGE_TOKEN']
            except KeyError:
                return "Required header STORAGE_TOKEN is needed for storage " + objectStorage + "\n"
        else:
            storageToken = None
            
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
        
        app.setMetaConfiguration(param)
        
        app.setState(AppState.PRIMED)
        
        msg = {"State": app.getState()}
        return json.dumps(msg) + "\n"

    def GET(self):
        return json.dumps(app.getMetaConfiguration(), sort_keys=True, indent=4) + "\n"
    
    def DELETE(self):
        # We should be able to delete the parameters during PRIMED state and bring the application back to init state
        return "Not implemented"
            

if __name__ == "__main__":
    webapp = web.application(urls, globals())
    webapp.run()