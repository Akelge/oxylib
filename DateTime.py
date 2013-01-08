"""
Oxysoft standard library
DateTime classes
$Id$
"""

__headUrl__  = '$HeadURL$'

import datetime as pydt
import re
import pytz
import tztest
import copy
import babel.dates as babeldates
from mx import DateTime as mxdt
from oxylib.locale import makeLocale



#############################################################################
#############################################################################
#############################################################################


class TimeZone(object):
    """
    @brief Class for managing Time Zones. (Wrapper for pytz.timezone)
    @param zone Zone name (for reference see pytz.common_timezones)
    """

    def __init__(self,zone=None):
        """
        TimeZone("TimeZoneName") # e.g. "Europe/London", "US/Pacific"...
        """
        if not zone: zone = "UTC"
        self.__dict__["_timezone"] = pytz.timezone(zone)

    def __setattr__(self,arg,value):
        raise AttributeError, "TimeZone objects are read only"

    #############################################################################

    def __str__(self):
        return self.zone

    def __repr__(self):
        return r"<%s('%s')>" % (self.__class__.__name__, self)

    #############################################################################

    def __copy__(self): return copy.deepcopy(self)

    #############################################################################

    @classmethod
    def local(cls):
        return TimeZone(tztest.get_zone())

    @classmethod
    def zones(cls):
        """
        @brief Returns the possible zones
        @return array
        """
        return pytz.common_timezones

    @classmethod
    def country_zones(cls):
        """
        @brief Returns the possible zones by country
        @return dict
        """
        return pytz.country_timezones

    #############################################################################

    def dst(self,DateTimeObj):
        """
        @brief Returns the Daylight Saving Time Offset
        @param DateTimeObj a DateTime object
        @return TimeDelta object
        """
        return TimeDelta(seconds=self._timezone.dst(DateTimeObj.todatetime()).seconds)

    def tzname(self,DateTimeObj):
        """
        @brief Returns the Time Zone Name (e.g 'UTC', 'CET', 'CEST')...
        @param DateTimeObj a DateTime object
        @return string
        """
        return self._timezone.tzname(DateTimeObj.todatetime())

    def utcoffset(self,DateTimeObj):
        """
        @brief Returns the total offset from UTC (DST included)
        @param DateTimeObj a DateTime object
        @return TimeDelta object
        """
        offset = self._timezone.utcoffset(DateTimeObj.todatetime())
        if offset.days < 0: offset = offset.seconds*offset.days
        else: offset = offset.seconds
        return TimeDelta(seconds=offset)

    @property
    def zone(self):
        """
        @brief Returns the zone name
        @return string zone name
        """
        return self._timezone.zone

    #############################################################################

    def __eq__(self, other): # X == Y
        if isinstance(other,(DateTime,TimeZone)):
            return self.zone == other.zone
        return False
        # elif other is None or str(type(u))==str(util.symbol): return False
        # else:
            # raise TypeError, "supports only TimeZone objects"

    def __ne__(self, other): # X != Y
        return not(self.__eq__(other))

    #############################################################################



#############################################################################
#############################################################################
#############################################################################



