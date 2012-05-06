'''
Created on 17 Apr 2012

@author: vangelis
'''

__author__ = 'vangelis'

import subprocess
import signal
import os
import threading
import socket
import traceback
import json

import pika
from pika.adapters import BlockingConnection

class AppState:
    READY = "READY" # Input data staged in and application is ready to run
    INIT = "INIT"  # Application is in initialization phase
    PRIMED = "PRIMED" # Application has been provided all configuration and data dependency information 
    RUNNING = "RUNNING" # Application is running
    PROLOG = "PROLOG" # Input data are being staged locally from the source location
    SUSPENDED = "SUSPENDED" # Application is suspended
    FAILED = "FAILED" # Application failed 
    ABORTED = "ABORTED" # Application was terminated after user intervention 
    DONE = "DONE" # Application has completed
    CLEARED = "CLEARED" # Output data has been staged out to external storage
    EPILOGUE = "EPILOGUE" # Output data is being staged to external storage

class AppHooks:
    RUN = "__lr_run"
    CLEAR = "__lr_clear"
    
class Application:
    
    # Message broker information should be defined on instantiation. Should the user be able to alter this during
    # execution time?
    username = 'vangelis'
    password = 'verifym9'
 
    amqp = {
        'host' : 'vm035.grnet.stratuslab.eu',
        'port' : 5672,
        'virtual_host' : '/',
        'credentials' : pika.PlainCredentials(username, password)
    }
    
    queue = 'lr-'+socket.gethostname()
    
    def __init__(self):
        #self.queue = 'lr-'+socket.gethostname()
        (self.channel, self.connection) = self.initQueue()
        
        self.step = 0
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
        except Exception:
            print 'No notifications queue could be activated'
            traceback.print_tb()
            channel = connection = None

        return (channel, connection)
    
    def build_json_notification(self, msg):
        msg = {"STEP": self.getStep(), "STATE": self.getState(), "TAG": msg}
        return json.dumps(msg)
    
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
        if self.getState() == AppState.READY:
            # Prepare shell environment
            self.prepareEnvironment()
            
            # Prepare stdout and stderr redirections
            self.stdout = open("/tmp/app-stdout.txt", "w+")
            self.stderr = open("/tmp/app-stderr.txt", "w+")
            
            # Start the process
            self.process = subprocess.Popen(AppHooks.RUN, stdout=self.stdout, stderr=self.stderr)
            
            self.increaseStep()
            self.setState(AppState.RUNNING)
            
            # Start the monitoring thread
            self.monitorThread = threading.Thread(target=self.monitor, args=())
            self.monitorThread.start()
            
            return self.process
        else:
            return None

    def runBlocking(self):
        if self.getState() == AppState.READY:
            try:
                self.setState(AppState.RUNNING)
                os.system(AppHooks.RUN)
                self.setState(AppState.DONE)
            except:
                print "WARNING: Run hook could not be found"
                self.setState(AppState.READY)
            

    def prepareInput(self):
        if self.getState() == AppState.PRIMED:
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
        notification = self.build_json_notification("STATE CHANGE")
        self.sendNotification(notification)
        

    def kill(self):
        if self.process is not None and self.getState()==AppState.RUNNING:
            self.process.kill()
            self.setState(AppState.ABORTED)
            return True
        else:
            return False

    def terminate(self):
        if self.process is not None and self.getState()==AppState.RUNNING:
            self.process.terminate()
            self.setState(AppState.ABORTED)
            return True
        else:
            return False
        
    def suspend(self):
        if self.process is not None and self.getState()==AppState.RUNNING:
            self.process.send_signal(signal.SIGSTOP)
            self.setState(AppState.SUSPENDED)
            
    def resume(self):
        if self.process is not None and self.getState()==AppState.SUSPENDED:
            self.process.send_signal(signal.SIGCONT)
            self.setState(AppState.RUNNING)
            
    def reset(self):
        if self.getState()==AppState.SUSPENDED or self.getState()==AppState.ABORTED or self.getState()==AppState.FAILED or self.getState()==AppState.CLEARED:
            self.__init__()
            # execute the clear() hook
            try:
                os.system(AppHooks.CLEAR)
            except:
                print "WARNING: No local clear hook available"
        
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
            if self.getState()!=AppState.ABORTED:
                print "Exit code " + str(exitcode)
                print "Unexpected program termination. Output will not be staged"
                self.setState(AppState.FAILED)
            else:
                print "Terminated by User"
        
    def prepareEnvironment(self):
        if self.params is not None:
            for parameter in self.params.keys():
                os.environ[parameter]=self.params[parameter]
                
    def increaseStep(self):
        self.step += 1
        
    def resetStep(self):
        self.step=0
        
    def getStep(self):
        return self.step
        
    
                


