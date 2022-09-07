import sys, os
sys.path.insert(0,os.path.abspath(os.environ['GOLDBERRY']))
sys.path.append(os.path.abspath(os.environ['KALE']))
from kale.core.valar_singleton import *
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.mysql_operator import MySqlOperator
from airflow.sensors.sql_sensor import SqlSensor
from datetime import datetime, timedelta
from goldberry_airflow.create_dags import *
from goldberry_airflow.operators.mysqlr_operator import *
from goldberry_airflow.dag_tasks.slack_tasks.task_msg_user import *
from goldberry_airflow.dag_tasks.slack_tasks.slack_fail_alert import *


pickle_dags_dir = os.environ['AIRFLOW_PICKLED_DAGS']
SLACK_CONN_ID = 'slack'


def create_dag(pickle_dir: str, **kwargs):
    ti = kwargs["ti"]
    CreateDag.run(ti.xcom_pull(task_ids='retrieve_dag_name'), pickle_dir, ti.xcom_pull(task_ids='retrieve_feat_type'))


def message_user(message: str, **kwargs):
    ti = kwargs["ti"]
    MessageUser.run(ti.xcom_pull(task_ids='retrieve_dag_name'), message)


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2019, 6, 1),
    'email': [],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=1),
    'on_failure_callback': SlackFailAlert.run
}

dag = DAG(
    'dag_creator', default_args=default_args, max_active_runs=1, catchup = False, schedule_interval=timedelta(seconds = 5))

with dag:
    s1 = SqlSensor(
        task_id='query_check',
        conn_id='dag_db',
        sql='select * from dags_to_create where dag_created = 0',
        poke_interval=30
        )
    sq1 = MySqlOperatorReturns(
        task_id='retrieve_dag_name',
        mysql_conn_id='dag_db',
        sql='select submission_hash from dags_to_create where dag_created = 0 limit 1;')
    sq2 = MySqlOperatorReturns(
        task_id='retrieve_feat_type',
        mysql_conn_id='dag_db',
        sql="""select feature_type from dags_to_create where dag_created = 0 and submission_hash ='{{task_instance.xcom_pull(task_ids='retrieve_dag_name')}}' ;"""
        )
    t1 = PythonOperator(
        task_id='create_dag',
        provide_context=True,
        python_callable=create_dag,
        op_args=[pickle_dags_dir]
    )
    sq3 = MySqlOperator(
        task_id='update_row_dag_created',
        mysql_conn_id ='dag_db',
        sql="""UPDATE dags_to_create set dag_created = 1 where submission_hash = '{{task_instance.xcom_pull(task_ids='retrieve_dag_name')}}';"""
        )
    b1 = BashOperator(
        task_id='trigger_submission',
        bash_command="""
        airflow unpause {{task_instance.xcom_pull(task_ids='retrieve_dag_name')}}
        airflow trigger_dag {{task_instance.xcom_pull(task_ids='retrieve_dag_name')}}
        """
    )
    sl1 = PythonOperator(
        task_id='slack_user',
        provide_context=True,
        python_callable=message_user,
        op_args=['Processing']
    )

s1 >> sq1 >> sq2 >> t1 >> sq3 >> b1 >> sl1
