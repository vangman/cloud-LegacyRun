'''
Created on 12 May 2012

@author: vangelis
'''

import web

urls = (
    '/file', 'filemanager'
    )

class filemanager:
    def GET(self):
        return "Not implemented\n"
    
    def PUT(self):
        return "Not implemented\n"
    
    def DELETE(self):
        return "Not implemented\n"
    
if __name__ == "__main__":
    webapp = web.application(urls, globals())
    webapp.run()