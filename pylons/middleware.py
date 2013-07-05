"""
 Copyright CUBE Gestioni S.r.l. 2010

 Middleware modules

 $Id$

"""
from paste.response import has_header
from paste.wsgilib import intercept_output


class testMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        environ['NEWMID'] = True
        return self.app(environ, start_response)


class ContentLengthMiddleware(object):
    """Adds a content-length header to responses which lack one,
    such as those produced by pylons.middleware.ErrorDocuments
    (primarily a workaround for a bug in varnish:
    http://varnish.projects.linpro.no/ticket/400)
    """
    def __init__(self, app):
        self.app = app

    def needs_content_length(self, status, headers):
        return not has_header(headers, 'content-length')

    def __call__(self, environ, start_response):
        status, headers, body = intercept_output(
            environ, self.app, conditional=self.needs_content_length,
            start_response=start_response)
        if status and len([h for h in headers if h[0] == 'Content-Length']) == 0:
            headers.append(('Content-Length', str(len(body))))
            start_response(status, headers)
            return [body]
        else:
            return body
