#-*- coding: latin-1 -*-

"""

@brief Oxysoft standard library
Custom types

$Id$
"""
__headUrl__  = '$HeadURL$'

import decimal as dc

# *************************************************************************** #
# Custom types
# *************************************************************************** #
class sdict(dict):
    """
    An sdict can be instanciated either from a python dict
    or an instance object (eg. SQL recordsets) and it ensures that you can
    do all the convenient lookups such as x.first_name, x['first_name'] or
    x.get('first_name').

    Examples:
        y= sdict(name='Peter', age=25)
        x= sdict({'name':'Peter', 'age':25})
        class C:
            def __init__(self, name, age):
                self.name = name
                self.age = age

        c = C('Peter', 25)
        z = sdict(c)
    """

    def __init__(self, *args, **kwargs):
         from types import DictType, InstanceType
         if args:
            if type(args[0]) is DictType:
                kwargs.update(args[0])
            elif type(args[0]) is InstanceType:
                kwargs.update(args[0].__dict__)
            elif hasattr(args[0], '__class__') and args[0].__class__.__name__=='sdict':
                kwargs.update(args[0].items())

         dict.__init__(self, **kwargs)

    def __setattr__(self,attr,value):
         self[attr] = value

    def __getattr__(self,attr):
        if self.has_key(attr):
            return self.get(attr)
        else:
            raise AttributeError

    def __deepcopy__(self, memo={}):
         from copy import deepcopy
         mycls = self.__class__
         newObj = mycls.__new__(mycls)
         memo[id(self)] = newObj

         items = self.items
         kwargs = {}
         memo[id(items)] = kwargs
         for key, value in items():
             try:
                 newkey = deepcopy(key, memo)
             except TypeError:
                 newkey = copy(key)
             try:
                 newvalue = deepcopy(value, memo)
             except TypeError:
                 newvalue = copy(value)
             kwargs[newkey] = newvalue

         newObj.__init__(**kwargs)
         return newObj

####################################################################################################################
# Structs
####################################################################################################################
class kstruct(object):
    """
    Like C structs.
    c = kstruct(empty=0, halfway=1, full=2)
     or
    c= kstruct({'empty':0, 'half':1, 'full':2})

    c.empty = c['empty'] = c[0] -> <kstructElement "empty" -> 0 > 

    c['empty'].key = c[0].key     -> 'empty'
    c['empty'].value = c[0].value -> 0

    print c[0] -> 'empty'
    print int(c[0]) -> 0

    c.dict -> {'empty': 0, 'half': 1, 'full': 2}

    """


    def __init__(self, *args, **kwargs):

        if len(args)==1 and isinstance(args[0], dict):
            dictionary = args[0]
        else:
            dictionary = kwargs

        self.__dict__['_elements'] = dictionary

    def __setattr__(self, attr, value):
        raise AttributeError,"You cannot set attrs at runtime"

    def __getattr__(self, attr):
        if self.__dict__['_elements'].has_key(attr):
            return kstructElement(attr,self._elements[attr])
        else:
            raise AttributeError,"No item with key %r" % attr

    def __getitem__(self,item):
        if isinstance(item, str):
            return self.__getattr__(item)
        if isinstance(item, int):
            return self._fromValue(item)
        raise Exception, "Only str and int allowed"

    def __repr__(self):
        return r"<%s(%s)>" % (self.__class__.__name__, self._elements)

    @property
    def dict(self): return self.__dict__['_elements']

    def _fromValue(self,value):
        for attr in self._elements:
            if self._elements[attr] == value:
                return kstructElement(attr,self._elements[attr])
        raise Exception, "No item with value %d" % value

class kstructElement(object):
    """
    A single item of a kstruct.
    Only interesting method is 'abbrev' that gives back abbreviated string form
    """
    def __init__(self,key,value):
        self.__dict__['key'] = key
        self.__dict__['value'] = value

    def __setattr__(self, attr, value):
        raise AttributeError,"You cannot set attrs at runtime"

    def __str__(self): return self.key

    def __int__(self): return self.value

    def __repr__(self): return "<%s \"%s\" -> %d >" % (self.__class__.__name__,self.key,self.value)

    def abbrev(self, nchar=3):
       """
       Return abbreviated form of item key.
       If nchar=0, return full key.
       """

       if nchar==0:
           return str(self)
       else:
           return str(self)[0:nchar]

