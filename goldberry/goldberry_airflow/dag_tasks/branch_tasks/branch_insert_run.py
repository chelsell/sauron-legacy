from ..task_utils import *
from klgists.common import *
from valarpy.model import *


class BranchInsertRun:
	"""
	Branching task that determines if it's necessary to insert run to Valar.
	"""
	@staticmethod
	def run(sub: str, task_pass: str, task_insert_run: str) -> str:
		"""
		Checks if a run associated with the submission hash exists.
		:param sub: submission hash of run
		:param task_pass: Task ID of dummy task (Run has been inserted already)
		:param task_insert_run: Task ID of insert_run task (Run with sub hash doesn't exist, insert into Valar)
		:return:
		"""
		run = TaskUtils.get_run(sub)
		if run is not None:
			return task_pass
		else:
			return task_insert_run


__all__ = ['BranchInsertRun']