class DateTime(object):
    """
    @brief Class for managing Dates and DateTimes. (Wrapper for mxDateTime)
           needs a DateTime and a TimeZone (default is UTC)
    @param *args,**kwargs Can handle parsing strings, numbers and keywords.
           Can specify "tz", a TimeZone() object (as LAST argument).
    """
    isostr = "%Y-%m-%dT%H:%M:%S"

    def __new__(cls,*args,**kwargs):
        # needed for composite
        if len(args)==2 and args[0] is None and args[1] is None: return None
        return object.__new__(cls)

    def __init__(self,*args,**kwargs):
        """
        DateTime(year,month,[day],[hour],[minute],[second],[TimeZone])
        DateTime("YYYY-MM-DDThh:mm:ss",[TimeZone])
        DateTime("YYYY-MM-DDThh:mm:ss zone")
        DateTime(ticks,[TimeZone])
        DateTime(mxDateTime,[TimeZone])
        DateTime(datetime,[TimeZone])
        """

        # print "ONEMORE - %s, %s" % (args, kwargs)

        # set default timezone
        timezone = TimeZone()

        # *******
        if args:
            # cast tuple to array
            args = [a for a in args]

            # get tz as string (two args, last is timezone as string)
            # COMPOSITE VALUES
            if len(args) == 2 and isinstance(args[0],DateTime) and isinstance(args[1],TimeZone):
                timezone = args[1]
                args = (args[0].toTZ(timezone)._mxObj,)
            # END COMPOSITE VALUES

            # *******

            # get TZ from last args
                #(...,TimeZone)
            if args and isinstance(args[-1],TimeZone): timezone = args.pop()

            # *******
            if len(args) == 1 and isinstance(args[0],(str,unicode)):
                # ("ISO") iso with timezone
                m = re.search('^(\d+-\d+-\d+(?:T\d+:\d+:\d+)?) (.+)$',args[0])
                if m:
                    g = m.groups()
                    args = (g[0],)
                    timezone = TimeZone(g[1])
            if len(args) == 1 and isinstance(args[0],(pydt.datetime,pydt.date)):
                # (datetime) from pydt.datetime
                args = (self._parsedatetime(args[0]),)
            if len(args) == 1 and isinstance(args[0],DateTime):
                # (DateTime) from DateTime
                args = (args[0].toTZ(timezone)._mxObj,)

        # *******
        # get TZ from kwargs
        if kwargs and kwargs.has_key("tz"):
            #(...,tz=TimeZone)
            if isinstance(kwargs["tz"],TimeZone): timezone = kwargs["tz"]
            del kwargs['tz']

        #if no input use NOW
        if not(args or kwargs):
            # Get current date and time, apply system timezone and then convert to given timezone (default UTC)
            args = (DateTime(mxdt.now().strftime(self.isostr),TimeZone(tztest.get_zone())).toTZ(timezone)._mxObj,)

        # *******

        #sets read-only properties
        self.__dict__["_mxObj"] = mxdt.DateTimeFrom(*args,**kwargs)
        self.__dict__["timezone"] = timezone
        self.__dict__["zone"] = self.timezone.zone
        self.__dict__["dst"] = self.timezone.dst(self)
        self.__dict__["tzname"] = self.timezone.tzname(self)
        self.__dict__["utcoffset"] = self.timezone.utcoffset(self)

    def __setattr__(self,arg,value):
        raise AttributeError, "DateTime objects are read only"

    # COMPOSITE VALUES
    def __composite_values__(self):
        return (self,self.timezone)
    # END COMPOSITE VALUES

    #############################################################################

    def __float__(self):
        return self.ticks

    def __int__(self):
        return int(self.__float__())

    def __str__(self):
        return r"%s %s" % (self.strftime("%Y-%m-%dT%H:%M:%S"),self.zone)
        # return self.formatISO()

    def __repr__(self):
        return r"<%s('%s')>" % (self.__class__.__name__, self)

    def info(self):
        return r"%s%s %s (%s)" % (self.strftime("%Y-%m-%dT%H:%M:%S"),self._utcoffsetstr,self.tzname,self.zone)

    #############################################################################

    # collide copy and deepcopy
    def __copy__(self): return copy.deepcopy(self)

    #############################################################################

    @classmethod
    def _parsedatetime(cls,datetimeObj):
        """
        @brief Classmethod to parse a pydt.datetime
        @param datetimeObj datetime object
        @return DateTime object
        """
        t = [datetimeObj.year,datetimeObj.month,datetimeObj.day]
        if isinstance(datetimeObj,pydt.datetime):
            t.extend((datetimeObj.hour,datetimeObj.minute,datetimeObj.second))
        return cls(*t)

    @classmethod
    def strptime(cls,string,pattern):
        """
        @brief Classmethod to parse a string following a strptime pattern
        @param string a datetime string
        @param pattern an strftime pattern
        @return DateTime object
        """
        t = pydt.datetime.strptime(string,pattern)
        return cls(t)


    #############################################################################

    # wrap mxDateTime properties and methods

    def tuple(self): return self._mxObj.tuple()

    @property
    def _utcoffsetstr(self):
        sign = "+"
        if (self.utcoffset.seconds < 0): sign="-"
        return "%s%02d:%02d" % (sign,self.utcoffset.hour,self.utcoffset.minute)

    @property
    def day(self): return self._mxObj.day
    @property
    def month(self): return self._mxObj.month
    @property
    def year(self): return self._mxObj.year
    @property
    def day_of_week(self): return self._mxObj.day_of_week
    @property
    def week_of_year(self): return self._mxObj.iso_week[1]
    @property
    def day_of_year(self): return self._mxObj.day_of_year
    @property
    def days_in_month(self): return self._mxObj.days_in_month
    @property
    def hour(self): return self._mxObj.hour
    @property
    def is_leapyear(self): return self._mxObj.is_leapyear
    @property
    def minute(self): return self._mxObj.minute
    @property
    def month(self): return self._mxObj.month
    @property
    def second(self): return self._mxObj.second
    @property
    def ticks(self): return self._mxObj.ticks()

    #############################################################################

    def todatetime(self,tzinfo=False):
        """
        @brief Converts to python datetime (without TimeZone)
        @return datetime object
        """
        t=self.tuple()[:6]
        t=[e for e in t]
        if tzinfo: t.extend((0,pytz.timezone(self.zone)))
        return pydt.datetime(*t)

    def tomxDateTime(self):
        """
        @brief Converts to mxDateTime (without TimeZone)
        @return mxDateTime object
        """
        return self._mxObj

    #############################################################################

    def toTZ(self,tz):
        """
        @brief Change TimeZone
        @param tz new TimeZone
        @return DateTime object
        """
        if self.timezone == tz: return self
        offset = tz.utcoffset(self)-self.utcoffset
        #return DateTime((self + offset).strftime(self.isostr),tz) #heavier way
        return DateTime((self._mxObj + offset._mxObj).strftime(self.isostr),tz) #lighter way

    def toUTC(self):
        """
        @brief Change TimeZone to UTC
        @return DateTime object
 e      """
        return self.toTZ(TimeZone())

    def toLocal(self):
        """
        @brief Change TimeZone to Local System Timezone
        @return DateTime object
        """
        return self.toTZ(TimeZone.local())

    #############################################################################

    def getTime(self):
        """
        @brief Gets current Time (ignore TZ)
        @return TimeDelta object
        """
        return TimeDelta(self.strftime("%H:%M:%S"))

    def getDate(self,tz=None):
        """
        @brief Gets current Date (ignore TZ)
        @param tz optional tz (default UTC)
        @return DateTime object
        """
        return DateTime(self.strftime("%Y-%m-%d"),tz or TimeZone())

    #############################################################################

    def yearBoundary(self):
        """
        @brief Return start and end of the year
        @return a tuple containing start and end of year as DateTime objects
        """
        start = DateTime(year=self.year, day=1, month=1,tz=self.timezone)
        end = start+oneYear-oneSecond
        return (start, end)

    def monthBoundary(self):
        """
        @brief Return start and end of the month
        @return a tuple containing start and end of month as DateTime objects
        """
        start = DateTime(year=self.year, month=self.month, day=1, tz=self.timezone)
        end = start+oneMonth-oneSecond
        return (start, end)

    def weekBoundary(self):
        """
        @brief Return start and end of the week
        @return a tuple containing start and end of week as DateTime objects
        """
        start = self.getDate(tz=self.timezone)+RelativeDateTime(weekday=(0,0))
        end = start+oneWeek-oneSecond
        return (start, end)

    #############################################################################

    def strftime(self,format):
        """
        @brief Format with strftime
        @param format the strftime format
        @return string
        """
        return self._mxObj.strftime(format)

    def formatISO(self, offset=True, part="full"):
        """
        @brief Format as ISO (YYYY-MM-DDThh:mm:ss+hh:mm) (without TimeZone, only offset)
        @param offset Print tz offset
        @param part "full", "date", "time"
        @return string
        """
        t_date = "%Y-%m-%d"
        t_time = "%H:%M:%S"
        if part == "full":
            pattern = "%sT%s" % (t_date,t_time)
        elif part == "date":
            pattern = t_date
        elif part == "time":
            pattern = t_time
        else:
            raise Exception("Unknown part type '%s', use one of 'full', 'date', 'time'" % part)

        if not offset or part == "date":
            return "%s" % (self.strftime(pattern))
        else:
            return "%s%s" % (self.strftime(pattern),self._utcoffsetstr)

    def _formatDateTimeObj(self, locale, format, part):
        """
        @brief Hidden function.
        @param locale babel.Locale object
        @param format can be 'short', 'medium' (default), 'long', 'full' and 'notYear'
        """

        if not locale: locale = makeLocale()

        if format == 'notYear':
            if part == 'date':
                pattern=locale.date_formats['short'].pattern
                pattern=pattern.replace('/yyyy', '')
                pattern=pattern.replace('yyyy/', '')
                pattern=pattern.replace('/yy', '')
                pattern=pattern.replace('yy/', '')
                format=pattern
            if part == 'time':
                format='short'

        # pattern=locale.date_formats[format].pattern
        # pattern = format

        return eval("babeldates.format_%s" % part)(self.todatetime(tzinfo=True), format=format, locale=locale)

    def formatDate(self, locale=None, format='short'):
        """
        @brief Return a string, formatted Date according to locale
        @param locale babel.Locale object
        @param format can be 'short', 'medium' (default), 'long', 'full' and 'notYear'
        """
        return self._formatDateTimeObj(locale=locale, part='date', format=format)

    def formatTime(self, locale=None, format='short'):
        """
        @brief Return a string, formatted Time according to locale
        @param locale babel.Locale object
        @param format can be 'short', 'medium' (default), 'long', 'full'
        """
        return self._formatDateTimeObj(locale=locale, part='time', format=format)

    def formatDateTime(self, locale=None, format='short'):
        """
        @brief Return a string, formatted Date+Time according to locale
        @param locale babel.Locale object
        @param format can be 'short', 'medium' (default), 'long', 'full' and 'notYear'
        """
        return self._formatDateTimeObj(locale=locale, part='datetime', format=format)


    #############################################################################

    def __eq__(self, other): # X == Y
        if isinstance(other,DateTime):
            lo = self.toUTC()
            ro = other.toUTC()
            return lo._mxObj == ro._mxObj
        elif isinstance(other,TimeZone):
            return self.zone == other.zone
        return False
        # elif other is None or str(type(u))==str(util.symbol): return False
        # else:
            # raise TypeError, "supports only DateTime objects"

    def __ne__(self, other): # X != Y
        return not(self.__eq__(other))

    def __lt__(self, other): # X < Y
        if other is None: return False
        if isinstance(other,DateTime):
            lo = self.toUTC()
            ro = other.toUTC()
            return lo._mxObj < ro._mxObj
        else:
            raise TypeError, "supports only DateTime objects"

    def __le__(self, other): # X <= Y
        if other is None: return False
        if isinstance(other,DateTime):
            lo = self.toUTC()
            ro = other.toUTC()
            return lo._mxObj <= ro._mxObj
        else:
            raise TypeError, "supports only DateTime objects"

    def __gt__(self, other): # X > Y  
        if other is None: return False
        if isinstance(other,DateTime):
            lo = self.toUTC()
            ro = other.toUTC()
            return lo._mxObj > ro._mxObj
        else:
            raise TypeError, "supports only DateTime objects"

    def __ge__(self, other): # X >= Y
        if other is None: return False
        if isinstance(other,DateTime):
            lo = self.toUTC()
            ro = other.toUTC()
            return lo._mxObj >= ro._mxObj
        else:
            raise TypeError, "supports only DateTime objects"

    #############################################################################

    def __add__(self,other):
        if isinstance(other,TimeDelta): return DateTime((self._mxObj+other._mxObj).strftime(self.isostr),self.timezone)
        elif isinstance(other,RelativeDateTime): return other.__radd__(self)
        else: raise TypeError, "supports only TimeDelta and RelativeDateTime objects"

    def __sub__(self,other):
        if isinstance(other,TimeDelta):
            return DateTime((self._mxObj-other._mxObj).strftime(self.isostr),self.timezone)
        elif isinstance(other,DateTime):
            lo = self.toUTC()
            ro = other.toUTC()
            return TimeDelta(seconds=(lo._mxObj-ro._mxObj).seconds)
        elif isinstance(other,RelativeDateTime):
            return other.__rsub__(self)
        else:
            raise TypeError, "supports only DateTime, TimeDelta and RelativeDateTime objects"

    # SQLPlus
    def toDict(self): return self.formatISO(offset=False)

    #############################################################################

