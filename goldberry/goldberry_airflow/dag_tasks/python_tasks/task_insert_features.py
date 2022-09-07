from ..task_utils import *
from klgists.files.wrap_cmd_call import wrap_cmd_call
from klgists.common import *
from valarpy.model import *
import logging


class TaskInsertCalcFeatures:
        """
        DAG Task that calculates and inserts well_features based on SauronX model.
        """
        @staticmethod
        def run(sub: str, path: str, **kwargs):
                ti = kwargs['ti']
                curr_run = TaskUtils.get_run(sub)
                feat_val = ti.xcom_pull(task_ids='retrieve_feat_type')
                if feat_val == 4:
                        feature = 'cd(10)'
                else:
                        feature = 'MI'
                logging.info("Calculating {} for Run {}".format(feature, curr_run.id))
                TaskUtils.update_status('inserting features', ti.xcom_pull(task_ids='retrieve_sub_info'))
                wrap_cmd_call([
                        'sbt', 'project simple', '-mem', '512',
                        'runMain kokellab.lorien.simple.FeatureProcessor {} {} "{}"'.format(
                                feature, curr_run, TaskUtils.video_file(path))], cwd=ConfigUtils.gen_repo_path('lorien'))
                logging.info("Completed {} calculation for Run {}".format(feature, curr_run.id))
                TaskUtils.update_status('inserted features', ti.xcom_pull(task_ids='retrieve_sub_info'))


__all__ = ['TaskInsertCalcFeatures']
