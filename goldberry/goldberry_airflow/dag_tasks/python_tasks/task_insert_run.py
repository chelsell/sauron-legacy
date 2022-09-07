from klgists.files.wrap_cmd_call import wrap_cmd_call
from ..task_utils import *
from valarpy.model import *
import logging


class TaskInsertRun:
        """
        DAG Task for inserting run data into the Runs table in Valar. Delegates to the DirectoryLoader Scala script
        for insertion.
        """
        @staticmethod
        def run(sub: str, path: str, **kwargs) -> None:
                """
                Executes task for inserting run into valar.
                :param sub: Submission Hash
                :param path: Pathname of where run metadata is located.
                :return:
                """
                ti = kwargs["ti"]
                logging.info("Inserting run with sub_hash {} to Valar".format(sub))
                wrap_cmd_call(
                        ['sbt', 'project importer', '-mem', '256','runMain kokellab.valar.importer.DirectoryLoader "{}"'.format(path)],
                        cwd=ConfigUtils.gen_repo_path("valar")
                )
                TaskUtils.update_status('inserting sensors', ti.xcom_pull(task_ids='retrieve_sub_info'))
                wrap_cmd_call(
                        ['sbt', 'project importer', '-mem','1024', 'runMain kokellab.valar.importer.SensorProcessor "{}"'.format(path)], cwd=ConfigUtils.gen_repo_path("valar")
                        )
                run_id = TaskUtils.get_run(sub).id
                TaskUtils.update_status('inserted sensors', ti.xcom_pull(task_ids='retrieve_sub_info'))
                logging.info("Successfully inserted run to Valar. Run ID: {}".format(run_id))


__all__ = ['TaskInsertRun']
