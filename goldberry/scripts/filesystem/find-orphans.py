#!/usr/bin/env python3
import os, sys, glob, argparse
from typing import Optional, Iterator, Callable, List

import colorama
from colorama import Fore, Style

from valarpy.Valar import Valar
from klgists.common import *
from klgists.common.exceptions import *
from klgists.files import make_dirs
from klgists.common.timestamp import timestamp
from klgists.files.find_only_file_matching import find_only_file_matching
from klgists.files.scantree import walk_until, walk_until_level

colorama.init(autoreset=True)


class OrphanFinder:

	follow = None
	verbose = None

	def __init__(self, follow: bool, verbose: bool) -> None:
		self.follow = follow
		self.verbose = verbose


	def walk(self, path: str) -> Iterator[str]:
		# TODO get all dirs under /alpha/plates/ with depth=3
		for root, dirs, files in walk_until_level(path, 3):
			depth = root[len(path) + len(os.path.sep):].count(os.path.sep)
			if depth == 2:
				yield root

	def search(self, root: str):
		with Valar():
			import valarpy.model as model
			print("Connected to Valar. Found {} plate runs.".format(len(model.PlateRuns.select())))
			print("Listing orphans under {}".format(root))
			for path in self.walk(root):
				run = os.path.basename(path)
				if not run.isdigit():
					if self.verbose: print(('-' * 80))
					print(Fore.MAGENTA + '[invalid] ' + path)
					if self.verbose: print(('-' * 80) + '\n')
					continue
				match = model.PlateRuns.select().where(model.PlateRuns.id == int(run)).first()
				if match is None:
					if self.verbose: print(('-' * 80))
					sub_hash_file = pjoin(path, 'submission_hash.txt')
					if not pexists(sub_hash_file):
						print(Fore.MAGENTA + "[invalid] {} does not exist!".format(sub_hash_file))
					else:
						with open(sub_hash_file) as f:
							sub_hash = f.read().strip()
						print(Fore.RED + '[orphan]  ' + sub_hash + ' /// '  + path)
						if self.verbose:
							with open(pjoin(path, 'environment.properties')) as f:
								print(f.read())
					if self.verbose: print(('-' * 80) + '\n')


if __name__ == '__main__':
	parser = argparse.ArgumentParser("Scans for directories ")
	parser.add_argument("--follow", action='store_true', help="Follow symlinks.")
	parser.add_argument("--verbose", action='store_true', help="Output full environment info")
	args = parser.parse_args()
	finder = OrphanFinder(args.follow, args.verbose)
	finder.search('/alpha/plates')