class Date(DateTime):

    def formatISO(self, offset=True, part="date"):
        return DateTime.formatISO(self, offset, part)
    def __str__(self):
        return self.formatISO(part='date')


#############################################################################
#############################################################################
#############################################################################



class TimeDelta(object):
    """
    @brief Class for managing Times and TimeDelta. (Wrapper for mxDateTimeDelta)
    @param *args,**kwargs Can handle parsing strings, numbers and keywords.
            If args=None and kwargs=None defaults to now()
    """
    def __init__(self,*args,**kwargs):
        """
        TimeDelta(seconds)
        TimeDelta([days],[hours],[minutes],[seconds])
        TimeDelta("+DDd:hh:mm:ss")
        TimeDelta() -> now
        """
        if len(args) == 1 and isinstance(args[0],(pydt.time)):
            args = (args[0].isoformat(),)
        if len(args) == 1 and isinstance(args[0],TimeDelta):
            #from TimeDelta
            args = (args[0]._mxObj,)
        if len(args) == 0 and len(kwargs) == 0:
            args=(mxdt.now().time,) # Default to now

        self.__dict__["_mxObj"] = mxdt.DateTimeDeltaFrom(*args,**kwargs)

    def __setattr__(self,arg,value):
        raise AttributeError, "TimeDelta objects are read only"

    #############################################################################

    def __str__(self):
        sign = ''
        if self.seconds < 0: sign = '-'
        output = "%s" % sign
        if self.day: output += "%02dd" % self.day
        if self.day or self.hour: output += "%02d:" % self.hour
        if self.day or self.hour or self.minute: output += "%02d:" % self.minute
        return "%s%02d" % (output,self.second)

    def __repr__(self):
        return r"<%s('%s')>" % (self.__class__.__name__, self)

    def __float__(self):
        return self.seconds

    def __int__(self):
        return int(self.__float__())

    #############################################################################

    def __copy__(self): return copy.deepcopy(self)

    #############################################################################
    @classmethod
    def _parsetime(self,timeObj):
        """
        @brief Classmethod to parse a pydt.datetime
        @param datetimeObj datetime object
        @return DateTime object
        """
        t = "%02d:%02d:%02d" % (timeObj.hour,timeObj.minute,timeObj.second)
        return Time(t)

    #############################################################################

    def tuple(self): return self._mxObj.tuple()

    @property
    def second(self): return abs(self._mxObj.second)
    @property
    def minute(self): return abs(self._mxObj.minute)
    @property
    def hour(self): return abs(self._mxObj.hour)
    @property
    def day(self): return abs(self._mxObj.day)
    @property
    def seconds(self): return self._mxObj.seconds
    @property
    def minutes(self): return self._mxObj.minutes
    @property
    def hours(self): return self._mxObj.hours
    @property
    def days(self): return self._mxObj.days

    #############################################################################

    def totime(self):
        return pydt.time(*self.tuple()[1:])

    #############################################################################

    def strftime(self,format):
        """
        @brief Formats with strftime
        @param format the strftime format
        @return string
        """
        return self._mxObj.strftime(format)

    def formatISO(self, offset=False):
        """
        @brief Format as ISO (hh:mm:ss)
        @return string
        """
        return "%s" % (self.strftime("%H:%M:%S"))

    def _formatTimeObj(self, locale, format):
        """
        @brief Hidden function.
        @param locale babel.Locale object
        @param format can be 'short', 'medium', 'long', 'full'
        """
        if not locale: locale = makeLocale()
        part = "time"
        return eval("babeldates.format_%s" % part)(self.totime(), format=format, locale=locale)

    def formatTime(self, locale=None, format='medium'):
        """
        @brief Return a string, formatted Time according to locale
        @param locale babel.Locale object
        @param format can be 'short', *'medium'
        """
        if format=='long' or format=='full': format = 'medium' #ignore TZ
        return self._formatTimeObj(locale=locale, format=format)

    #############################################################################

    def __eq__(self, other): # X == Y
        if isinstance(other,TimeDelta): return self._mxObj == other._mxObj
        return False
        # elif other is None or str(type(u))==str(util.symbol): return False
        # else:
            # raise TypeError, "supports only TimeDelta objects"

    def __ne__(self, other): # X != Y
        return not(self.__eq__(other))

    def __neg__(self): # -X
        selfcopy = copy.deepcopy(self)
        selfcopy.__dict__['_mxObj'] = -selfcopy._mxObj
        return selfcopy

    def __lt__(self, other): # X < Y
        if other is None: return False
        if isinstance(other,TimeDelta): return self._mxObj < other._mxObj
        else: raise TypeError, "supports only TimeDelta objects"

    def __le__(self, other): # X <= Y
        if other is None: return False
        if isinstance(other,TimeDelta): return self._mxObj <= other._mxObj
        else: raise TypeError, "supports only TimeDelta objects"

    def __gt__(self, other): # X > Y  
        if other is None: return False
        if isinstance(other,TimeDelta): return self._mxObj >= other._mxObj
        else: raise TypeError, "supports only TimeDelta objects"

    def __ge__(self, other): # X >= Y
        if other is None: return False
        if isinstance(other,TimeDelta): return self._mxObj >= other._mxObj
        else: raise TypeError, "supports only TimeDelta objects"

    #############################################################################

    def __add__(self,other):
        if isinstance(other,TimeDelta): return TimeDelta(self._mxObj+other._mxObj)
        else: raise TypeError, "supports only TimeDelta objects"

    def __sub__(self,other):
        if isinstance(other,TimeDelta): return TimeDelta(self._mxObj-other._mxObj)
        else: raise TypeError, "supports only TimeDelta objects"

    def __mul__(self,other):
        if isinstance(other,(int,float)): return TimeDelta(self._mxObj*float(other))
        else: raise TypeError, "supports only numbers"
    __rmul__ = __mul__

    def __div__(self,other):
        if isinstance(other,(int,float)): return self.__mul__(1/float(other))
        else: raise TypeError, "supports only numbers"
    __rdiv__ = __div__

    #############################################################################

    # SQLPlus
    def toDict(self): return self.formatISO(offset=False)


