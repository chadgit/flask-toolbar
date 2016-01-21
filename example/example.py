import sys
sys.path.insert(0, '.')

from flask import Flask, render_template, redirect, url_for
from flask.ext.script import Manager
from flask.ext.sqlalchemy import SQLAlchemy
from flask_toolbar import ToolbarExtension


app = Flask(__name__)
app.config['TB_INTERCEPT_REDIRECTS'] = True
#app.config['TB_PANELS'] = (
#    'flask_toolbar.panels.headers.HeaderToolbarPanel',
#    'flask_toolbar.panels.logger.LoggingPanel',
#    'flask_toolbar.panels.timer.TimerToolbarPanel',
#)
#app.config['TB_HOSTS'] = ('127.0.0.1', '::1' )
app.config['SECRET_KEY'] = 'asd'
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

toolbar = ToolbarExtension(app)


class ExampleModel(db.Model):
    __tablename__ = 'examples'
    value = db.Column(db.String(100), primary_key=True)


@app.route('/')
def index():
    app.logger.info("Hello there")
    ExampleModel.query.get(1)
    return render_template('index.html')


@app.route('/redirect')
def redirect_example():

    response = redirect(url_for('index'))
    response.set_cookie('test_cookie', '1')
    return response

if __name__ == "__main__":
    db.create_all()

    manager = Manager(app)
    manager.run()
