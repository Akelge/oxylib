#############################################################################
"""
Oxysoft standard library
Helpers classes
$Id$
"""

import DateTime

__headUrl__ = '$HeadURL$'

#############################################################################
#############################################################################
#############################################################################


def HTMLOption(description, value, selected):
    output = "<option value=\"%s\"" % (value)
    if int(value) == int(selected):
        output += " selected=\"selected\""
    output += ">%s</option>" % (description)
    return output

#############################################################################


def urlquery_for(*args, **kargs):
    querystring = kargs.get('querystring')
    qs = ''
    if querystring:
        for k, v in querystring.items():
            qs += '&%s=%s' % (k, v)
            if qs:
                qs = '?%s' % qs[1:]
        del kargs['querystring']
    return "%s%s" % (urlquery_for(*args, **kargs), qs)

#############################################################################


def scaleColors(cs, ce, s):
    _cs = [_cint(cs[0:2]), _cint(cs[2:4]), _cint(cs[4:6])]
    _ce = [_cint(ce[0:2]), _cint(ce[2:4]), _cint(ce[4:6])]

    e = [_chex(_scaleColor(_cs[0], _ce[0], s)),
         _chex(_scaleColor(_cs[1], _ce[1], s)),
         _chex(_scaleColor(_cs[2], _ce[2], s))]

    return ''.join(e)


def _scaleColor(cs, ce, s):  # int
    if cs > ce:
        l = ce
        u = cs
        return int(u - ((u - l) * s))
    else:
        l = cs
        u = ce
        return int(((u - l) * s) + l)


def _chex(c):
    return "%02X" % c
    # return ("0"+hex(c)[2:4])[-2:]


def _cint(c):
    return int(c, 16)

#############################################################################


def fDate(dt):
    if dt:
        return DateTime.DateTime(dt).formatDate()
    return ""


def fDateTime(dt):
    if dt:
        return DateTime.DateTime(dt).formatDateTime()

#############################################################################


def IIF(expression, iftrue, iffalse):
    if expression:
        return iftrue
    else:
        return iffalse

#############################################################################


def htmlBreadcrumb(args):
    output = '<div id="breadcrumb">'
    for el in args:
        k, v = el
        if v:
            output += ' &raquo; <a href="%s">%s</a>' % (v, k.upper())
        else:
            output += ' &raquo; %s' % k.upper()
    output += '</div>'
    return output
