'''
Created on 12 May 2012

@author: vangelis
'''

import web

from FileResource import FileResource
from urlparse import parse_qs


urls = (
    '/file', 'filemanager',
    '/file/([A-Za-z0-9]+)', 'instanceManager'
)

files = {}


class filemanager:
    def POST(self):
        fileResource = FileResource()
        files[fileResource.id] = fileResource

        return fileResource.id + "\n"

    def GET(self):
        for fileResource in files:
            yield fileResource + "\n"

    def PUT(self):
        return "Not implemented\n"

    def DELETE(self):
        return "Not implemented\n"


class instanceManager:
    def GET(self, fileid):
        web.header('Content-type', 'text/plain')

        try:
            yield "File " + files[fileid].getID() + "\n"
        except KeyError:
            yield "No such file\n"

    def PUT(self, fileid):
        """
        Appends file object with a new version of a real file. URL of the target file is passed as query string
        :param fileid: id of the file to act upon
        """
        try:
            querystring = parse_qs(web.ctx.env['QUERY_STRING'])
            url = querystring['url']
            files[fileid].put(url)
        except KeyError:
            yield "No such file\n"


if __name__ == "__main__":
    webapp = web.application(urls, globals())
    webapp.run()