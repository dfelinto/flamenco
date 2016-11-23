#! /usr/bin/env python2
import os
import logging
import socket
import json
import sqlalchemy.exc

from flask.ext.script import Manager
from flask.ext.migrate import MigrateCommand
from flask.ext.migrate import upgrade
from sqlalchemy import create_engine
from alembic.migration import MigrationContext

from application import app
from application import db
from application import register_manager

from application.modules.job_types.model import JobType

manager = Manager(app)
manager.add_command('db', MigrateCommand)

log = logging.getLogger(__name__)


@manager.command
def setup_db():
    """Create database and required tables."""
    if not app.config['DATABASE_URI'].startswith('sqlite'):
        try:
            with create_engine(
                app.config['DATABASE_URI'],
            ).connect() as connection:
                connection.execute('CREATE DATABASE {0}'.format(
                    app.config['DATABASE_NAME']))
            print("Database created")
        except sqlalchemy.exc.OperationalError:
            pass
        except sqlalchemy.exc.ProgrammingError:
            # If database already exists
            pass

    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    conn = engine.connect()
    context = MigrationContext.configure(conn)
    current_ver = context.get_current_revision()
    if not current_ver:
        print("Automatic DB Upgrade")
        print("Press Ctrl+C when finished")
        upgrade()
        print("Upgrade completed. Press Ctrl+C and runserver again.")

    # TODO: search for the task_compilers and ask for required commands accordingly
    # Render Config
    render_config = JobType.query.filter_by(name='blender_simple_render').first()
    if not render_config:
        log.debug('Creating blender_simple_render.')
        configuration = {
                'blender_render': get_blender_render(),
                }
        render_config = JobType(
            name='blender_simple_render',
            properties=json.dumps(configuration))
        db.session.add(render_config)
        db.session.commit()

    # Render resume config
    render_resume = JobType.query.filter_by(name='blender_resume_render').first()
    if not render_resume:
        log.debug('Creating blender_resume_render job_type.')
        configuration = {
                'blender_render': get_blender_render(),
                'imagemagick_convert': get_imagemagick_convert(),
                'move_file': get_move_file(),
                'delete_file': get_delete_file(),
                }
        render_resume_config = JobType(
                name='blender_resume_render',
                properties=json.dumps(configuration))
        db.session.add(render_resume_config)
        db.session.commit()

    # The sleep simple command, used for testing and with OS defaults already set.
    sleep_simple = JobType.query.filter_by(name='sleep_simple').first()
    if not sleep_simple:
        log.debug('Creating sleep_simple job_type.')
        configuration = {
                'sleep': get_sleep(),
                }
        sleep_config = JobType(
            name='sleep_simple',
            properties=json.dumps(configuration))
        db.session.add(sleep_config)
        db.session.commit()


@manager.command
def setup_register_manager():
    # Register the manager to the server
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        if app.config['VIRTUAL_WORKERS']:
            has_virtual_worker = 1
        else:
            has_virtual_worker = 0
        full_host = "http://{0}:{1}".format(
            app.config['HOST'], app.config['PORT'])
        register_manager(app.config['PORT'], app.config['NAME'], has_virtual_worker)


@manager.command
def runserver():
    """This command is meant for development. If no configuration is found,
    we start the app listening from all hosts, from port 7777."""
    setup_db()
    #setup_register_manager()

    app.run(
        port=app.config['PORT'],
        debug=app.config['DEBUG'],
        host=app.config['HOST'],
        threaded=True)


configuration_cache = {}

def job_type(settings_name):
    if settings_name not in configuration_cache:
        configuration = {
            'Linux': '',
            'Darwin': '',
            'Windows': ''
        }

        print("Please enter the shared path for the {0} "
              "command".format(settings_name))

        configuration['Linux'] = raw_input('Linux path: ')
        configuration['Darwin'] = raw_input('OSX path: ')
        configuration['Windows'] = raw_input('Windows path: ')

        configuration_cache[settings_name] = configuration

    return configuration_cache[settings_name]


def get_blender_render():
    """Render setup for Blender related tasks"""
    return job_type('blender_render')


def get_imagemagick_convert():
    """Render setup for imagemagick related tasks"""
    return job_type('imagemagick_convert')


def get_sleep():
    """"""
    configuration = {
            'Linux': 'sleep',
            'Darwin': 'sleep',
            'Windows': 'timeout'
        }
    return configuration


def get_move_file():
    """"""
    configuration = {
            'Linux': 'mv',
            'Darwin': 'mv',
            'Windows': 'rename'
        }
    return configuration


def get_delete_file():
    """"""
    configuration = {
            'Linux': 'rm',
            'Darwin': 'rm',
            'Windows': 'del'
        }
    return configuration


if __name__ == "__main__":
    manager.run()
