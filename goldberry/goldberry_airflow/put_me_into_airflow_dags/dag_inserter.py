from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2019, 6, 1),
    'email': [],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(seconds=1)
}

dag = DAG(
    'dag_inserter', default_args=default_args, max_active_runs=1, catchup=False, schedule_interval=timedelta(minutes=1))

with dag:
    b1 = BashOperator(
        task_id='insert_dag',
        bash_command=
        """
            for entry in `ls /alpha/uploads`; do
                sql_check=$(mysql -u root -D valar -s -N  -e "select sauron_id from submission_records r left outer join submissions s on s.id = r.submission_id where s.lookup_hash = '${entry}'
                AND r.status = 'uploaded'")
                dags_check=$(mysql -u root -D valar  -e "select * from dags_to_create where submission_hash = '${entry}'")
                if [ "$sql_check" -eq 4 ] || [ "$sql_check" -eq 7 ] || [ "$sql_check" -ge 10 ]; then
                    feature_type=4
                else
                    feature_type=1
                fi
                if [ ! -z "$sql_check" ] && [ -z "$dags_check" ]; then
                    mysql -u root -D valar -e "insert into dags_to_create(submission_hash, feature_type) values('${entry}', '${feature_type}')"
                else
                    echo "${entry} is already in the dags_to_create table"
                fi;
            done
        """
    )
