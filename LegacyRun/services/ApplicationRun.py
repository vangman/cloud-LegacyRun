'''
Created on 17 Apr 2012

@author: vangelis
'''

__author__ = 'vangelis'

import subprocess
import sys
import os
import threading

import random
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

class Application:
    queue = 'legacyrun-' + str(random.randint(10000, 99999))

    username = 'guest'
    password = 'guest'

    amqp = {
        'host' : 'dev.rabbitmq.com',
        'port' : 5672,
        'virtual_host' : '/',
        'credentials' : pika.PlainCredentials(username, password)
    }

    def __init__(self):
        (self.channel, self.connection) = self.initQueue()
        self.applicationName = "run.sh"
        self.environment = ""
        self.process = None
        self.monitorThread= None
        self.inputData = None
        self.outputData = None
        #self.inputData = {  "TERRAIN_DOMAIN1":"https://pithos.okeanos.grnet.gr/public/c57vn", \
        #                    "EC_anal_iniz.2d_1deg":"https://pithos.okeanos.grnet.gr/public/b6ptc", \
        #                    "namelist_regrid.input":"https://pithos.okeanos.grnet.gr/public/rtq5j", \
        #                    "namelist_interpf.input":"https://pithos.okeanos.grnet.gr/public/ybtnr", \
        #                    "LANDUSE.TBL":"https://pithos.okeanos.grnet.gr/public/whc88", \
        #                    "mmlif.input":"https://pithos.okeanos.grnet.gr/public/jvcqq"}
                                
        '''self.outputData = { "MMOUT_DOMAIN1_00":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_02":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_03":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_04":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_05":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_06":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_07":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_02":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_03":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_04":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_05":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_06":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_07":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_08":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_09":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_10":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_11":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_12":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_13":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_14":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_15":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_16":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_17":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_18":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_19":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_20":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_21":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_22":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_23":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_24":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_25":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_26":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_27":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_28":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_29":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_30":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_31":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_32":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_33":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_34":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_35":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1", \
                            "MMOUT_DOMAIN1_36":"https://pithos.okeanos.grnet.gr/v1/efloros@grnet.gr/pithos/LEGACYRUN_DATA_REPO/MM5_DATA/OUT_DOMAIN1"
                        }'''
                                
        self.setState(AppState.INIT)


    def initQueue(self):
    # Connect to RabbitMQ
        parameters = pika.ConnectionParameters(**self.amqp)
        connection = BlockingConnection(parameters)
        
        # Open the channel
        channel = connection.channel()
        
        # Declare the queue
        channel.queue_declare(queue=self.queue,
                              durable=True,
                              exclusive=False,
                              auto_delete=False)
    
        print 'Sending notifications to queue: %s' % self.queue

        return (channel, connection)


    def sendNotification(self, msgBody):
        self.channel.basic_publish(exchange='',
                  routing_key=self.queue,
                  body=msgBody,
                  properties=pika.BasicProperties(
                      content_type="text/plain",
                      delivery_mode=1))

    
    def run(self):
        print "Invoking Application"
        if self.applicationName is not None and self.getState() == AppState.READY:
            gocommand = self.environment + self.applicationName
            self.process = subprocess.Popen(gocommand)
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
            for outputFile in self.outputData.keys():
                print "Uploading to object store " + outputFile
                uploadCommand = "curl -s -X PUT -D -  -H \"Content-Type: application/octet-stream\" -H \"X-Auth-Token: x1ujZSFrFRgwCvs22NNiLA==\" -T " + outputFile + " " + self.outputData[outputFile] + "/" + outputFile + "> /dev/null"
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
        
    def monitor(self):
        #print "Now monitoring"
        #while self.process.poll() is None:
        #    (stdout, stderr) = self.process.communicate()
        #    print stdout
            
        self.process.wait()
        exitcode = self.process.returncode
    
        if exitcode == 0:
            self.setState(AppState.DONE)
            self.stageOutput()
        else:
            print "Exit code " + str(exitcode)
            print "Abnormal program termination. Output will not be staged"
            self.setState(AppState.FAILED)
        

# main functions defined for test purposes only
def main(argv):
    app = Application()
    app.prepareInput()
    #app.runBlocking()
    appProcess = app.run() 
    appProcess.wait()
        
    '''while appProcess.poll() is None:
        (stdout, stderr) = appProcess.communicate()
        print stdout

    exitcode = appProcess.returncode

    if exitcode == 0:
        app.setState(AppState.DONE)
        app.stageOutput()
    else:
        print "Exit code " + str(exitcode)
        print "Ubnormal program termination. Output will not be staged"
        app.setState(AppState.FAILED)
    '''
    sys.exit()
    

if __name__ == '__main__':
    main(main(sys.argv[1:]))