#############################################################################
#############################################################################
#############################################################################

class RelativeDateTime(object):
    """
    @brief Class for managing Times and TimeDelta. (Wrapper for mxDateTimeDelta)
    @param *args,**kwargs Can handle parsing strings, numbers and keywords.
    """
    def __init__(self,*args,**kwargs):
        """ RelativeDateTime([years],[months],[days],[hours],[minutes],[seconds],
                             [year],[month],[day],[hour],[minute],[second],[weekday])
            RelativeDateTime("YYYY-MM-DD HH:MM:SS") # absolutes
            RelativeDateTime("(+YYYY)-(+MM)-(+DD) (+HH):(+MM):(+SS)") # relatives
        """
        self.__dict__["_mxObj"] = mxdt.RelativeDateTimeFrom(*args,**kwargs)

    def __setattr__(self,arg,value):
        raise AttributeError, "RelativeDateTime objects are read only"

    #############################################################################

    def __str__(self):
        return "%s" % self._mxObj.__str__()

    def __repr__(self):
        return r"<%s('%s')>" % (self.__class__.__name__, self)

    #############################################################################

    def __copy__(self): return self.__deepcopy__(None)
    def __deepcopy__(self,memo):
        o = self._mxObj
        return RelativeDateTime(years=o.years,
                                months=o.months,
                                days=o.days,
                                year=o.year,
                                month=o.month,
                                day=o.day,
                                hours=o.hours,
                                minutes=o.minutes,
                                seconds=o.seconds,
                                hour=o.hour,
                                minute=o.minute,
                                second=o.second,
                                weekday=o.weekday)

    #############################################################################

    def tuple(self): return self._mxObj.tuple()

    @property
    def second(self): return self._mxObj.second
    @property
    def minute(self): return self._mxObj.minute
    @property
    def hour(self): return self._mxObj.hour
    @property
    def day(self): return self._mxObj.day
    @property
    def month(self): return self._mxObj.month
    @property
    def year(self): return self._mxObj.year
    @property
    def seconds(self): return self._mxObj.seconds
    @property
    def minutes(self): return self._mxObj.minutes
    @property
    def hours(self): return self._mxObj.hours
    @property
    def days(self): return self._mxObj.days
    @property
    def months(self): return self._mxObj.months
    @property
    def years(self): return self._mxObj.years
    @property
    def weekday(self): return self._mxObj.weekday

    #############################################################################

    def __eq__(self, other): # X == Y
        if isinstance(other,RelativeDateTime): return self._mxObj == other._mxObj
        else: raise TypeError, "supports only RelativeDateTime objects"

    def __ne__(self, other): # X != Y
        return not(self.__eq__(other))

    def __neg__(self): # - X
        selfcopy = copy.deepcopy(self)
        selfcopy.__dict__['_mxObj'] = -selfcopy._mxObj
        return selfcopy

    #############################################################################

    def __add__(self,other):
        if isinstance(other,RelativeDateTime): return RelativeDateTime(self._mxObj+other._mxObj)
        else: raise TypeError, "supports only RelativeDateTime objects"

    def __radd__(self,other):
        if isinstance(other,DateTime): return DateTime(other._mxObj+self._mxObj,other.timezone)
        else: raise TypeError, "supports only DateTime objects"

    def __sub__(self,other):
        if isinstance(other,RelativeDateTime): return RelativeDateTime(self._mxObj-other._mxObj)
        else: raise TypeError, "supports only RelativeDateTime objects"

    def __rsub__(self,other):
        if isinstance(other,DateTime): return DateTime(other._mxObj-self._mxObj,other.timezone)
        else: raise TypeError, "supports only DateTime objects"

    def __mul__(self,other):
        if isinstance(other,(int,float)):
            #rewritten beacuse in original mx, X+X != X*2
            factor = float(other)
            selfcopy = copy.deepcopy(self)
            # date deltas
            r = selfcopy._mxObj
            r.years = factor * r.years
            r.months = factor * r.months
            r.days = factor * r.days
            # time deltas
            r.hours = factor * r.hours
            r.minutes = factor * r.minutes
            r.seconds = factor * r.seconds
            return selfcopy
        else: raise TypeError, "supports only numbers"

    __rmul__ = __mul__

    def __div__(self,other):
        if isinstance(other,(int,float)): return self.__mul__(1/float(other))
        else: raise TypeError, "supports only numbers"

    __rdiv__ = __div__

    #############################################################################

