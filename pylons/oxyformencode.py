# -*- coding: utf-8 -*-
"""
Formencode and custom validators

$Id$
"""

import formencode as f
from formencode import *
from datetime import date, datetime


class ISODateConverter(f.FancyValidator):
    dateformat = '%Y-%m-%d'
    not_empty = False
    messages = {'badFormat': 'Please enter the date in the form %(format)s',
                'empty': "Please enter a value"}

    def _to_python(self, value, state):
        output = None
        try:
            output = date.fromordinal(datetime.strptime(value,
                                                        self.dateformat).toordinal())
        except:
            raise f.Invalid(self.message("badFormat", state,
                                         format=self.dateformat),
                            value, state)
        if not output and self.not_empty is True:
            raise f.Invalid(self.message("empty", state), value, state)
        return output

    def _from_python(self, value, state):
        if value:
            return value.strftime(self.dateformat)
        else:
            return None


class ISODatetimeConverter(f.FancyValidator):
    dateformat = '%Y-%m-%dT%H:%M:%S'
    not_empty = False
    messages = {'badFormat': 'Please enter the date in the form %(format)s',
                'empty': "Please enter a value"}

    def _to_python(self, value, state):
        output = None
        try:
            output = datetime.strptime(value, self.dateformat)
        except:
            raise f.Invalid(self.message("badFormat", state,
                                         format=self.dateformat),
                            value, state)
        if not output and self.not_empty is True:
            raise f.Invalid(self.message("empty", state), value, state)
        return output

    def _from_python(self, value, state):
        if value:
            return value.strftime(self.dateformat)
        else:
            return None
