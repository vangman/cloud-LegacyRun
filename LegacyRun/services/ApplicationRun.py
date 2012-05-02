'''
Created on 17 Apr 2012

@author: vangelis
'''

__author__ = 'vangelis'

import subprocess
import os
import threading
import socket

import pika
from pika.adapters import BlockingConnection

class AppState:
    READY = "READY"
    INIT = "INIT" 
    RUNNING = "RUNNING"
    PROLOG = "PROLOG"
    SUSPENDED = "SUSPENDED"
    FAILED = "FAILED"
    KILLED = "KILLED"
    DONE = "DONE"
    CLEARED = "CLEARED"
    EPILOGUE = "EPILOGUE"

class Application:
    

    username = 'vangelis'
    password = 'verifym9'
 
    amqp = {
        'host' : 'vm035.grnet.stratuslab.eu',
        'port' : 5672,
        'virtual_host' : '/',
        'credentials' : pika.PlainCredentials(username, password)
    }
    
    def __init__(self):
        self.queue = 'lr.'+socket.gethostname()
        (self.channel, self.connection) = self.initQueue()
        self.applicationName = "run.sh"
        self.environment = ""
        self.process = None
        self.monitorThread= None
        self.inputData = None
        self.outputData = None
        self.params = None
        self.streamedData = None
        self.stdout = None
        self.stderr = None
        print "Initializing..."
        self.setState(AppState.INIT)


    def initQueue(self):
    # Connect to RabbitMQ
        try:
            parameters = pika.ConnectionParameters(**self.amqp)
            connection = BlockingConnection(parameters)
            
            # Open the channel
            channel = connection.channel()
            
            # Declare the queue
            channel.queue_declare(queue=self.queue,
                                  durable=False,
                                  exclusive=False,
                                  auto_delete=True)
        
            print 'Sending notifications to queue: %s' % self.queue
        except Exception as exc:
            print 'No notifications queue could be activated'
            print exc
            channel = connection = None

        return (channel, connection)
    
    def setStorageOptions(self, storageType, storageToken):
        # Actually only pithos is supported at this time
        self.storageType = storageType
        self.storageToken = storageToken


    def sendNotification(self, msgBody):
        if self.channel is not None:
            self.channel.basic_publish(exchange='',
                      routing_key=self.queue,
                      body=msgBody,
                      properties=pika.BasicProperties(
                          content_type="text/plain",
                          delivery_mode=1))

    
    def run(self):
        if self.applicationName is not None and self.getState() == AppState.READY:
            # Prepare shell environment
            self.prepareEnvironment()
            
            # Prepare stdout and stderr redirections
            self.stdout = open("/tmp/app-stdout.txt", "w+")
            self.stderr = open("/tmp/app-stderr.txt", "w+")
            
            # Start the process
            gocommand = self.environment + self.applicationName
            self.process = subprocess.Popen(gocommand, stdout=self.stdout, stderr=self.stderr)
            self.setState(AppState.RUNNING)
            
            # Start the monitoring thread
            self.monitorThread = threading.Thread(target=self.monitor, args=())
            self.monitorThread.start()
            
            return self.process
        else:
            return None

    def runBlocking(self):
        if self.getState() == AppState.INIT:
            if self.applicationName is not None:
                gocommand = self.environment + self.applicationName
                self.setState(AppState.RUNNING)
                os.system(gocommand)
            self.setState(AppState.DONE)

    def prepareInput(self):
        if self.getState() == AppState.INIT:
            self.setState(AppState.PROLOG)
            for inputFile in self.inputData.keys():
                print "Downloading " + self.inputData[inputFile]
                downloadCommand = "curl -s " + self.inputData[inputFile] + " -o " + inputFile
                os.system(downloadCommand)
            self.setState(AppState.READY)
            
    def stageOutput(self):
        if self.getState() == AppState.DONE:
            self.setState(AppState.EPILOGUE)
            for outputFile in self.outputData.keys():
                print "Uploading to object store " + outputFile
                uploadCommand = "curl -s -X PUT -D -  -H \"Content-Type: application/octet-stream\" -H \"X-Auth-Token: " + self.storageToken +"\" -T " + outputFile + " " + self.outputData[outputFile] + "/" + outputFile + "> /dev/null"
                os.system(uploadCommand)
            self.setState(AppState.CLEARED)
            
    def poll(self):
        return self.process.poll()

    def getState(self):
        return self.state

    def setState(self, newState):
        self.state = newState
        self.sendNotification(self.state)

    def kill(self):
        if self.process is not None:
            self.process.kill()
            self.setState(AppState.KILLED)
            return True
        else:
            return False

    def setInputData(self, dataref):
        self.inputData = dataref

    def setOutputData(self, dataref):
        self.outputData = dataref
        
    def setParams(self, paramsList):
        self.params = paramsList
        
    def setStreamedOutput(self, streamedlist):
        self.streamedData = streamedlist
        
    def getStreamedOutput(self):
        return self.streamedData
    
    def monitor(self):
        self.process.wait()
        exitcode = self.process.returncode
    
        if exitcode == 0:
            self.setState(AppState.DONE)
            self.stageOutput()
        else:
            print "Exit code " + str(exitcode)
            print "Unexpected program termination. Output will not be staged"
            self.setState(AppState.FAILED)
        
    def prepareEnvironment(self):
        if self.params is not None:
            for parameter in self.params.keys():
                os.environ[parameter]=self.params[parameter]
                


