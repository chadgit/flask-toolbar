import os
from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))

try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()
except:
    README = ''
    CHANGES = ''


setup(
    name='Flask-Toolbar',
    version='0.00.1',
    url='http://flask-toolbar.rtfd.org/',
    license='BSD',
    author='Chad Collins',
    author_email='chad@chadcollins.com',
    maintainer='Chad Collins',
    maintainer_email='chad@chadcollins.com',
    description='A toolbar for flask and ui developers. Browser based editors for .python, and client side files.',
    long_description=README + '\n\n' + CHANGES,
    zip_safe=False,
    platforms='any',
    include_package_data=True,
    packages=['flask_toolbar',
              'flask_toolbar.panels'
    ],
    install_requires=[
        'Flask>=0.8',
        'Blinker',
        'itsdangerous',
        'werkzeug',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
