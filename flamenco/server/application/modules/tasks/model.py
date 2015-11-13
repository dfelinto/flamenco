from application import db

class Task(db.Model):
    """Tasks are created after a Shot is added

    Tasks can be reassigned individually to a different worker, but can be
    deleted and recreated all together. A task is made of "commands" or
    instructions, for example:
    * Check out SVN revision 1954
    * Clean the /tmp folder
    * Render frames 1 to 5 of scene_1.blend
    * Send email with results to user@flamenco-farm.org

    Possible statuses for a job are:
    * 0 Waiting (tasks for this job are ready to be dispatched)
    * 1 Active
    * 2 Canceled
    * 3 Failed
    * 4 Completed
    * 5 Processing
    """
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    job = db.relationship('Job',
        backref=db.backref('tasks', lazy='dynamic'))
    manager_id = db.Column(db.Integer())
    name = db.Column(db.String(64))
    status = db.Column(db.String(64))
    priority = db.Column(db.Integer())
    type = db.Column(db.String(64))
    settings = db.Column(db.Text())
    log = db.Column(db.Text())
    activity = db.Column(db.String(128))
    child_id = db.Column(db.Integer())
    parser = db.Column(db.String(64))
    time_cost = db.Column(db.Integer())
    last_activity = db.Column(db.DateTime())
    # Currently the hostname, later will be a serialized dictionary, storing
    # id and hostname of a worker
    worker = db.Column(db.String(128))

    # Convenience list that maps status name with the IDs stored in the db
    statuses_list = ['waiting', 'active', 'canceled', 'failed', 'completed',
    'processing']

    @property
    def status_name(self):
        """Human representation of a status name"""
        return statuses_list[self.status]

    @status_name.setter
    def status_name(self, value):
        value = statuses_list.index(value)
        self.status = value


    def __repr__(self):
        return '<Task %r>' % self.id
