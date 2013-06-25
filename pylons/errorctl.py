# -*- coding: utf-8 -*-
"""
Pylons Base controller with error management

$Id$
"""

from formatter import Formatter

from pylons import response

class HTTPCode(object):
    """
    Class for managing HTTP Error codes
    """
    http_codes = {
            '200': 'OK',
            '201': 'Created',
            '204': 'No Content',

            '300': 'Multiple Choices',
            '301': 'Moved Permanently',
            '303': 'See Other',
            '304': 'Not Modified',
            '307': 'Temporary Redirect',

            '400': 'Bad Request',
            '401': 'Unauthorized',
            '403': 'Forbidden',
            '404': 'Not Found',
            '405': 'Method Not Allowed',
            '409': 'Conflict',
            '412': 'Precondition Failed'
            }
    @classmethod
    def codes(cls):
        return cls.http_codes

    def __init__(self, code, error=None, data=None):
        self.status = code
        self.text = self.http_codes.get(str(code), 'Unknown Error')
        if error:
            self.error = str(error)
        else:
            self.error = self.text
        self.data = data

    def toDict(self):
        return dict(status=self.status,
                text=self.text,
                error=self.error,
                data=self.data)

class ErrorCtl(object):
    """
    To use this class:
        - disable default pylons error management in middleware.py
        - derive BaseController from ErrorCtl
        - use return self.ErrorType in your controller's actions
    """

    def abort(self, code=None, error=None, data=None, format='json'):
        """
        Basic abort code.
        Set status, header and content of response
        """
        h=HTTPCode(code, error, data)
        f = Formatter(h, format=format)
        response.status_int = code
        response.content_type = f.header
        response.unicode_body = unicode(f)
        # response.content = str(f)

    def Ok(self, format='json'):
        return self.abort(200, 'Ok', 'Ok', format)

    def Created(self, format='json'):
        return self.abort(201, 'Created', 'Created', format)

    def BadRequest(self, error=None, data=None, format='json'):
        """
        The request was wrong for some reason.
        """
        return self.abort(400, error, data, format)

    def SQLError(self, data=None, format='json'):
        """
        Some error in SQL processing happened.
        """
        return self.BadRequest('SQL Error', data, format)

    def NoContent(self, error=None, data=None, format='json'):
        """
        There is nothing to display
        """
        return self.abort(204, error, data, format)

    def NotFound(self, error=None, data=None, format='json'):
        """
        No record with that ID exists
        """
        return self.abort(404, error, data, format)

    def Duplicate(self, error=None, data=None, format='json'):
        """
        There is already a record with same parameters
        I.E.: a category with same name or a version with same fingerprint
        """
        return self.abort(409, error, data, format)

    def PreconditionFailed(self, error=None, data=None, format='json'):
        """
        Some necessary parameter is missing.
        Usually returned by a failed form validation
        """
        return self.abort(412, error, data, format)




