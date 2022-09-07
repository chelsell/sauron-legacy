from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

import os

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2015, 6, 1),
    'email': [],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=5)
    }
dag = DAG(
    'valar_backups', default_args=default_args, max_active_runs = 1, catchup = False, schedule_interval= '0 8 * * *')

forever_sh = '/data/repos/valar/scripts/forever_bak_task.sh'
nightly_sh = '/data/repos/valar/scripts/nightly_bak_task.sh'

with dag: 
    if os.path.exists(forever_sh):
        t1 = BashOperator(
            task_id='valar_backup_forever',
            bash_command='bash '+forever_sh+' ',
            pool='archive_pool'
            )
    else:
        raise Exception("{} not found.".format(forever_sh))

    if os.path.exists(nightly_sh):
        t2 = BashOperator(
            task_id='valar_backup_nightly',
            bash_command='bash '+nightly_sh+ ' ',
            pool='archive_pool'
            )
    else: 
        raise Exception("{} not found.".format(nightly_sh))
t1 >> t2 
