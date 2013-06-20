# -*- coding: utf-8 -*-
"""
Pylons formatter.

$Id$
"""

# toHTML/toMako
from pylons.templating import render_mako as render
from pylons import response, request, config
import mako

# JSON
try:
    import json
except:
    import simplejson as json

# CSV
import csv
import StringIO

# XML
from xml.dom.minidom import parseString

class Formatter(object):
    """
    Formatter class. Supports JSON, XML, CSV, HTML and TXT formats.
    Usage:
        obj = myClass()
        f=Formatter(obj, format='json')
        f.respond()
    or
        obj = myClass()
        formatResponse(obj, 'json')
    """

    formats = {
            'dict': {
                'fn': 'toDict',
                'type': 'text/plain;charset=utf-8'
                },

            'xml': {
                'fn': 'toXML',
                'type': 'text/xml;charset=utf-8'
                },
            'json': {
                'fn': 'toJSON',
                'type': 'application/json;charset=utf-8'
                },
            'csv': {
                'fn': 'toCSV',
                'type': 'text/csv;charset=utf-8'
                },
            'html': {
                'fn': 'toHTML',
                'type': 'text/html;charset=utf-8'
                },
            'txt': {
                'fn': 'toTXT',
                'type': 'text/plain;charset=utf-8'
                }
            }

    def __init__(self, obj, format='json'):
        if format.lower() in self.formats.keys():
            self.format=format.lower()
        else:
            raise Exception,"format %s not supported" % format

        self.status_int = 200
        self.objDict = self.toDict(obj)

        if isinstance(obj, list): # For XML generation we need to know class name
            if len(obj):
                self.obj_class = obj[0].__class__.__name__
            else:
                self.obj_class = 'null'
        else:
            self.obj_class = obj.__class__.__name__

    def __repr__(self): return "<Formatter(format='%s')>" % self.format

    def __str__(self): return getattr(self, self.formats[self.format]['fn'])()

    @property
    def header(self): return self.formats[self.format]['type']

    def toDict(self, obj=None):
        """
        Basic conversion to dict of an Object
        """
        if hasattr(self, 'objDict'):
            if isinstance(self.objDict, list):
                return '[%s]' % ','.join(map(str, self.objDict))
            else:
                return str(self.objDict)

        if isinstance(obj, list) or isinstance(obj, set):
            return [self.toDict(item) for item in obj]
        elif isinstance(obj, dict):
            newDict={}
            for k,v in obj.items():
                newDict[k]=self.toDict(v)
            return newDict
        elif hasattr(obj, 'toDict'): # Object has a dict method
            try:
                return obj.toDict()
            except:
                pass
        elif hasattr(obj, '__table__'): # Alchemy Object, build dict on the fly
            return dict([(col, getattr(obj, col, None)) for col in obj.__table__.c.keys()])
        elif hasattr(obj, '__dict__'):
            return obj.__dict__ # Fallback
        else:
            return obj
            raise Exception, "Object type '%s' is not supported" % type(obj)

    def toJSON(self):
        """
        If we pass a single record work as toJSONsingle, else cycle all items and call 
        toJSONsingle on them
        """
        if config['debug']:
            return json.dumps(self.objDict, indent=2)
        else:
            return json.dumps(self.objDict)

    def toCSV(self):
        csv.register_dialect('ourdialect', delimiter=';', quoting=csv.QUOTE_NONE)
        fp=StringIO.StringIO()
        csvout = csv.writer(fp, 'ourdialect')
        if isinstance(self.objDict, list):
            csvout.writerow(self.objDict[0].keys())
            csvout.writerows([i.values() for i in self.objDict])
        else:
            csvout.writerow(self.objDict.keys())
            csvout.writerow(self.objDict.values())
        fp.seek(0)
        return fp.read()

   
    def __buildXML(self, root):
        """
        basic converter to XML
        """
        xml = ''
        for key in root.keys():
            if isinstance(root[key], dict):
                xml = '%s\n<%s>%s</%s>\n' % (xml, key, self.__buildXML(root[key]), key)
            elif isinstance(root[key], list):
                xml = '%s<%s>' % (xml, key)
                for item in root[key]:
                    xml = '%s%s' % (xml, self.__buildXML(item))
                xml = '%s</%s>' % (xml, key)
            else:
                value = root[key]
                if isinstance(value, str) or isinstance(value, unicode):
                    value = '<![CDATA[%s]]>' % value
                xml = '%s<%s>%s</%s>\n' % (xml, key, value, key)
        return xml

    def toXML(self):
        className = self.obj_class.lower()
        if isinstance(self.objDict, list):
            d =  {'%ss' % className : [{'%s' % className : i} for i in self.objDict]}
            xml = self.__buildXML(d)
        else:
            xml = self.__buildXML({'%s' % className : self.objDict})
        return '<?xml version="1.0" encoding="UTF-8"?>%s' % xml

    def toHTML(self):
        """
        Return rendered template with filled data
        template name is <controller>_<action>.mako
        If template file is not found return 404
        """

        ctl = request.environ['pylons.routes_dict']['controller']
        act = request.environ['pylons.routes_dict']['action']
        tmpl = "%s_%s.mako" % (ctl, act)
        try:
            return render(tmpl)
        except mako.exceptions.TopLevelLookupException:
            self.status_int = 404
            return """<b>Template '%s' not found</b><p></p>
            Rendering as text<br />
            <pre>%s</pre>""" % (tmpl, self.toTXT())

    def toTXT(self):
        output=[]
        if isinstance(self.objDict, list):
            for d in self.objDict:
                output.append('{\n')
                for k,v in d.items():
                    output.append('%s: %s\n' % (k,v))
                output.append('}\n')
        elif isinstance(self.objDict, dict):
                for k,v in self.objDict.items():
                    output.append('%s: %s\n' % (k,v))
        return ''.join(output)


    # Pylonesque method to setup response
    def respond(self):
        """
        Set Response with correct status and header
        and fill body with data
        """
        response.status_int = self.status_int
        response.content_type = self.header
        response.unicode_body = unicode(self)

    setResponse = respond # Legacy

def formatResponse(obj, format):
    """
    Utility to compact writing of answers in controllers
    @param obj objects we want to format
    @param format output format
    """
    Formatter(obj, format).respond()


