import toml
from klgists.common import *
from dateutil import parser
from ..task_utils import *


class SubmissionInfo:
	"""
	SubmissionInfo holds all the information (SauronX #, datetime_created, etc.) related to the submission that are found
	in the environment.properties. This is necessary for creating insertions to the SubmissionRecords tables.
	"""
	def __init__(self, sub: str):
		self.sub_hash = sub
		self.created = self._retrieve_dt()
		self.sauron_id = self._retrieve_sauron_id()

	def _retrieve_dt(self) -> datetime:
		"""
		Retrieves datetime timestamp corresponding to datetime experiment was started.
		:return: dt_started: The timestamp of when the experiment started
		"""
		from ..task_utils import ConfigUtils
		env_path = pjoin(ConfigUtils.find_path(self.sub_hash), 'environment.properties')
		part_str = 'datetime_started='
		with open(env_path, 'rt') as env_file:
			file_lines = env_file.read().splitlines()
			dt_started = parser.parse([y.replace(part_str, '') for y in file_lines if part_str in y][0])
		return dt_started

	def _retrieve_sauron_id(self):
		"""
		Retrieves SauronX ID of the machine used for this submission from the config.toml file.
		:return:
		"""
		from ..task_utils import ConfigUtils
		with open(pjoin(ConfigUtils.find_path(self.sub_hash), 'config.toml')) as config_handle:
			data = toml.loads(config_handle.read())
			sauron_id = data['sauron']['number']
		return sauron_id


class TaskRetrieveSubInfo:

	@staticmethod
	def run(sub: str):
		return SubmissionInfo(sub)


__all__ = ['TaskRetrieveSubInfo', 'SubmissionInfo']
