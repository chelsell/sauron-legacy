
from prefect import Task, task, Flow
from prefect.tasks.notifications.slack_task import SlackTask

@task()
def verify_upload():
    pass


class VerifyUpload(Task):
    def run(self) -> int:
        pass

class InsertRun(Task):
    def run(self) -> int:
        pass

class InsertSensors(Task):
    def run(self) -> int:
        pass

class InsertFeature(Task):
    def run(self) -> int:
        pass
