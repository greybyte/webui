from aw.base import USERS
from aw.model.job import JobExecution, JobExecutionResultHost
from aw.model.alert import BaseAlert, AlertPlugin


def alert_plugin_wrapper(alert: BaseAlert, user: USERS, stats: [JobExecutionResultHost], execution: JobExecution):
    # implement plugin interface
    pass
