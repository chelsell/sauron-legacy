import sys, os
sys.path.insert(0,os.path.abspath(os.environ['GOLDBERRY']))
from scripts.filesystem.reindex import *
from valarpy.Valar import Valar
from ..task_utils import *
import logging


class TaskAddSymLink:
	@staticmethod
	def run(sub: str):
		logging.info("Adding Symlink for submission {}".format(sub))
		run_id = TaskUtils.get_run(sub).get_id()
		logging.info("Run_id: {}".format(run_id))
		with Valar() as valar:
			Reindexer(valar).reindex(run_id)
			logging.info("SymLinks added for : {}".format(run_id))


__all__ = ['TaskAddSymLink']