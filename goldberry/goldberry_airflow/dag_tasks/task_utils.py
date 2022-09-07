from klgists.common import *
from typing import Union, List
from klgists.files import make_dirs
from valarpy.model import *
from .python_tasks.task_retrieve_sub_info import SubmissionInfo
import datetime

import logging
import json
import os


class FileDoesNotExistError(Exception): pass


class ConfigUtils:
	"""
	Utility functions that are used to access variables in config.json
	"""

	@staticmethod
	def get_key(attribute: str) -> Union[str, int]:
		"""
		Returns value of attribute in the config file
		:param attribute: String of key in config file
		:return:
		"""
		with open(os.path.abspath(pjoin(os.environ["GOLDBERRY"], 'goldberry_airflow', 'config.json'))) as json_file:
			data = json.load(json_file)
			return data[attribute]

	@staticmethod
	def gen_repo_path(repo: str) -> str:
		"""
		Returbs absolute path name to provided repo
		:param repo
		:return: absolute pathname to specified repo
		"""
		return os.path.abspath(pjoin(os.path.expanduser('~'), *ConfigUtils.get_key('repo_path'), repo))

	@staticmethod
	def storage_path(sub: str) -> str:
		curr_run = TaskUtils.get_run(sub)
		if curr_run:
			store_path = pjoin(
				*ConfigUtils.get_key('store_path'),
				str(curr_run.datetime_run.year).zfill(4),
				str(curr_run.datetime_run.month).zfill(2),
				str(curr_run.tag)
			)
			return store_path

	@staticmethod
	def link_path(sub: str) -> str:
		f = pjoin(*ConfigUtils.get_key('link_path'), sub)
		return f if pexists(f) else None

	@staticmethod
	def find_path(sub: str) -> str:
		u_path = pjoin(*ConfigUtils.get_key("upload_path"), sub)
		if pexists(u_path):
			return u_path
		s_path = ConfigUtils.storage_path(sub)
		if s_path:
			return s_path
		l_path = ConfigUtils.link_path(sub)
		if l_path:
			return l_path
		else:
			raise FileDoesNotExistError("Submission {} was not found under uploads or store".format(sub))


class TaskUtils:
	"""
	Utility functions that are used in multiple tasks
	"""

	@staticmethod
	def video_file(sub_path: str) -> str:
		"""
		Returns the path that the video file will be saved in.
		:param sub_path: Path to submission folder that contains frames.7z and other data acquired from SauronX
		:return: pathname to video file
		"""
		return pjoin(sub_path, 'camera', 'x265-crf{}'.format(ConfigUtils.get_key('crf')), 'x265-crf{}.mkv'.format(ConfigUtils.get_key('crf')))

	@staticmethod
	def video_file_hash(sub_path: str) -> str:
		"""
		Returns the path that the video hash should be at
		:param sub_path: Path to submission folder that contains frames.7z and other data acquired from SauronX
		:return: pathname to video hash file
		"""
		return TaskUtils.video_file(sub_path) + '.sha256'

	@staticmethod
	def get_run(sub: str ) -> Runs:
		"""
		Fetches run associated with provided submisison lookup_hash.
		:param sub: submisison lookup_hash
		:return: Run instance with matching submission lookup_hash
		"""
		return Runs.select(Runs, Submissions).join(Submissions).where(Runs.submission.lookup_hash == sub).first()

	@staticmethod
	def update_status(status_val: str, sub_info: SubmissionInfo):
		new_record = SubmissionRecords(
			submission=Submissions.select().where(Submissions.lookup_hash == sub_info.sub_hash).first().id,
			created=sub_info.created,
			datetime_modified=datetime.datetime.now(),
			sauron=sub_info.sauron_id,
			status=status_val
		)
		new_record.save()
		logging.info('Status for Submission {} changed to {}'.format(sub_info.sub_hash, status_val))


__all__ = ['ConfigUtils', 'TaskUtils']
