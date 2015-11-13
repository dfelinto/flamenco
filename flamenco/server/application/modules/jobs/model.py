import datetime
from application import db

from application.modules.managers.model import Manager
from application.modules.users.model import User

class Job(db.Model):
    """A Job is the basic work unit of Flamenco

    The creation of a job can happen in different ways:
    * within Flamenco (using the job creation form)
    * via a query from an external software (e.g. Attract)
    * within Blender itself, via an addon

    Possible statuses for a job are:
    * 0 Waiting (tasks for this job are ready to be dispatched)
    * 1 Active
    * 2 Canceled
    * 3 Failed
    * 4 Completed

    In the database (and some other place) we use int types to reference
    statuses, for indexing and query speed.
    """
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    project = db.relationship('Project',
        backref=db.backref('jobs', lazy='dynamic'))
    name = db.Column(db.String(120))
    status = db.Column(db.String(64))
    priority = db.Column(db.Integer())
    settings = db.Column(db.Text())
    creation_date = db.Column(db.DateTime(), default=datetime.datetime.now)
    date_edit = db.Column(db.DateTime())
    type = db.Column(db.String(64))
    tasks_status = db.Column(db.String(256))
    notes = db.Column(db.Text())
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('job', lazy='dynamic'))

    # Convenience list that maps status name with the IDs stored in the db
    statuses_list = ['waiting', 'active', 'canceled', 'failed', 'completed']

    @property
    def status_name(self):
        """Human representation of a status name"""
        return statuses_list[self.status]

    @status_name.setter
    def status_name(self, value):
        value = statuses_list.index(value)
        self.status = value

    def __repr__(self):
        return '<Job %r>' % self.name

class JobManagers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer(), db.ForeignKey('job.id'))
    job = db.relationship('Job', backref=db.backref('manager_list', lazy='dynamic'))
    manager_id = db.Column(db.Integer(), db.ForeignKey('manager.id'))
    manager = db.relationship('Manager', backref=db.backref('jobs_list', lazy='dynamic'))

# TODO: look into the benefits of using the standard many to many
# job_managers_table = db.Table('job_managers', db.Model.metadata,
#     db.Column('job_id', db.Integer, db.ForeignKey('jon.id', ondelete='CASCADE')),
#     db.Column('manager_id', db.Integer, db.ForeignKey('manager.id'))
#     )
