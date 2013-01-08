"""
Oxysoft standard library
@brief Locale parsing, setting and formatting

$Id$
"""
__headUrl__  = '$HeadURL$'

from babel import Locale, UnknownLocaleError
from babel.dates import DateTimePattern
import os, re
import warnings
#############################################################################################

def makeLocale(language_string=None):
    """
    @brief Returns a Locale (from argument or environ)
    @param language_string language to use (None for guessing)
    @return Locale object
    """

    lang,territory = 'en','US'

    if not language_string:
        # LANGUAGE FROM HTTP LANGUAGE (VIA PYLONS)
        try:
            from pylons import request
            language_string = request.languages[0]
        except: language_string = None

    if not language_string:
        # LANGUAGE FROM ENVIRON
        try:
            language_string = os.environ['LANG'].split('.')[0]
        except: language_string = None

    if not language_string or language_string == 'C':
        warnings.warn('Locale default to en_US')
    else:
        try:
            language_string = language_string.replace('-','_') #uniform
            lang = language_string.split('_')[0].lower() #get lang
            territory = language_string.split('_')[1].upper() #get territory
        except:
            lang = language_string.lower() #only lang
            territory = None

    try:
        locale = Locale(lang, territory) #try lang + territory
    except:
        try:
            locale = Locale(lang) #try only lang
        except:
            warnings.warn('Error: locale [\'%s\',\'%s\'] not valid; reset to en_US' % (lang,territory))
            locale = Locale('en','US') #reset to en_US

    # Fix patterns
    # always two digits for hours, minutes, seconds, days and months
    # always four digits for year
    for format in locale.time_formats:
        pat=locale.time_formats[format]
        pat.pattern=pat.pattern.replace('.', ':')
        pat.pattern=re.sub(r'\bm\b', 'mm', pat.pattern)
        pat.pattern=re.sub(r'\bh\b', 'hh', pat.pattern)
        pat.pattern=re.sub(r'\bH\b', 'HH', pat.pattern)

        pat.format=pat.format.replace('.', ':')
        pat.format=re.sub('\(m\)', '(mm)', pat.format)
        pat.format=re.sub('\(h\)', '(hh)', pat.format)
        pat.format=re.sub('\(H\)', '(HH)', pat.format)
        if format == 'full':
             pat.pattern=re.sub(r'\bv\b', 'z', pat.pattern)
             pat.format=re.sub('\(v\)', '(z)', pat.format)

    for format in locale.date_formats:
        pat=locale.date_formats[format]
        pat.pattern=re.sub(r'\bM\b', 'MM', pat.pattern)
        pat.pattern=re.sub(r'\bd\b', 'dd', pat.pattern)
        pat.pattern=re.sub(r'\byy\b', 'yyyy', pat.pattern)

        pat.format=re.sub('\(M\)', '(MM)', pat.format)
        pat.format=re.sub('\(d\)', '(dd)', pat.format)
        pat.format=re.sub('\(yy\)', '(yyyy)', pat.format)

    return locale
