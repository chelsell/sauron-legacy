from klgists.common import *
from ..task_utils import *
from klgists.files import make_dirs
from klgists.files.wrap_cmd_call import wrap_cmd_call
import logging


class TaskArchive:
	"""
	DAG Task for archiving. Moves data from valinor to shire.
	"""
	@staticmethod
	def run(sub: str, path: str, **kwargs):
		ti = kwargs['ti']
		store_path = ConfigUtils.storage_path(sub)
		if pexists(store_path):
			logging.info("{} already exists.".format(store_path))
		else:
			make_dirs(os.path.dirname(store_path))
		TaskUtils.update_status('archiving', ti.xcom_pull(task_ids='retrieve_sub_info'))
		wrap_cmd_call(['rsync', '-avz', '--ignore-existing', '--remove-source-files', path + '/', store_path])
		with open(pjoin(store_path, '.moved'),  'w') as f:
			logging.info(".moved file created.")
		logging.info("Successfully copied to {}".format(store_path))
		logging.info("Deleting {}".format(path))
		wrap_cmd_call(['find', path, '-type', 'd', '-empty', '-delete'])
		logging.info("Deleted {}".format(path))
		TaskUtils.update_status('archived', ti.xcom_pull(task_ids='retrieve_sub_info'))


__all__ = ['TaskArchive']