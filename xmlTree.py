# -*- coding: utf8 -*-
"""
 Generic Xml Tree parser. Returns a structure of dictionaries of dictionaries

 Copyright by Andrea Mistrali <am@am.cx>
 $Id$


"""

import xml.etree.ElementTree as et


class xmlTree(object):
    """
    @class xmlTree
    @brief XML Tree parser
    @details Parse a Tree in XML format and return a dictionary of dictionaries/array of dictionaries
    """

    def __init__(self, xml=None):
        self.parsed = {}
        if xml:
            self.parse(xml)

    def __repr__(self):
        return r'<%s()>' % (self.__class__.__name__)

    def parse(self, xml):
        """
        @brief do the parsing
        @param xml XML text to be parsed
        @return Nothing. Populates self.parsed
        """
        x = et.fromstring(xml)
        self._recurse(self.parsed, x)

    def _recurse(self, branch, elem):
        try:
            text = elem.text.strip()
        except:
            text = ''

        if len(elem.getchildren()):  # This is a branch
            if elem.tag in branch:
                if type(branch[elem.tag]) == list:
                    branch[elem.tag].append({})
                else:
                    branch[elem.tag] = [branch[elem.tag], {}]
                toPass = branch[elem.tag][-1]
            else:
                branch[elem.tag] = {}
                toPass = branch[elem.tag]
            for i in elem.getchildren():
                self._recurse(toPass, i)
        else:  # This is a leaf
            if elem.tag in branch:
                if type(branch[elem.tag]) != list:
                    branch[elem.tag] = [branch[elem.tag]]
                branch[elem.tag].append(text)
            else:
                branch[elem.tag] = text