# -- Shortcuts

RelativeDate = RelativeDateTime
Time = TimeDelta
# Date = DateTime

oneYear   = RelativeDateTime(years=1)
oneMonth  = RelativeDateTime(months=1)
oneWeek   = RelativeDateTime(weeks=1)
oneDay    = RelativeDateTime(days=1)
oneHour   = RelativeDateTime(hours=1)
oneMinute = RelativeDateTime(minute=1)
oneSecond = RelativeDateTime(seconds=1)
# s_month = Decimal("30.417") # IN GV2

#############################################################################
#############################################################################
#############################################################################

# -- Patterns 

def getPattern(locale=None, part='date', format='short', returns='strftime'):
    if not locale: locale = makeLocale()
    babelPattern=eval('locale.%s_formats["%s"].pattern' % (part, format))
    return convertDateFormat(babelPattern,inputFormat='babel',outputFormat=returns)

def strftimePatternDate(locale=None, format='short'):
    return getPattern(locale=locale, part='date', format=format, returns='strftime')

def strftimePatternTime(locale=None, format='short'):
    return getPattern(locale=locale, part='time', format=format, returns='strftime')

def strftimePatternDateTime(locale=None, format='short'):
    return "%s %s" % (strftimePatternDate(locale=locale, format=format), strftimePatternTime(locale=locale, format=format))

