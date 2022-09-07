from ..task_utils import *
from klgists.common import *


class BranchMakeVideo:
	"""
	Branching task that determines if it's necessary to make video.
	"""
	@staticmethod
	def run(sub_path: str, task_pass: str, task_make_video: str) -> str:
		"""
		Checks if video file hash exists. Branches to either a dummy task or the make_video task.
		:param sub_path: path to submission directory that contains frames
		:param task_pass: Task ID that corresponds to dummy_task
		:param task_make_video: Task ID that corresponds to task for making video
		:return: Task ID that dictates next task, NOT class of next task. Task IDs are defined when DAGs are defined.
		"""
		h_path = TaskUtils.video_file_hash(sub_path)
		if pexists(h_path):
			return task_pass
		else:
			return task_make_video


__all__ = ['BranchMakeVideo']