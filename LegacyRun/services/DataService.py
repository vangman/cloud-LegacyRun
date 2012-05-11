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
        return "No data \n"
    
if __name__ == "__main__":
    webapp = web.application(urls, globals())
    webapp.run()