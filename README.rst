Flask Toolbar
===================

This is a port of the excellent `django-toolbar <https://github.com/django-toolbar/django-toolbar>`_
for Flask applications.

.. image:: https://travis-ci.org/mgood/flask-toolbar.png?branch=master
   :target: https://travis-ci.org/mgood/flask-toolbar


Installation
------------

Installing is simple with pip::

    $ pip install flask-toolbar


Usage
-----

Setting up the debug toolbar is simple::

    from flask import Flask
    from flask_toolbar import ToolbarExtension

    app = Flask(__name__)

    # the toolbar is only enabled in debug mode:
    app.debug = True

    # set a 'SECRET_KEY' to enable the Flask session cookies
    app.config['SECRET_KEY'] = '<replace with a secret key>'

    toolbar = ToolbarExtension(app)


The toolbar will automatically be injected into Jinja templates when debug mode is on.
In production, setting ``app.debug = False`` will disable the toolbar.

See the `documentation`_ for more information.

.. _documentation: http://flask-toolbar.readthedocs.org