def humanPatternDate(locale=None, format='short'):
    return getPattern(locale=locale, part='date', format=format, returns='human')

def humanPatternTime(locale=None, format='short'):
    return getPattern(locale=locale, part='time', format=format, returns='human')

def humanPatternDateTime(locale=None, format='short'):
    return "%s %s" % (humanPatternDate(locale=locale, format=format), humanPatternTime(locale=locale, format=format))

def convertDateFormat(inputPattern, outputFormat='strftime',inputFormat='babel'):
    subst={ 'babel-strftime': [('d{1,2}', '%d'),
                               ('m{1,2}', '%M'),
                               ('(?<!%)M{1,2}', '%m'),
                               ('y{3,}', '%Y'),
                               ('y{1,2}', '%y'),
                               ('h{1,2}', '%I'),
                               ('H{1,2}', '%H'),
                               ('a', '%p'),
                               ('s{1,2}', '%S')],
               'babel-human': [('d{1,2}', 'dd'),
                               ('[mM]{1,2}', 'mm'),
                               ('y{3,}', 'yyyy'),
                               ('y{1,2}(?!y)', 'yy'),
                               ('h{1,2}', 'h12'),
                               ('H{1,2}', 'h24'),
                               ('a', 'AM/PM'),
                               ('s{1,2}', 'ss')],
            'strftime-babel': [('%d','dd'),
                               ('%M','mm'),
                               ('%m','MM'),
                               ('%Y','yyyy'),
                               ('%y','yy'),
                               ('%I','hh'),
                               ('%H','HH'),
                               ('%p','a'),
                               ('%S','ss')],
            'strftime-human': [('%d','dd'),
                               ('%M','mm'),
                               ('%m','mm'),
                               ('%Y','yyyy'),
                               ('%y','yy'),
                               ('%I','h12'),
                               ('%H','h24'),
                               ('%p','AM/PM'),
                               ('%S','ss')]
          }

    outputPattern=inputPattern
    if not subst.has_key("%s-%s" % (inputFormat,outputFormat)): return None
    for pat in subst["%s-%s" % (inputFormat,outputFormat)]:
        outputPattern=re.sub(pat[0], pat[1], outputPattern)

    return outputPattern

