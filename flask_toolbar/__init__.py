import os
import warnings

from flask import Blueprint, current_app, request, g, send_from_directory
from flask.globals import _request_ctx_stack
from jinja2 import Environment, PackageLoader
from werkzeug.urls import url_quote_plus

from flask_toolbar.compat import iteritems
from flask_toolbar.toolbar import Toolbar
from flask_toolbar.utils import decode_text


module = Blueprint('toolbar', __name__)


def replace_insensitive(string, target, replacement):
    """Similar to string.replace() but is case insensitive
    Code borrowed from:
    http://forums.devshed.com/python-programming-11/case-insensitive-string-replace-490921.html
    """
    no_case = string.lower()
    index = no_case.rfind(target.lower())
    if index >= 0:
        return string[:index] + replacement + string[index + len(target):]
    else:  # no results so return the original string
        return string


def _printable(value):
    try:
        return decode_text(repr(value))
    except Exception as e:
        return '<repr(%s) raised %s: %s>' % (
               object.__repr__(value), type(e).__name__, e)


class ToolbarExtension(object):
    _static_dir = os.path.realpath(
        os.path.join(os.path.dirname(__file__), 'static'))

    _redirect_codes = [301, 302, 303, 304]

    def __init__(self, app=None):
        self.app = app
        self.toolbars = {}

        # Configure jinja for the internal templates and add url rules
        # for static data
        self.jinja_env = Environment(
            autoescape=True,
            extensions=['jinja2.ext.i18n', 'jinja2.ext.with_'],
            loader=PackageLoader(__name__, 'templates'))
        self.jinja_env.filters['urlencode'] = url_quote_plus
        self.jinja_env.filters['printable'] = _printable

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        for k, v in iteritems(self._default_config(app)):
            app.config.setdefault(k, v)

        if not app.config['TB_ENABLED']:
            return

        if not app.config.get('SECRET_KEY'):
            raise RuntimeError(
                "The Flask-Toolbar requires the 'SECRET_KEY' config "
                "var to be set")

        Toolbar.load_panels(app)

        app.before_request(self.process_request)
        app.after_request(self.process_response)
        app.teardown_request(self.teardown_request)

        # Monkey-patch the Flask.dispatch_request method
        app.dispatch_request = self.dispatch_request

        app.add_url_rule('/_toolbar/static/<path:filename>',
                         '_toolbar.static', self.send_static_file)

        app.register_blueprint(module, url_prefix='/_toolbar/views')

    def _default_config(self, app):
        return {
            'TB_ENABLED': app.debug,
            'TB_HOSTS': (),
            'TB_INTERCEPT_REDIRECTS': True,
            'TB_PANELS': (
                'flask_toolbar.panels.versions.VersionToolbarPanel',
                'flask_toolbar.panels.timer.TimerToolbarPanel',
                'flask_toolbar.panels.headers.HeaderToolbarPanel',
                'flask_toolbar.panels.request_vars.RequestVarsToolbarPanel',
                'flask_toolbar.panels.config_vars.ConfigVarsToolbarPanel',
                'flask_toolbar.panels.template.TemplateToolbarPanel',
                'flask_toolbar.panels.sqlalchemy.SQLAlchemyToolbarPanel',
                'flask_toolbar.panels.logger.LoggingPanel',
                'flask_toolbar.panels.route_list.RouteListToolbarPanel',
                'flask_toolbar.panels.profiler.ProfilerToolbarPanel',
            ),
        }

    def dispatch_request(self):
        """Modified version of Flask.dispatch_request to call process_view."""
        req = _request_ctx_stack.top.request
        app = current_app

        if req.routing_exception is not None:
            app.raise_routing_exception(req)

        rule = req.url_rule

        # if we provide automatic options for this URL and the
        # request came with the OPTIONS method, reply automatically
        if getattr(rule, 'provide_automatic_options', False) \
           and req.method == 'OPTIONS':
            return app.make_default_options_response()

        # otherwise dispatch to the handler for that endpoint
        view_func = app.view_functions[rule.endpoint]
        view_func = self.process_view(app, view_func, req.view_args)

        return view_func(**req.view_args)

    def _show_toolbar(self):
        """Return a boolean to indicate if we need to show the toolbar."""
        if request.blueprint == 'toolbar':
            return False

        hosts = current_app.config['TB_HOSTS']
        if hosts and request.remote_addr not in hosts:
            return False

        return True

    def send_static_file(self, filename):
        """Send a static file from the flask-toolbar static directory."""
        return send_from_directory(self._static_dir, filename)

    def process_request(self):
        g.toolbar = self

        if not self._show_toolbar():
            return

        real_request = request._get_current_object()

        self.toolbars[real_request] = (
            Toolbar(real_request, self.jinja_env))

        for panel in self.toolbars[real_request].panels:
            panel.process_request(real_request)

    def process_view(self, app, view_func, view_kwargs):
        """ This method is called just before the flask view is called.
        This is done by the dispatch_request method.
        """
        real_request = request._get_current_object()
        try:
            toolbar = self.toolbars[real_request]
        except KeyError:
            return view_func

        for panel in toolbar.panels:
            new_view = panel.process_view(real_request, view_func, view_kwargs)
            if new_view:
                view_func = new_view

        return view_func

    def process_response(self, response):
        real_request = request._get_current_object()
        if real_request not in self.toolbars:
            return response

        # Intercept http redirect codes and display an html page with a
        # link to the target.
        if current_app.config['TB_INTERCEPT_REDIRECTS']:
            if (response.status_code in self._redirect_codes and
                    not real_request.is_xhr):
                redirect_to = response.location
                redirect_code = response.status_code
                if redirect_to:
                    content = self.render('redirect.html', {
                        'redirect_to': redirect_to,
                        'redirect_code': redirect_code
                    })
                    response.content_length = len(content)
                    response.location = None
                    response.response = [content]
                    response.status_code = 200

        # If the http response code is 200 then we process to add the
        # toolbar to the returned html response.
        if not (response.status_code == 200 and
                response.is_sequence and
                response.headers['content-type'].startswith('text/html')):
            return response

        response_html = response.data.decode(response.charset)

        no_case = response_html.lower()
        body_end = no_case.rfind('</body>')

        if body_end >= 0:
            before = response_html[:body_end]
            after = response_html[body_end:]
        elif no_case.startswith('<!doctype html>'):
            before = response_html
            after = ''
        else:
            warnings.warn('Could not insert debug toolbar.'
                          ' </body> tag not found in response.')
            return response

        toolbar = self.toolbars[real_request]

        for panel in toolbar.panels:
            panel.process_response(real_request, response)

        toolbar_html = toolbar.render_toolbar()

        content = ''.join((before, toolbar_html, after))
        content = content.encode(response.charset)
        response.response = [content]
        response.content_length = len(content)

        return response

    def teardown_request(self, exc):
        self.toolbars.pop(request._get_current_object(), None)

    def render(self, template_name, context):
        template = self.jinja_env.get_template(template_name)
        return template.render(**context)
