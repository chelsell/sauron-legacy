from datetime import datetime, timedelta
from airflow import DAG
from klgists.common import *
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from goldberry_airflow.operators.mysqlr_operator import *

# Import Python Tasks
from .dag_tasks.python_tasks.task_make_video import *
from .dag_tasks.python_tasks.task_annotate import *
from .dag_tasks.python_tasks.task_insert_run import *
from .dag_tasks.python_tasks.task_insert_features import *
from .dag_tasks.python_tasks.task_archive import *
from .dag_tasks.python_tasks.task_add_symlink import *
from .dag_tasks.python_tasks.task_retrieve_sub_info import *
from .dag_tasks.slack_tasks.task_msg_user import *
from .dag_tasks.slack_tasks.slack_fail_alert import *

# Import Branch Tasks
from .dag_tasks.branch_tasks.branch_archive import *
from .dag_tasks.branch_tasks.branch_calc_features import *
from .dag_tasks.branch_tasks.branch_insert_run import *
from .dag_tasks.branch_tasks.branch_make_video import *

import pickle
from .dag_tasks.task_utils import *

SLACK_CONN_ID = 'slack'


def identity(sub: str, **kwargs):
        return sub

def feat_type(feat_num: int, **kwargs):
        return feat_num

class CreateDag:
        """
        DAG Task responsible for creating a Submission DAG
        """
        @staticmethod
        def run(sub: str, pickle_dags_dir: str, feature_type: int):
                default_args = {
                        'owner': 'airflow',
                        'depends_on_past': False,
                        'start_date': datetime(2015, 6, 1),
                        'email': [],
                        'email_on_failure': False,
                        'email_on_retry': False,
                        'retries': 1,
                        'on_failure_callback': SlackFailAlert.run,
                        'retry_delay': timedelta(seconds=1)
                }
                path = ConfigUtils.find_path(sub)
                dag = DAG(sub, default_args=default_args, schedule_interval=None, max_active_runs=1)
                with dag:
                        # RETRIEVE DAG NAME
                        # Necessary for SlackFailAlert to have access to the sub name
                        t_ret_name = PythonOperator(
                                task_id='retrieve_dag_name',
                                python_callable=identity,
                                op_args=[sub]
                        )
                        # RETRIEVE_SUB_INFO
                        t_ret_sub_info = PythonOperator(
                                task_id='retrieve_sub_info',
                                python_callable=TaskRetrieveSubInfo.run,
                                op_args=[sub]
                        )
                        # RETRIEVE_FEAT_TYPE
                        t_ret_feat_type = PythonOperator(
                            task_id='retrieve_feat_type',
                            python_callable=feat_type,
                            op_args=[feature_type]
                        )
                        # BRANCH_MAKE_VIDEO
                        id_dmv = 'dummy_make_vid'
                        id_mv = 'make_video'
                        b_make_vid = BranchPythonOperator(
                                task_id='branch_make_vid',
                                python_callable=BranchMakeVideo.run,
                                op_args=[path, id_dmv, id_mv]
                        )
                        d_make_vid = DummyOperator(task_id=id_dmv)
                        t_make_vid = PythonOperator(
                                task_id=id_mv,
                                python_callable=TaskMakeVideo.run,
                                provide_context=True,
                                op_args=[sub, path],
                                pool='insertion_pool'
                        )
                        # BRANCH_INSERT_RUN
                        b_ins_run = BranchPythonOperator(
                                task_id='branch_insert_run',
                                python_callable=BranchInsertRun.run,
                                op_args=[sub, 'dummy_insert_run', 'insert_run'],
                                trigger_rule='none_failed'
                        )
                        d_ins_run = DummyOperator(task_id='dummy_insert_run')
                        t_ins_run = PythonOperator(
                                task_id='insert_run',
                                python_callable=TaskInsertRun.run,
                                provide_context=True,
                                op_args=[sub, path],
                                pool='insertion_pool'
                        )
                        # BRANCH_CALC_FEATURES
                        b_calc_feats = BranchPythonOperator(
                                task_id='branch_calc_features',
                                python_callable=BranchCalcFeatures.run,
                                provide_context=True,
                                op_args=[sub, 'dummy_insert_features', 'insert_features'],
                                trigger_rule='none_failed'
                        )
                        d_calc_feats = DummyOperator(task_id='dummy_insert_features')
                        t_calc_feats = PythonOperator(
                                task_id='insert_features',
                                python_callable=TaskInsertCalcFeatures.run,
                                provide_context=True,
                                op_args=[sub, path],
                                pool='insertion_pool'
                        )

                        # TASK_ANNOTATE (only one task before)
                        t_annotate = PythonOperator(
                                task_id='annotate',
                                python_callable=TaskAnnotate.run,
                                op_args=[sub, path],
                                trigger_rule='none_failed'
                        )

                        # BRANCH_ARCHIVE (only one task before)
                        b_archive = BranchPythonOperator(
                                task_id='branch_archive',
                                python_callable=BranchArchive.run,
                                op_args=[sub, path, 'dummy_archive', 'archive'],
                                trigger_rule='none_failed'
                        )
                        d_archive = DummyOperator(task_id='dummy_archive')
                        t_archive = PythonOperator(
                                task_id='archive',
                                python_callable=TaskArchive.run,
                                provide_context=True,
                                op_args=[sub, path],
                                pool='archive_pool'
                        )
                        t_add_sym_link = PythonOperator(
                                task_id='add_symlink',
                                python_callable=TaskAddSymLink.run,
                                op_args=[sub],
                                trigger_rule='none_failed'
                        )
                        t_message = PythonOperator(
                                task_id='slack_finish',
                                python_callable=MessageUser.run,
                                op_args=[sub, "Successfully processed "],
                                trigger_rule='none_failed'
                        )
                        t_delete_dag = BashOperator(
                                task_id='delete_dag',
                                bash_command="""
                                mkdir -p /var/airflow/dags/completed_dags/
                                mv /var/airflow/dags/pickled_dags/{0}.obj /var/airflow/dags/completed_dags/
                                curl -X "DELETE" http://127.0.0.1:8080/api/experimental/dags/{0}
                                """.format(sub)
                        )
                        t_ret_name.set_downstream(t_ret_sub_info)
                        t_ret_sub_info.set_downstream(t_ret_feat_type)
                        t_ret_feat_type.set_downstream(b_make_vid)
                        b_make_vid.set_downstream([t_make_vid, d_make_vid])
                        b_ins_run.set_upstream([t_make_vid, d_make_vid])
                        b_ins_run.set_downstream([d_ins_run, t_ins_run])
                        b_calc_feats.set_upstream([d_ins_run, t_ins_run])
                        b_calc_feats.set_downstream([d_calc_feats, t_calc_feats])
                        t_annotate.set_upstream([d_calc_feats, t_calc_feats])
                        b_archive.set_upstream(t_annotate)
                        b_archive.set_downstream([d_archive, t_archive])
                        t_add_sym_link.set_upstream([d_archive, t_archive])
                        t_add_sym_link.set_downstream(t_message)
                        t_message.set_downstream(t_delete_dag)
                file_handler = open(pjoin(pickle_dags_dir, '{}.obj'.format(sub)), 'wb')
                pickle.dump(dag, file_handler)


__all__ = ['CreateDag']
