from ..task_utils import *
from klgists.common import *


class BranchArchive:
	"""
	Branching task that determines if it's necessary to archive.
	"""
	@staticmethod
	def run(sub:str, path: str, task_pass: str, task_archive: str):
		store_path = ConfigUtils.storage_path(sub)
		link_path = pjoin('/', 'runs', 'by-hash', sub)
		moved = pjoin(store_path, '.moved')
		# Using data from shire, just make .moved token for bookkeeping purposes
		if path == store_path or path == link_path:
			if not pexists(moved):
				with open(moved, 'w') as f:
					pass
			return task_pass
		else:
			return task_archive


__all__ = ['BranchArchive']