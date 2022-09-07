from ..task_utils import *
from klgists.common import *
from valarpy.model import *


class BranchCalcFeatures:
        """
        Branching task that determines if it's necessary to insert well_features to Valar.
        """
        @staticmethod
        def run(sub: str, task_pass: str, task_calc_features: str, **kwargs) -> str:
                """
                Checks if all features associated with the run have been calculated
                :param sub: submission hash of run
                :param task_pass: Task ID of dummy task (Features have been calculated already)
                :param task_calc_features: Task ID of task for deciding feature to calculate
                :return:
                """
                ti = kwargs["ti"]
                feat_val = ti.xcom_pull(task_ids='retrieve_feat_type')
                run = TaskUtils.get_run(sub)
                plate_type = Runs.select(PlateTypes).join(Plates).join(PlateTypes).where(Runs.id == run.id).first().plate.plate_type
                n_exp_feats = plate_type.n_rows * plate_type.n_columns
                n_act_feats = WellFeatures.select(WellFeatures.well_id, Wells.id, Wells.run_id).join(Wells).where((WellFeatures.type == Features.fetch(feat_val)) & (Wells.run == run)).count()
                if n_exp_feats == n_act_feats:
                        return task_pass
                else:
                        return task_calc_features

__all__ = ['BranchCalcFeatures']