#############################################################################
#############################################################################
#############################################################################

# -- LISTING FUNCTIONS

__formatMapping={ 'short': 'abbreviated',
                  'long': 'wide',
                  'single': 'narrow' }

def monthsList(locale=None, format='short'):
    """
    @brief Return an ordered array of tuples, each tuple is (# of month, name of month)
    Format can be: short, long or single
    """
    if not locale: locale = makeLocale()
    localeMonths=locale.months['format'][__formatMapping[format]]
    return [(k, localeMonths[k].capitalize()) for k in sorted(localeMonths.keys())]

def daysList(locale=None, format='short'):
    """
    @brief Return an ordered array of tuples, each tuple is (# of day, name of day)
    Format can be: short, long or single
    """
    if not locale: locale = makeLocale()
    localeDays=locale.days['format'][__formatMapping[format]]
    return [(k, localeDays[k].capitalize()) for k in sorted(localeDays.keys())]


#############################################################################
#############################################################################
#############################################################################

# PICKLING

### Make the types pickleable:
# Shortcuts for pickle (reduces the pickle's length)
def _PDT(mark):
    return DateTime(mark)
def _PTD(mark):
    return TimeDelta(mark)
def _PRDT(mark):
    return RelativeDateTime(mark)
def _PTZ(mark):
    return TimeZone(mark)

# Module init
class modinit:

    import copy_reg
    def pickle_DateTime(d):
        return _PDT,(str(d),)
    copy_reg.pickle(DateTime,
                    pickle_DateTime,
                    _PDT)

    def pickle_TimeDelta(d):
        return _PTD,(str(d),)
    copy_reg.pickle(TimeDelta,
                    pickle_TimeDelta,
                    _PTD)

    def pickle_RelativeDateTime(d):
        return _PRDT,(str(d),)
    copy_reg.pickle(RelativeDateTime,
                    pickle_RelativeDateTime,
                    _PRDT)

    def pickle_TimeZone(d):
        return _PTZ,(str(d),)
    copy_reg.pickle(TimeZone,
                    pickle_TimeZone,
                    _PTZ)

del modinit
