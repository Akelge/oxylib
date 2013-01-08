from webhelpers.util import html_escape
from pylons import request
import urllib

def current_url(request=request):
    """
    \brief Temporary kludge until pylons.url.current() stabilizes and returns
    the query string.
    """

    if request.query_string:
        return "%s?%s" % (request.path_info, request.query_string)
    else:
        return request.path_info


def construct_url(environ, with_query_string=True, with_path_info=True, script_name=None, path_info=None, querystring=None):
    """Reconstructs the URL from the WSGI environment.
    You may override SCRIPT_NAME, PATH_INFO, and QUERYSTRING with
    the keyword arguments.
    """
    url = '://'
    host = environ.get('HTTP_X_FORWARDED_HOST', environ.get('HTTP_HOST'))
    port = None
    if ':' in host:
        host, port = host.split(':', 1)
    else:
        # See if the request is proxied
        host = environ.get('HTTP_X_FORWARDED_HOST', environ.get('HTTP_X_FORWARDED_FOR'))
        if host is not None:
            # Request was proxied, get the correct data
            host = environ.get('HTTP_X_FORWARDED_HOST')
            port = environ.get('HTTP_X_FORWARDED_PORT')
            if port is None and environ.get('HTTP_X_FORWARDED_SSL') == 'on':
                port = '443'
            if not port:
                log.warning(
                    'No HTTP_X_FORWARDED_PORT or HTTP_X_FORWARDED_SSL found '
                    'in environment, cannot '
                    'determine the correct port for the form action. '
                )
            if not host:
                log.warning(
                    'No HTTP_X_FORWARDED_HOST found in environment, cannot '
                    'determine the correct hostname for the form action. '
                    'Using the value of HTTP_HOST instead.'
                )
                host = environ.get('HTTP_HOST')
        else:
            # Request was not proxied
            if environ['wsgi.url_scheme'] == 'https':
                port = 443
            if host is None:
                host = environ.get('HTTP_HOST')
            if port is None:
                 port = environ.get('SERVER_PORT')
    url += host
    if port:
        if str(port) == '443':
            url = 'https'+url
        elif str(port) == '80':
            url = 'http'+url
        else:
            # Assume we are running HTTP on a non-standard port
            url = 'http'+url+':%s' % port
    else:
        url = 'http'+url
    if script_name is None:
        url += urllib.quote(environ.get('SCRIPT_NAME',''))
    else:
        url += urllib.quote(script_name)
    if with_path_info:
        if path_info is None:
            url += urllib.quote(environ.get('PATH_INFO',''))
        else:
            url += urllib.quote(path_info)
    if with_query_string:
        if querystring is None:
            if environ.get('QUERY_STRING'):
                url += '?' + environ['QUERY_STRING']
        elif querystring:
            url += '?' + querystring
    return url

def HTMLPrint(what, title="Unknown Object"):
    """
    \brief Print a dict (session,environ,etc) in a pretty HTML table
    """
    output=[]
    output.append("<table border='2' width=80%% align='center'><tr><td align='center' colspan='2'><b>%s</b></td></tr>" % title)
    if hasattr(what, 'items'):
        for k,v in sorted(what.items()):
            output.append("<tr><td><b>%s</b></td><td>%s</td></tr>" % (k, html_escape(repr(v))))
    else:
        output.append("<tr><td colspan='2'>%s</td></tr>" % html_escape(type(what)))
    output.append("</table><p></p>")
    return '\n'.join(output)

# Commodities to print useful parts
def printConfig(config): return HTMLPrint(config, "Config")
def printSession(session): return HTMLPrint(session, "Session")
def printCGIEnv(): return HTMLPrint(dict(([i for i in request.environ.items() if i[0].upper()==i[0]])), "CGI Environ")
def printWSGIEnv(): return HTMLPrint(dict(([i for i in request.environ.items() if i[0].lower()==i[0]])), "WSGI Environ")

