from airflow.operators.mysql_operator import MySqlOperator
from airflow.hooks.mysql_hook import MySqlHook


class MySqlOperatorReturns(MySqlOperator):
    """
    MySqlOperator that returns results
    """
    def execute(self, context):
        self.log.info('Executing: %s', self.sql)
        hook = MySqlHook(mysql_conn_id=self.mysql_conn_id, schema=self.database)
        return hook.get_records(self.sql, parameters=self.parameters)[0][0]


__all__ = ['MySqlOperatorReturns']