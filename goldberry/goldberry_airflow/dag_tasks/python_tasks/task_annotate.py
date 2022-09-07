from ..task_utils import *
from klgists.common import *
from valarpy.model import *
import logging

class TaskAnnotate:
	"""
	DAG Task for adding annotations to id and history files.
	"""
	@staticmethod
	def run(sub: str, path: str):
		curr_run = TaskUtils.get_run(sub)
		path_dict = {
			pjoin(path, '.id'): 'w',
			pjoin(path, 'camera', '.id'): 'w',
			pjoin(path, '.history'): 'a'
		}
		logging.info("Annotating... ")
		for k, v in path_dict.items():
			TaskAnnotate._write_ids(curr_run, k, v)
			logging.info("Added the {} file. ".format(k))
		logging.info("Finished Annotating. ")


	@staticmethod
	def _write_ids(run: Runs, pathname: str, option: str):
		with open(pathname,  option) as f:
			if option == 'a':
				f.write('================ {} ================\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
			f.write('submissions.lookup_hash={}\n'.format(run.submission.lookup_hash))
			f.write('runs.id={}\n'.format(run.id))
			f.write('runs.tag={}\n'.format(run.tag))
			f.write('runs.name={}\n'.format(run.name))
			if option == 'a':
				f.write(((16 + 2 + 19 + 2 + 16) * '=') + '\n')


__all__ = ['TaskAnnotate']