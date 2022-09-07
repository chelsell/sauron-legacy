from airflow.hooks.base_hook import BaseHook
from airflow.operators.slack_operator import SlackAPIPostOperator
from valarpy.model import *

import os
import array as arr
SLACK_CONN_ID = 'slack'


class SlackFailAlert:

    @staticmethod
    def _parse_log(filename: str):
        with open(filename, 'r') as f:
            return f.read()

    @staticmethod
    def run(context):
        """
        Sends slack message on failure of DAG task.
        :param context:
        :return:
        """
        notifs = BaseHook.get_connection(SLACK_CONN_ID).login
        slack_token = BaseHook.get_connection(SLACK_CONN_ID).password
        failed_alert = SlackAPIPostOperator(
            task_id='slack_failed',
            channel=notifs,
            icon_url='https://avatars.slack-edge.com/2017-12-08/284284180357_c7fb8fd3297e4fb50da9_512.jpg',
            username='goldberry',
            token=slack_token,
            attachments=[
            {
                "pretext": "Task failed for submission {sub}".format(
                    sub=context.get('task_instance').xcom_pull(task_ids='retrieve_dag_name')
                ),
                "color": "danger",
                "fields": [
                    {
                        "title": "Dag",
                        "value": """{}""".format(context.get('task_instance').dag_id),
                        "short": True
                    },
                    {
                        "title": "Task",
                        "value": """{}""".format(context.get('task_instance').task_id),
                        "short": True
                    },
                    {
                        "title": "Submission Description",
                        "value": """{}""".format(
                            Submissions.fetch((context.get('task_instance').dag_id)).description
                        ),
                        "short": True
                    }
                    ,
                    {
                        "title": "Execution Time",
                        "value": """{}""".format(context.get('execution_date')),
                        "short": True
                    }
                ],
                "text": """```{}```""".format(SlackFailAlert._parse_log(
                os.path.join(context.get('task_instance').log_filepath[:-4], '2') + '.log')
                )
            }
            ],
            text="",
        )
        return failed_alert.execute(context=context)


__all__ = ['SlackFailAlert']