'''
Created on 17 Apr 2012

@author: vangelis
'''

__author__ = 'vangelis'

import web
import json

from ApplicationRun import Application
from ApplicationRun import AppState

urls = (
    '/apprun', 'runner',
#    '/(\w+)', 'handleApplication',
#    '/(\w+)/(\d+)', 'handleInstance',
#    '/(\w+)/(\d+)/input', 'inputData',
#    '/(\w+)/(\d+)/output', 'outputData'
    )

globalApp = Application()

class runner:
    
    def __init__(self):
        self.app = globalApp
        
    def GET(self):
        msg = {"State": self.app.getState()}
        return json.dumps(msg)

    def PUT(self):
        self.app.prepareInput()
        return "Preparing input"
        

    def POST(self):
        #msg = {}
        body = web.data()
        decoder = json.JSONDecoder()
        #msg = decoder.decode(body)
        #print msg.get("applicationPath")
        appProcess = self.app.run() 
            
        msg = {"State": self.app.getState()}
        
        return json.dumps(msg)

    def DELETE(self):
        self.app.kill()
        return "Killed application"

if __name__ == "__main__":
    webapp = web.application(urls, globals())
    webapp.run()