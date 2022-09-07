#!/usr/bin/env python3
import os, sys, shutil, argparse
from os.path import normpath, realpath, dirname
from typing import Optional, Iterator, Callable, List

import peewee
import colorama
from colorama import Fore, Style

from valarpy.Valar import Valar
from klgists.common import *
from klgists.common.exceptions import *
from klgists.files import make_dirs, pjoin_sanitized_abs
from klgists.files.scantree import walk_until

colorama.init(autoreset=True)


class Reindexer:

	def __init__(self, valar: Valar, verbose: bool = False, overwrite: bool = False, dry: bool = False) -> None:
		self._valar = valar
		self._verbose = verbose
		self._overwrite = overwrite
		self._dry = dry

	def reindex_all(self) -> None:
		import valarpy.model as model
		n_reindexed = 0; i = 0
		for i, match in enumerate(self._query()):
			n_reindexed += 1
			self._build_symlinks(match, self._symlink_list_of(match))
		n_total = len(model.Runs)
		print(Fore.BLUE + "Reindexed {}/{} runs.".format(n_reindexed, n_total))

	def reindex(self, run_id: int) -> None:
		import valarpy.model as model
		match = self._query().where(model.Runs.id == run_id).first()
		if match is None:
			raise KeyError("No run with ID {} exists".format(run_id))
		else:
			self._build_symlinks(match, self._symlink_list_of(match))

	def _find(self, match) -> str:
		year = str(match.datetime_run.year).zfill(4)
		month = str(match.datetime_run.month).zfill(2)
		return "/shire/store/{}/{}/{}".format(year, month, match.tag)
		#return pjoin('/', 'samba', 'shire', 'store', year, month, match.tag)

	def _query(self) -> peewee.Expression:
		import valarpy.model as model
		return (
			model.Runs
			.select(model.Runs, model.Experiments, model.Superprojects, model.ProjectTypes, model.Users, model.Submissions, model.Batteries, model.TemplatePlates, model.PlateTypes, model.SauronConfigs, model.Saurons)
		 	.join(model.Experiments).join(model.Superprojects, model.JOIN.LEFT_OUTER).join(model.ProjectTypes, model.JOIN.LEFT_OUTER)
			.switch(model.Experiments).join(model.Batteries, model.JOIN.LEFT_OUTER)
			.switch(model.Experiments).join(model.TemplatePlates, model.JOIN.LEFT_OUTER).join(model.PlateTypes, model.JOIN.LEFT_OUTER)
			.switch(model.Runs).join(model.SauronConfigs, model.JOIN.LEFT_OUTER).join(model.Saurons)
		 	.switch(model.Runs).join(model.Users)
		 	.switch(model.Runs).join(model.Submissions, model.JOIN.LEFT_OUTER)
		)

	def _symlink_list_of(self, match) -> List[str]:
		import valarpy.model as model

		rid = match.id
		sid = match.submission_id
		sauronx_version = model.RunTags.select().where(model.RunTags.run_id == rid).where(model.RunTags.name == 'sauronx_version').first()
		sauronx_hash = model.RunTags.select().where(model.RunTags.run_id == rid).where(model.RunTags.name == 'sauronx_hash').first()
		fps = model.RunTags.select().where(model.RunTags.run_id == rid).where(model.RunTags.name == 'video:fps').first()
		year = str(match.datetime_run.year).zfill(4)
		month = str(year) + '-' + str(match.datetime_run.month).zfill(2)
		dt_run = match.datetime_run
		day = month + '-' + str(match.datetime_run.day).zfill(2)
		user = match.experimentalist.username
		name = match.name
		tag = match.tag
		sauron_config = match.sauron_config.id
		sauron_config_dt = str(match.sauron_config.datetime_changed).replace(' ', 'T')#.strftime("%Y-%m-%dT%H:%M:%S")
		sauron_id = match.sauron_config.sauron.id
		sauron_name = match.sauron_config.sauron.name
		battery = match.experiment.battery
		layout = match.experiment.template_plate
		plate_type = match.plate.plate_type
		plate = match.plate.id
		sub = None if match.submission is None else match.submission.lookup_hash
		experiment = match.experiment
		superproject = None if match.experiment.project is None else match.experiment.project
		generation = self._generation(sauron_id, sauron_name, dt_run, sauronx_version)
		# build up symlink list
		symlinks = []
		# gen full symlink path
		def add(*ps):
			symlinks.append(pjoin_sanitized_abs(*['runs', *ps]))
		# add symlinks up to the last bit (by-xxx/data)
		def add_by(thing_name, thing):
			t = 'by-' + str(thing_name)
			add(t, thing)
			add('users', user, t, thing)
			add('years', year, t, thing)
			add('months', month, t, thing)
			add('days', day, t, thing)
			add('plates', plate, t, thing)
			add('saurons', 'by-id', sauron_id, t, thing)
			add('saurons', 'by-name', sauron_name, t, thing)
			add('sauron-months', sauron_name, month, t, thing)
			add('user-months', user, month, t, thing)
			add('sauron-users', sauron_name, user, t, thing)
			add('configs', 'by-id', sauron_config, t, thing)
			add('configs', 'by-tag', "s{}-{}".format(sauron_id, sauron_config_dt), t, thing)
			add('experiments', 'by-id', experiment.id, t, thing)
			add('experiments', 'by-name', experiment.name, t, thing)
			add('batteries', 'by-id',  battery.id, t, thing)
			add('batteries', 'by-name',  battery.name, t, thing)
			if layout is not None:
				add('layouts', 'by-id',  layout.id, t, thing)
				add('layouts', 'by-name',  layout.name, t, thing)
			if plate_type is not None:
				add('plate-types', 'by-id',  plate_type.id, t, thing)
				add('plate-types', 'by-name',  plate_type.name, t, thing)
			if superproject is not None:
				add('projects', 'by-id', superproject.id, t, thing)
				add('projects', 'by-name', superproject.name, t, thing)
			if sauronx_version is not None:
				add('info', 'sauronx-versions', sauronx_version.value, t, thing)
			if sauronx_hash is not None:
				add('info', 'sauronx-hashes', sauronx_hash.value, t, thing)
			if fps is not None and sub is not None:
				add('info', 'sauronx-framerates', fps.value, t, thing)
			if generation is not None:
				add('generations', generation, t, thing)
		# and finally do this for each of the by-xxx:
		add_by('rid', rid)
		if sid is not None: add_by('sid', sid)
		if name is not None: add_by('name', name)
		if sub is not None: add_by('hash', sub)
		if tag is not None: add_by('tag', tag)
		return symlinks

	def _generation(self, sauron_id, sauron_name, dt_run, sauronx_version):
		if sauron_name == 'MGH':
			return '1:mgh'
		elif sauron_name in {'1', '2', '3'} and sauronx_version is None:
			return '2:ucsf-legacy'
		elif sauron_name in {'1', '2', '3'} and sauronx_version is not None:
			return '3:sauronx-alliedvision'
		elif dt_run < datetime(2019, 2, 26):
			return '4:sauronx-pointgrey-alpha'
		elif sauron_id > 10:

			return '5:sauronx-pointgrey'

	def _write_symlink(self, target, link: str) -> None:
		if self._verbose: print("Symlinking {} → {}".format(target, link))
		if not self._dry:
			make_dirs(dirname(link))
			os.symlink(target, link)

	def _build_symlink(self, target, link: str) -> None:
		real_target = realpath(link) if pexists(link) else None
		if not pexists(link):
			self._write_symlink(target, link)
		elif normpath(target) != normpath(real_target):
			if not self._overwrite or self._verbose:
				print(Fore.YELLOW + "link {} already points to {}, not {}".format(link, real_target, target))
			if self._overwrite:
				self._write_symlink(target, link)

	def _build_symlinks(self, match, symlinks: List[str]) -> None:
		target = self._find(match)
		if not pexists(target):
			#print(Fore.RED + "{} not found".format(match.tag))
			return
		for link in symlinks:
			if not os.path.lexists(link):
				self._build_symlink(target, link)


if __name__ == '__main__':
	parser = argparse.ArgumentParser("Rebuilds plate_run symlinks.")
	parser.add_argument("--verbose", action='store_true')
	parser.add_argument("--dry", action='store_true')
	parser.add_argument("--overwrite", action='store_true')
	args = parser.parse_args()
	with Valar() as valar:
		Reindexer(valar, args.verbose, args.overwrite, args.dry).reindex_all()


__all__ = ['Reindexer']
