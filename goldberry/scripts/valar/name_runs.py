"""
Idempotent changes to Valar.
Some may require non-default user privileges.
"""

import argparse
from typing import Iterator, Union

from valarpy.Valar import Valar


class RunNamer:

	_valar = None  # type: Valar
	_verbose = None  # type: bool
	_overwrite = None  # type: bool
	_dry = None  # type: bool
	_initials = None  # type: dict

	def __init__(self, valar: Valar, verbose: bool, overwrite: bool, dry: bool) -> None:
		self._valar = valar
		self._verbose = verbose
		self._overwrite = overwrite
		self._dry = dry
		import valarpy.model as model
		self._initials = {
			user.id: self._gen_initials(user)
			for user in model.Users
		}

	def run_tag(self, run) -> str:
	    return run.datetime_run.strftime("%Y%m%d.%H%M%S") + '.S' + str(run.sauron_config.sauron.id)

	def run_name(self, run) -> str:
		import valarpy.model as model
		priors = model.Runs.select(model.Runs) \
				.where(model.Runs.plate_id == run.plate_id) \
				.where(model.Runs.datetime_run < run.datetime_run).count() + 1

		return \
			run.datetime_run.strftime("%Y-%m-%d") \
			+ "-" + "r" + str(run.id) \
			+ "u" + self._initials[run.experimentalist_id] \
			+ "-" + "S" + str(run.sauron_config.sauron_id).zfill(2) \
			+ "-" + str(priors) \
			+ "-" + run.datetime_run.strftime("%H%M")

	def generate_run_names(self):
		"""Returns an iterator over runs where the name is set or reset.
		Does not save these to Valar, and only changes nonnull names.
		This is idempotent as long as no one's changed a name manually, which should never happen.
		Usage:
		for run in generate_names():
			run.save()
		"""
		import valarpy.model as model
		query = model.Runs.select(model.Runs, model.SauronConfigs).join(model.SauronConfigs).join(model.Saurons)#.where(model.Runs.submission != None)
		if not self._overwrite: query = query.where(model.Runs.name == None)#.where(model.Runs.name == None)
		for run in query:
			run.name = self.run_name(run)
			#if run.submission is not None:
				#run.tag = self.run_tag(run)
			yield run

	def update_run_names(self) -> None:
		for run in self.generate_run_names():
			if not self._dry: run.save()
			if self._verbose: print("Named {}: tag={}, name={}".format(run.id, run.tag, run.name))


	def _gen_initials(self, user) -> str:
		import valarpy.model as model
		if isinstance(user, int): user = model.Users.select(model.Users.id == user).first()
		if isinstance(user, str): user = model.Users.select(model.Users.username == user).first()
		s = ''
		use = True
		for i, c in enumerate(user.first_name + ' ' + user.last_name):
			if use and c == c.upper() and c != c.lower(): s += c
			use = c == c.upper()
		return s


__all__ = ['RunNamer']


if __name__ == '__main__':
	parser = argparse.ArgumentParser("Sets runs.name.")
	parser.add_argument("--verbose", action='store_true')
	parser.add_argument("--dry", action='store_true')
	parser.add_argument("--overwrite", action='store_true')
	args = parser.parse_args()
	with Valar() as valar:
		RunNamer(valar, args.verbose, args.overwrite, args.dry).update_run_names()

