#!/usr/bin/env python3
import os, sys, shutil, argparse
from os.path import normpath, realpath, dirname
from typing import Optional, Iterator, Callable, List, Union

import peewee
import colorama
from colorama import Fore, Style

from valarpy.Valar import Valar
from klgists.common import *
from klgists.common.exceptions import *
from klgists.files import make_dirs, pjoin_sanitized_abs
from klgists.files.wrap_cmd_call import wrap_cmd_call
from klgists.common.timestamp import timestamp

colorama.init(autoreset=True)


class Reimporter:
	_valar = None  # type: Valar
	_verbose = None  # type: bool
	_overwrite = None  # type: bool
	_empty_plate = None  # type: bool
	_dry = None  # type: bool

	def __init__(self, valar: Valar, verbose: bool = False, empty_plate: bool = False, dry: bool = False) -> None:
	        self._valar = valar
	        self._verbose = verbose
	        self._empty_plate = empty_plate
	        self._dry = dry


	def reimport(self, sub_hash: Union[str, int], new: Optional[str]) -> None:
		import valarpy.model as model
		match = model.Submissions.select().where(model.Submissions.lookup_hash == sub_hash).first()
		if match is None:
			raise KeyError("No submission {} exists".format(sub_hash))
		else:
			self._reimport_sauronx(match, new)


	def _reimport_sauronx(self, match, new: Optional[str]):

		print("Operating in {} mode".format('dry' if self._dry else 'REAL'))

		import valarpy.model as model

		sub_hash = match.lookup_hash
		path = self._find(match)

		run = model.Runs.select().where(model.Runs.submission_id == match.id).first()
		plate = model.Plates.select().where(model.Plates.id == run.plate_id).first() if run is not None else None
		other_runs_on_plate = list(model.Runs.select().where(model.Runs.plate_id == plate.id).where(model.Runs.id != run.id)) if run is not None else None

		if path is not None:
			assert pdir(path), "Path {} must exist iff run exists".format(path)
		print("Running on {} for {}".format(path, sub_hash))

		if run is not None:
			print("Deleting run {}".format(run.id))
			if not self._dry: run.delete_instance()
			if len(other_runs_on_plate) > 0:
				print("Other runs are tied to plate {}: {}".format(plate.id, [r.id for r in other_runs_on_plate]))
			if len(other_runs_on_plate) == 0 or self._empty_plate:
				print("Deleting plate {}".format(plate.id))
				if not self._dry: plate.delete_instance()
		else:
			print("No runs are associated")
			

		if new is not None:
			new_sub = model.Submissions.select().where(model.Submissions.lookup_hash == new).first()
			assert new_sub is not None, "Replacement submission {} does not exist".format(new)
			garbage_hash = 'see:' + new_sub.id_hash_hex[4:]
			match.id_hash_hex = garbage_hash
			print("Changed {} to {}".format(sub_hash, garbage_hash))
			new_sub.id_hash_hex = sub_hash
			if not self._dry:
				match.save()
				new_sub.save()

		if not self._dry:
			shutil.copytree(path, "/data/uploads/{}".format(sub_hash))
			shutil.move(path, "/data/prunable/")
			wrap_cmd_call(['/data/repos/valar/scripts/tap', sub_hash])


	def _find(self, match) -> Optional[str]:
		import valarpy.model as model
		run = model.Runs.select().where(model.Runs.submission_id == match.id).first()
		if run is None: return None
		year = str(run.datetime_run.year).zfill(4)
		month = str(run.datetime_run.month).zfill(2)
		#if match is None:
		#	return '/alpha/legacy/{}/{}/{}'.format(year, month, run.id)
		#else:
		return '/alpha/plates/{}/{}/{}'.format(year, month, run.id)


if __name__ == '__main__':
	parser = argparse.ArgumentParser("Reimports, possibly replacing something.")
	parser.add_argument("--verbose", action='store_true')
	parser.add_argument("--new", type=str, help='Replace with new submission')
	parser.add_argument("--empty-plate", action='store_true')
	parser.add_argument("--dry", action='store_true')
	parser.add_argument("run", type=str)
	args = parser.parse_args()
	with Valar() as valar:
			Reimporter(valar, args.verbose, args.empty_plate, args.dry).reimport(args.run, args.new)

