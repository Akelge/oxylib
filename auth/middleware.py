"""
 Copyright CUBE Gestioni S.r.l. 2010

 AAA Module
 Inspired by RADIUS, users AV Pairs, i.e. a dictionary.
 Middleware

 $Id$

"""

import logging
from oxylib.auth import ckey, AuthenticatedUser
from oxylib.pylons.utils import construct_url
from pylons.util import call_wsgi_application
from pylons.templating import render_mako as render
from pylons import tmpl_context as c
import webob

log = logging.getLogger(__name__)
"""
Configuration stanza for middleware
; URL that triggers login - Defaults to /authlogin
oxylib.auth.m.loginTrap = /authlogin
; URL that triggers logout - Defaults to /authlogout
oxylib.auth.m.logoutTrap = /authlogout
; Optional - Defaults to internal form
oxylib.auth.m.loginForm = login.mako
; Defaults to referer
oxylib.auth.m.afterLoginGoto = welcome.mako
; Defaults to /
oxylib.auth.m.afterLogoutGoto = bye.mako
; Optional - page for unauthorized access, defaults to a simple 403 message
oxylib.auth.m.unauthorizePage = unauth.mako
"""


class OxylibAuthMiddleware(object):

    defaultLoginHtml = """
<html>
    <head>
        <title>Authentication</title>
    </head>
    <body>
      <div style="width:400px; margin:100px auto 20px; padding:0; font-family:Tahoma,'sans-serif';
                  border-radius:9px; border:2px solid #1B4E9D; background-color:#EEE;">
        <div style="font-size:1.5em; color:#FFF; background-color:#1B4E9D; border-radius:7px 7px 0 0; padding:10px;">Authentication</div>
       <div style="padding:10px;">
        <form action="%s" method="post">
            <div><label for="username">Username:</label><br/>
            <input type="text" name="username" id="username" style="width:100%%; font-size:1.3em;" />
            <label for="password">Password:</label></div>
            <input type="password" name="password" id="password" style="width:100%%; font-size:1.3em;" />
          <div style="text-align:right;"><input type="submit" name="authform" value="Login" style="border:1px outer #000;background-color:#EEE;font-size:1.2em;" /></div>
          <hr/>
          %s
        </form>
        </div>
       </div>
    </body>
</html>
"""
    defaultNoauthHtml = """
<html>
    <head>
        <title>Not Authorized</title>
    </head>
    <body>
      <div style="width:400px; margin:100px auto 20px; padding:0; font-family:Tahoma,'sans-serif';
                  border-radius:9px; border:2px solid #1B4E9D; background-color:#EEE;">
        <div style="font-size:1.5em; color:#FFF; background-color:#1B4E9D; border-radius:7px 7px 0 0; padding:10px;">Not Authorized</div>
        <div style="padding:10px;">
           You are not authorized to display the requested page
           <hr/>
           <div style="text-align:right;">
              <a href="javascript:window.history.back();">back</a> -
              <a href="%s">home</a> -
              <a href="%s">logout</a>
           </div>
        </div>
       </div>
    </body>
</html>"""

    def __init__(self, app, config):
        log.debug("Oxylib Auth Middleware init")
        self.app = app
        self.config = config

        # Default config
        self.loginTrap = '/authlogin'
        self.logoutTrap = '/authlogout'
        self.afterLoginGoto = None
        self.afterLogoutGoto = '/'
        self.loginForm = None
        self.unauthorizePage = None

        self.setup(self.config)
        log.debug('Setup finished')

    def setup(self, config):
        pairs = [(k.split('.')[-1], config[k]) for k in config.keys() if k.startswith(
            'oxylib.auth.m')]
        for p in pairs:
            setattr(self, p[0], p[1])
            if p[0] == 'loginController':
                self.extLogin = True

    def _makeurl(self, root, path):
        # combine root with path_info and query_string
        if (path[0] == '/'):
            path = path[1:]
        return "%s%s" % (root, path)

    def __call__(self, environ, start_response):
        session = environ['beaker.session']

        if ckey('user') in session:
            user = session.get(ckey('user'))
            environ['REMOTE_USER'] = user.username
            # environ[ckey('user')] = user

        environ[ckey('active')] = True

        status, headers, app_iter, exc_info = call_wsgi_application(
            self.app, environ, catch_exc_info=True)

        session[ckey('active')] = True
        session.save()

        root = construct_url(environ, path_info='/', with_query_string=False)
        url = construct_url(environ, with_query_string=False)

        # Record in env that we exist
        log.debug('request path    %s' % environ['PATH_INFO'])
        log.debug('request status  %s' % status)
        log.debug('request headers %s' % headers)

       #  # No PATH_INFO
        if environ['PATH_INFO'] == '':
            # Hack for static files
            log.debug('no PATH_INFO, returning app_iter')
            start_response(status, headers)
            return app_iter
        log.debug('response status %s' % status)

        # Login Submit
        if self.loginTrap == url[-len(self.loginTrap):]:
            log.debug('Triggered login')
            formvars = webob.Request(environ).POST
            form_username = formvars.get('username')
            form_password = formvars.get('password')

            if form_username and form_password:
                user = AuthenticatedUser(form_username, form_password, session)
                # After calling AuthenticatedUser __init__ we have a real session
                # so we could use session._sess
                if user.isAuthenticated():
                    log.info('%s authentication ok', form_username)
                    session._sess[ckey('user')] = user
                    log.debug('perms %s', user.perms)
                else:
                    log.info('%s authentication failed', form_username)
                    session._sess[ckey('_errors')] = user.errors
            else:
                session._sess[ckey('_errors')] = [('auth', 'generic', 'Missing credentials')]

            # go to AFTERLOGIN, STORED ENTRYPAGE or /
            goto = self.afterLoginGoto or session._sess.get(ckey('_entry')) or root

            if ckey('_entry') in session._sess:
                del session._sess[ckey('_entry')]
            session.save()

            log.debug('Going to %s' % goto)
            start_response('307 Temporary Redirect', [('Location', goto)])
            return ['Login OK']

        # Logout Submit
        if self.logoutTrap == url[-len(self.logoutTrap):]:
            log.debug('Triggered logout')
            log.info('%s logout' % session._sess[ckey('user')].username)
            if ckey('user') in session._sess:
                del session._sess[ckey('user')]
                session._sess.save()
            if 'REMOTE_USER' in environ:
                del environ['REMOTE_USER']
            goto = self.afterLogoutGoto or '/'
            log.debug('logout, going to %s' % goto)
            start_response('307 Temporary Redirect', [('Location', self._makeurl(root, goto))])
            return ['Logout OK']

        # 403 - Unauthorized (Block)
        if status[:3] == '403':
            log.debug('Triggered 403 (unauthorized)')
            start_response('200 OK', [('Content-Type', 'text/html; charset=UTF-8')])
            if self.unauthorizePage:
                c.rooturl = self._makeurl(root, '/')
                c.logouturl = self._makeurl(root, self.logoutTrap)
                return render(self.unauthorizePage)
            else:
                return [self.defaultNoauthHtml % (self._makeurl(root, '/'), self._makeurl(root, self.logoutTrap))]

        # 401 - Unauthenticated (Login)
        if status[:3] == '401':
            log.debug('Triggered 401 (unauthenticated)')
            start_response('200 OK', [('Content-Type', 'text/html; charset=UTF-8')])

            # Save in session where we are from
            session._sess[ckey('_entry')] = construct_url(environ)

            errors = session._sess.get(ckey('_errors'), [])
            if ckey('_errors') in session._sess:
                del session._sess[ckey('_errors')]
            session._sess.save()

            return [self.loginFormRender(errors)]

        if hasattr(app_iter, 'close'):
            app_iter.close()
        start_response(status, headers)
        return app_iter

###########
    def loginFormRender(self, errors=[]):
        errorsOut = []
        for e in errors:
            errorsOut.append("<b>%s (%s)</b> %s" % (e[1], e[0], e[2]))
        errors = '<br />\n'.join(errorsOut)

        if self.loginForm:
            c.action = self.loginTrap
            c.errors = errors
            t = render(self.loginForm)
        else:
            t = self.defaultLoginHtml % (self.loginTrap, '<br />\n'.join(errorsOut))

        return str(t)
