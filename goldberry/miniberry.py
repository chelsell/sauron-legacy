import os, sys, json, shutil, argparse
import traceback
import socket
import logging
import ssl
from os.path import normpath, realpath, dirname
from datetime import datetime
from contextlib import contextmanager
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, Future
import functools
from multiprocessing import Queue, Process, Pool, JoinableQueue
from datetime import datetime, timedelta
from typing import Set, Optional
import re
import argparse
import socketserver
from typing import Optional, Iterator, Callable, List, Union
from enum import Enum
from websocket import WebSocketConnectionClosedException

import peewee
import colorama
import hashlib
import slackclient
from slackclient import SlackClient
import toml
from colorama import Fore, Style

from valarpy.Valar import Valar
from klgists.common import *
from klgists.common.exceptions import *
from klgists.common.flexible_logger import FlexibleLogger
from klgists.files import make_dirs, pjoin_sanitized_abs
from klgists.files.wrap_cmd_call import wrap_cmd_call
from klgists.files.file_hasher import FileHasher

from valarpy.Valar import Valar
from valarpy.global_connection import db as global_db
colorama.init(autoreset=True)


valar_obj = Valar()
valar_obj.open()
from valarpy.model import *
hasher = FileHasher(hashlib.sha256, '.sha256')

class SlackConnectionError(Exception): pass

class UserError(Exception): pass
class UnexpectedUserError(UserError): pass
class VideoCreationError(UnexpectedUserError): pass
class InsertionError(UnexpectedUserError): pass
class FeatureCalculationError(UnexpectedUserError): pass
class FeaturesNotCalculatedError(UnexpectedUserError): pass
class UploadFailedError(UnexpectedUserError): pass
class FileAlreadyExistsError(UnexpectedUserError): pass
class FileDoesNotExistError(UnexpectedUserError): pass

class ExpectedUserError(UserError): pass
class AlreadyInQueueError(ExpectedUserError): pass
class NoSuchSubmissionError(ExpectedUserError): pass
class NoSuchRunError(ExpectedUserError): pass
class NoSuchUploadError(ExpectedUserError): pass
class RunAlreadyExistsError(ExpectedUserError): pass


class GoldberryPaths:

        _uploads_root = pjoin('/', 'alpha', 'uploads')
        _store_root = pjoin('/', 'samba', 'shire', 'store')
        _trash_root = pjoin('/', 'trash', 'goldberry-tmp-data')
        _log_root = pjoin('/', 'var', 'log', 'goldberry')
        _repo_root = pjoin('/', 'data', 'repos')

        def upload_path(self, lookup_hash: str) -> str:
                return pjoin(GoldberryPaths._uploads_root, lookup_hash)

        def pending_subs(self) -> List[str]:
                return [s for s in os.listdir(GoldberryPaths._uploads_root) if len(s) == 12]

        """
        def _was_attempted(self, sub):
                return os.path.exists(os.path.join(self.upload_path(sub), '.attempted-insert'))

        def _was_failed(self, sub):
                return os.path.exists(os.path.join(self.upload_path(sub), '.failed-insert'))

        def _has_video(self, sub):
                return os.path.exists(self.video_file(self.upload_path(sub) + '.sha256'))

        def _was_succeeded(self, sub):
                return os.path.exists(os.path.join(self.upload_path(sub), '.succeeded-insert'))
        """

        def crf(self) -> int:
                return 15

        def video_file(self, sub_path: str) -> str:
                return pjoin(sub_path, 'camera', 'x265-crf' + str(self.crf()), 'x265-crf{}.mkv'.format(self.crf()))

        def log_path(self, lookup_hash: str) -> str:
                return pjoin(GoldberryPaths._log_root, 'insertion', lookup_hash + '.log')

        def valar_repo_path(self) -> str:
                return pjoin(GoldberryPaths._repo_root, 'valar')
        def goldberry_repo_path(self) -> str:
                return pjoin(GoldberryPaths._repo_root, 'goldberry')
        def lorien_repo_path(self) -> str:
                return pjoin(GoldberryPaths._repo_root, 'lorien')

        def goldberry_root_log_path(self) -> str:
                return pjoin(GoldberryPaths._log_root, 'goldberry.log')

        def submission_log_path(self, lookup_hash: str) -> str:
                return pjoin(GoldberryPaths._log_root, lookup_hash)

        def run_from_sub(self, sub: str) -> int:
                import valarpy.model as model
                run = model.Runs.select(model.Runs, model.Submissions).join(model.Submissions).where(Submissions.lookup_hash == sub).first()
                assert run is not None, "Run for submission {} does not exist".format(sub)
                return run

        def link_path(self, sub: str) -> str:
                f = '/runs/by-hash/{}/'.format(sub)
                return f if pexists(f) else None

        def store_path(self, sub: str) -> str:
                return self.storage_path_from_sub(sub)

        def storage_path_from_sub(self, sub: str) -> str:
                import valarpy.model as model
                run = model.Runs.select(model.Runs, model.Submissions).join(model.Submissions).where(Submissions.lookup_hash == sub).first()
                if run is None: return None  #raise ValueError("Run not found for sub {}".format(sub))
                #assert run is not None, "Run for submission {} does not exist".format(sub)
                return GoldberryPaths.storage_path_from_run(run)

        def storage_path_from_run(run) -> str:
                year = str(run.datetime_run.year).zfill(4)
                month = str(run.datetime_run.month).zfill(2)
                return pjoin(GoldberryPaths._store_root, year, month, str(run.tag))


PATHS = GoldberryPaths()
import time

def _log_global(sub: str, message: str, level: str):
        color = {'global': Fore.CYAN, 'error': Fore.RED, 'warn': Fore.YELLOW, 'success': Fore.GREEN, 'info': Fore.BLUE, 'debug': ''}[level]
        message = "{}[{}{}{} @ {} : {}] >>> {}".format(color, color + Style.BRIGHT, sub, Style.NORMAL + color, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), level.upper(), message)
        print(color + message)


class GoldberryProcessor:
        def __init__(self, sub: str, dry: bool = False, force: bool = False):
                self._dry = dry
                self.sub = sub
                self.sub_obj = Submissions.fetch(sub)
                self.run = None
                if self.sub_obj is None:
                        raise NoSuchSubmissionError("{} does not exist.".format(sub))
                self.force = force
                self.run = self._get_run()

        def _get_run(self):
                if self.run is None:
                        self.run = Runs.select().where(Runs.submission_id == self.sub_obj.id).first()
                return self.run

        def insert(self):
                path = self.find()
                sub = self.sub
                _log_global(sub, "Importing new submission at path {}".format(path), 'info')
                self._check(path)
                try:
                        self.make_video(path)
                except ExternalCommandFailed as e: raise e
                except Exception as e:
                        raise VideoCreationError("Failed to create the video:\n{}".format(str(e))) from e
                try:
                        self._call_insert(path)
                except ExternalCommandFailed as e: raise e
                except Exception as e:
                        raise InsertionError("Failed to insert into Valar:\n{}".format(str(e))) from e
                try:
                        self._annotate(path)
                        if path == PATHS.upload_path(sub):
                                self.archive()
                except ExternalCommandFailed as e:
                        raise UploadFailedError("Failed to move {}:\n{}".format(sub, e.extended_message())) from e
                except Exception as e:
                        raise UploadFailedError("Failed to archive after inserting into Valar:\n{}".format(str(e))) from e

        def _check(self, path):
                sub = self.sub
                run = self._get_run()
                if not self.force and run is not None:
                        raise RunAlreadyExistsError("Run {} is already attached to submission {} at path {}. Refusing to re-import. Use 'reimport' to override.".format(run.tag, sub, path))
                if not self.force and PATHS.store_path(self.sub) is not None and self.find() == PATHS.store_path(self.sub):
                        raise RunAlreadyExistsError("Run {} is not attached to a run but is stored! Refusing to re-import. Use 'reimport' to override.".format(run.tag, sub, path))

        def _call_insert(self, path):
                sub = self.sub; sub_obj = self.sub_obj
                #print("sub obj: {}".format(sub))
                if not self._dry: wrap_cmd_call(['sbt', 'project importer', 'runMain kokellab.valar.importer.DirectoryLoader "{}"'.format(path)], cwd=PATHS.valar_repo_path())
                run = self._get_run()
                if run is None:
                        raise NoSuchRunError("No run for submission {}".format(self.sub))
                lobby_run = Runs.select(Runs, Submissions).join(Submissions).where(Submissions.lookup_hash=='see:' + sub[4:]).where(Submissions.experiment_id == 1410).first()
                #print("run: {}".format(run))
                if lobby_run is None:
                        sauron = Saurons.select(Runs, SauronConfigs, Saurons).join(SauronConfigs).join(Runs).where(Runs.id == run).first()
                        if sauron.id in {4, 7} or sauron.id >= 10:
                                self._insert_feature(path, 'cd(10)')
                        else:
                                self._insert_feature(path, 'MI')
                else:
                        print("Found match in lobby r{} / {}".format(lobby_run.id, lobby_run.submission.lookup_hash))
                        wells = {w.well_index: w.id for w in Wells.select().where(Wells.run_id == run.id)}
                        # TODO in-place update
                        for wf in WellFeatures.select(WellFeatures.id, WellFeatures.feature_id, Wells, Runs).join(Wells).join(Runs).where(Runs.id == lobby_run.id).where(WellFeatures.feature_id == 1):
                                wf.well_id = wells[wf.well.well_index]
                                if not self._dry: wf.save()

        def find(self) -> str:
                if pexists(PATHS.upload_path(self.sub)):
                        return PATHS.upload_path(self.sub)
                elif self._get_run() is not None and pexists(PATHS.storage_path_from_sub(self.sub)):
                        return PATHS.storage_path_from_sub(self.sub)
                elif self._get_run() is None and PATHS.link_path(self.sub):
                        return PATHS.link_path(self.sub)
                else:
                        raise FileDoesNotExistError("Submission {} was not found under uploads or store".format(self.sub))
        
        def calculate(self, feature):
                self._insert_feature(self.find(), feature)

        def _insert_feature(self, path, feature):
                sub = self.sub
                run = self._get_run()
                if run is None:
                        raise NoSuchRunError("No run for submission {}".format(self.sub))
                _log_global(sub, "Calculating {}".format(feature), 'debug')
                try:
                        if not self._dry: wrap_cmd_call(['sbt', 'project simple', '-mem', '4096', 'runMain kokellab.lorien.simple.FeatureProcessor {} {} "{}"'.format(feature, run, PATHS.video_file(path))], cwd=PATHS.lorien_repo_path())
                except ExternalCommandFailed as e:
                        raise FeatureCalculationError("Failed to calculate {} on {}:\n{}".format(feature, path, e.extended_message())) from e
                _log_global(sub, "Finished calculating {}".format(feature), 'debug')

        def archive(self, force: bool = False):
                if self._get_run() is None:
                        raise NoSuchRunError("No run for submission {}".format(self.sub))
                sub = self.sub
                run = self._get_run()
                n_features = WellFeatures.select(WellFeatures.well_id, Wells.id, Wells.run_id).join(Wells).where(Wells.run == run).count()
                if n_features < 96: raise FeaturesNotCalculatedError("Can't archive: no features")
                upload_path = PATHS.upload_path(self.sub)
                store_path = PATHS.storage_path_from_sub(sub)
                assert upload_path is not None, "Storage path not found"
                assert store_path is not None, "Storage path not found"
                self._move(upload_path, store_path, force)

        def unarchive(self, force: bool = False):
                #if self._get_run() is None:
                #       raise NoSuchRunError("No run for submission {}".format(sub))
                sub = self.sub
                upload_path = PATHS.upload_path(sub)
                store_path = PATHS.storage_path_from_sub(sub)
                assert store_path is not None, "Storage path not found"
                self._move(store_path, upload_path, force)

        def _move(self, from_path, to_path, force: bool = False):
                sub = self.sub
                run = Runs.select(Runs, Submissions).join(Submissions).where(Submissions.lookup_hash == sub).first()
                from_path = from_path + '/'
                print("Copying {} to {}".format(from_path, to_path))
                if pexists(to_path) and not force:
                        #assert pexists(pjoin(store_path, 'frames.7z')), 'no frames'
                        #if not self._dry: wrap_cmd_call(['find', path, '-type', 'd', '-empty', '-delete'])
                        #shutil.move(path, "/media/temp_drive/trash/{}".format(sub))
                        raise FileAlreadyExistsError("Dir {} already exists".format(to_path))
                elif pexists(to_path) and force:
                        print(Fore.RED + "Dir {} already exists".format(to_path))
                make_dirs(os.path.dirname(to_path))
                if not self._dry: wrap_cmd_call(['rsync', '-avz', '--ignore-existing', '--remove-source-files', from_path, to_path])
                if not pexists(to_path):
                        raise FileDoesNotExistError('Failed to copy to {}'.format(to_path))
                #if not self._dry: wrap_cmd_call(['find', path, '-type', 'd', '-empty', '-delete'])
                assert from_path.startswith('/alpha/uploads'), "Refusing to delete path {}".format(from_path)   # TODO remove
                print(Fore.CYAN + "DELETING {}".format(from_path))
                updir = from_path + "../"
                if not self._dry: wrap_cmd_call(['find', updir, '-type', 'd', '-empty', '-delete'])

        def _annotate(self, path):
                run = Runs.select(Runs, Submissions).join(Submissions).where(Submissions.lookup_hash == self.sub).first()
                with open(pjoin(path, '.id'), 'w') as f:
                        self._write_ids(run, f)
                with open(pjoin(path, 'camera', '.id'), 'w') as f:
                        self._write_ids(run, f)
                with open(pjoin(path, '.history'), 'a') as f:
                        f.write('================ {} ================\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                        self._write_ids(run, f)
                        f.write(((16+2+19+2+16)*'=') + '\n')

        def _write_ids(self, run, f):
                f.write('submissions.lookup_hash={}\n'.format(run.submission.lookup_hash))
                f.write('runs.id={}\n'.format(run.id))
                f.write('runs.tag={}\n'.format(run.tag))
                f.write('runs.name={}\n'.format(run.name))

        def make_video(self, path) -> None:
                sub = self.sub
                v_path = PATHS.video_file(path)
                sz_path = pjoin(path, 'frames.7z')
                if pexists(v_path) or not pexists(sz_path): return
                yz_path = pjoin(path, 'frames.7z')
                tmp_frames_path = pjoin(path, "tmpframes")
                if not self._dry:
                        _log_global(sub, "Extracting frames to {}".format(yz_path), 'debug')
                        wrap_cmd_call(['7za', 'x', sz_path, "-o{}".format(tmp_frames_path), '-aos'])
                if pexists(tmp_frames_path) and not self._dry:
                        _log_global(sub, "Making video at {}".format(v_path), 'debug')
                        make_dirs(os.path.dirname(v_path))
                        wrap_cmd_call([
                                        'ffmpeg',
                                        '-pattern_type', 'glob',
                                        '-i', "{}/**/*.jpg".format(tmp_frames_path),
                                        '-safe', '0',
                                        '-vf', "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                                        '-c:v', 'libx265',
                                        '-crf', str(PATHS.crf()),
                                        '-pix_fmt', 'yuv420p',
                                        '-y', v_path
                        ])
                        hasher.add_hash(v_path)
                        shutil.rmtree(tmp_frames_path)


        def _datetime_started(self, path) -> datetime:
                with open(pjoin(path, 'environment.properties')) as f:
                        for line in f:
                                if line.startswith('datetime_started'):
                                        return datetime.strptime(line.split('=')[1], '%Y-%m-%dT%H:%M:%S.%f')



class GoldberryQueue:
        def __init__(self, max_workers: int, notify_callback: Callable[[str, Optional[Exception]], None]):
                self.pending = []
                self.running = []
                self.max_workers = max_workers
                self.executor = ThreadPoolExecutor(max_workers=max_workers)
                self.notify_callback = notify_callback
                print(Fore.GREEN + "Started queue. Found {} pending submissions.".format(len(PATHS.pending_subs())))

        def insert(self, sub):
                self._submit(sub, (GoldberryProcessor(sub, force=False).insert, ))

        def archive(self, sub, force: bool = False):
                self._submit(sub, (GoldberryProcessor(sub).archive, force))

        def unarchive(self, sub, force: bool = False):
                self._submit(sub, (GoldberryProcessor(sub).unarchive, force))

        def calculate(self, sub, feature):
                self._submit(sub, (GoldberryProcessor(sub).calculate, feature))

        def delete(self, sub, feature):
                self._submit(sub, (GoldberryProcessor(sub).delete,))

        def reinsert(self, sub):
                path = PATHS.store_path(sub)
                self._submit(sub, (GoldberryProcessor(sub, force=True).insert, ))

        def _submit(self, sub, task):
                if sub in self: raise AlreadyInQueueError("Can't add {}: already pending or in queue".format(sub))
                self.pending.append((sub, task))
                self.maybe_run_next()

        def maybe_run_next(self):
                if len(self.pending) == 0: return
                if len(self.running) > self.max_workers: return
                sub, task = self.pending.pop()
                _log_global(sub, 'Popped from queue', 'debug')
                future = self.executor.submit(*task)
                future.add_done_callback(functools.partial(self.finished, sub))
                self.running.append(sub)

        def finished(self, arg, fn: Future):
                if not fn.cancelled() and not fn.done(): return
                if fn.cancelled():
                        self.notify_callback(arg, ValueError("Cancelled"))
                        _log_global(arg, 'Canceled', 'warn')
                elif fn.done():
                        if fn.exception():
                                self.notify_callback(arg, fn.exception())
                                print('-'*60)
                                _log_global(arg, 'Caught exception. Stack trace below:', 'warn')
                                e = fn.exception()
                                print(str(traceback.format_exception(None, e, e.__traceback__)).replace('\\n', '\n'))
                                #print('{}: error returned: {}'.format(arg, fn.exception()))
                                #print(traceback.format_exc())
                                print('-'*60)
                                print('')
                        else:
                                self.notify_callback(arg, None)
                                _log_global(arg, 'Finished', 'info')
                self.running = [r for r in self.running if r != arg]
                self.maybe_run_next()  # TODO

        def __len__(self):
                return len(self.pending) + len(self.running)

        def __contains__(self, sub):
                return sub in [x for x,y in self.pending] or sub in self.running


class ResponseType(Enum):
        SUCCESS = 1
        WARNING = 2
        REFUSAL = 3
        CLIENT_ERROR = 4
        SERVER_ERROR = 5


class Response:
        def __init__(self, rtype: ResponseType, message: str):
                self.rtype = rtype
                self.message = message
        def __repr__(self):
                return self.rtype.name.lower() + ": " + self.message
        def __str__(self): return repr(self)


class Goldberry:
        def __init__(self, max_workers: int, notify_callback: Callable[[str, Optional[Exception]], None]):
                self.queue = GoldberryQueue(max_workers, notify_callback)

        def reinsert(self, sub) -> Response:
                run = Runs.select(Runs, Submissions).join(Submissions).where(Submissions.lookup_hash == sub).first()
                if run is None:
                        return self._respond(ResponseType.CLIENT_ERROR, "{} is not attached to a run.".format(sub))
                self.queue.reinsert(sub)
                return self._respond(ResponseType.SUCCESS, 'Added. There are {} items running and {} queued.'.format(len(self.queue.running), len(self.queue.pending)))

        def insert(self, sub: str, force: bool) -> Response:
                run = Runs.select(Runs, Submissions).join(Submissions).where(Submissions.lookup_hash == sub).first()
                if run is not None and not force:
                        return self._respond(ResponseType.REFUSAL, "{} is already attached to run {}.".format(sub, run.name))
                if len(sub) != 12:
                        return self._respond(ResponseType.CLIENT_ERROR, 'That is not a valid submission lookup hash.')
                if sub in self.queue.pending:
                        return self._respond(ResponseType.DUPLICATE, 'That submission is already queued.')
                if sub in self.queue.running:
                        return self._respond(ResponseType.DUPLICATE, 'That submission is currently being inserted.')
                if not pexists(PATHS.upload_path(sub)) and (run is None or not pexists(PATHS.store_path(sub))) and not PATHS.link_path(sub):
                        return self._respond(ResponseType.CLIENT_ERROR, 'That submission was not found in uploads or storage path.')
                self.queue.insert(sub)
                return self._respond(ResponseType.SUCCESS, 'Added. There are {} items running and {} queued.'.format(len(self.queue.running), len(self.queue.pending)))

        def insert_all(self):
                n = 0
                for s in [str(q) for q in PATHS.pending_subs()]:
                        if s not in self.queue:
                                try:
                                        self.insert(s, False)
                                except UserError: pass  # already added
                                n += 1
                return self._respond(ResponseType.SUCCESS, 'Added {}. There are {} tasks running and {} queued.'.format(n, len(self.queue.running), len(self.queue)))

        def insert_mine(self, username):
                return self._respond(ResponseType.SUCCESS, 'You are {}'.format(username))

        def insert_from(self, rest):
                n = 0
                for s in [str(q) for q in PATHS.pending_subs()]:
                        if s not in self.queue:
                                sub = Submissions.select(Submissions, Users).join(Users, on=Submissions.user_id == Users.id).where(Submissions.lookup_hash == s).first()
                                u = sub.user.username
                                if u != rest: continue
                                try:
                                        self.insert(s, False)
                                except UserError: pass  # already added
                                n += 1
                return self._respond(ResponseType.SUCCESS, 'Added {}. There are {} tasks running and {} queued.'.format(n, len(self.queue.running), len(self.queue)))

        def archive_all(self):
                n = 0
                for s in [str(q) for q in PATHS.pending_subs()]:
                        if s not in self.queue:
                                self.archive(s)
                                n += 1
                return self._respond(ResponseType.SUCCESS, 'Added {} items to archive. There are {} tasks running and {} queued.'.format(n, len(self.queue.running), len(self.queue)))

        def archive(self, sub, force: bool = False):
                run = Runs.select(Runs, Submissions).join(Submissions).where(Submissions.lookup_hash == sub).first()
                if run is None:
                        return self._respond(ResponseType.REFUSAL, "{} has not been inserted.".format(sub))
                if sub not in PATHS.pending_subs():
                        return self._respond(ResponseType.CLIENT_ERROR, "{} is not in the uploads directory.".format(sub))
                # TODO confirm that features were calculated
                if len(self.features_on(run)) == 0:
                        return self._respond(ResponseType.REFUSAL, "{} has no features calculated yet")
                self.queue.archive(sub, force=force)
                return self._respond(ResponseType.SUCCESS, "I’ll archive {}.".format(sub)) 

        def features_on(self, run) -> Set[str]:
                return {
                        wf.type.name
                        for wf in WellFeatures.select(WellFeatures.type, WellFeatures.well, WellFeatures.id, Features.id, Features.name, Wells.id, Wells.run, Runs.id)
                                        .join(Wells).join(Runs).switch(WellFeatures).join(Features)
                                        .where(Runs.id == run.id)
                }

        def calculate(self, feature, sub):
                run = Runs.select(Runs, Submissions).join(Submissions).where(Submissions.lookup_hash == sub).first()
                if run is None:
                        return self._respond(ResponseType.REFUSAL, "{} has not been inserted.".format(sub))
                self.queue.calculate(sub, feature)
                return self._respond(ResponseType.SUCCESS, "Will calculate {} on {}".format(feature, sub))
                #return self._respond(ResponseType.REFUSAL, "I’m sorry, Dave. I’m afraid I can’t do that.".format(sub)) 

        def replace(self, prev_hash, new_hash):
                prev_sub = Submissions.select().where(Submissions.lookup_hash == prev_hash).first()
                print(prev_hash)
                if prev_sub is None:
                        return self._respond(ResponseType.CLIENT_ERROR, "{} does not exist".format(prev_hash))
                new_sub = Submissions.select().where(Submissions.lookup_hash == new_hash).first()
                print(new_hash)
                if new_sub is None:
                        return self._respond(ResponseType.CLIENT_ERROR, "{} does not exist".format(new_hash))
                run = Runs.select().where(Runs.submission_id == prev_sub.id).first()
                continuing_subs = list(Submissions.select().where(Submissions.continuing_id == prev_sub.id))
                garbage_hash = 'see:' + new_sub.lookup_hash[4:]
                prev_sub.lookup_hash = garbage_hash
                print("Changed {} to {}".format(prev_hash, garbage_hash))
                new_sub.lookup_hash = prev_hash
                prev_sub.save()
                new_sub.save()
                if run is not None:
                        #run.submission_id = prev_sub.id  # keep it
                        run.experiment_id = 1410  # Goldberry lobby
                        run.save()
                        #print("Moved run {} to submission {} ({})".format(run.tag, new_sub.id, prev_hash))
                if len(continuing_subs) > 0:
                        for con in continuing_subs:
                                con.continuing_id = new_sub.id
                                con.save()
                        print("Updated 'continuing' submissions {} with submission {}".format(', '.join([c.id for c in continuing_subs]), new_sub.id))
                return self._respond(ResponseType.SUCCESS, "Renamed {}→{} and {}→{}.".format(new_hash, prev_hash, prev_hash, garbage_hash)) 

        def show_hide(name, table, col, val):
                obj = table.select().where(table.name == name).first()
                if obj is None:
                        return self._respond(ResponseType.CLIENT_ERROR, "{} {} does not exist.".format(table, name))
                if getattr(obj, col) == val:
                        return self._respond(ResponseType.SUCCESS, "No update needed for {}.".format(table, name))
                setattr(obj, col, val)
                obj.save()
                return self._respond(ResponseType.SUCCESS, "Updated {}.".format(table, name))

        def about(self, sub):
                r = self._only(sub)
                isin = sub in PATHS.pending_subs() 
                if r is None and isin:
                        return self._respond(ResponseType.SUCCESS, "{} is waiting in uploads".format(sub)) 
                elif r is None and not isin:
                        return self._respond(ResponseType.SUCCESS, "{} is not inserted and not in uploads".format(sub)) 
                elif r is not None and isin:
                        return self._respond(ResponseType.SUCCESS, "{} is associated with run r{} but has not been archived".format(sub, r.id)) 
                elif r is not None and not isin:
                        return self._respond(ResponseType.SUCCESS, "{} is associated with run r{} and has been archived".format(sub, r.id)) 

        def pause(self, sub):
                r = self._only(sub)
                if r is not None: return r
                self.queue.pending = [s for s in self.queue.pending if s != sub]
                return self._respond(ResponseType.SUCCESS, "I removed {} from the queue.".format(sub)) 

        def clear(self):
                n = len(self.queue.pending)
                self.queue.pending = []
                return self._respond(ResponseType.SUCCESS, "I removed {} submissions from the queue.".format(n)) 

        def prioritize(self, sub):
                r = self._only(sub)
                if r is not None: return r
                self.queue.pending = [sub, *[s for s in self.queue.pending if s != sub]]
                return self._respond(ResponseType.SUCCESS, "I’ll insert {} next.".format(sub)) 

        def _only(self, sub):
                run = Runs.select(Runs, Submissions).join(Submissions).where(Submissions.lookup_hash == sub).first()
                if run is not None:
                        return self._respond(ResponseType.REFUSAL, "{} is already attached to run {}.".format(sub, run.name))
                if sub in self.queue.running:
                        return self._respond(ResponseType.REFUSAL, "{} is already being inserted.".format(sub))
                if sub in self.queue.pending:
                        return None
                return self._respond(ResponseType.CLIENT_ERROR, "{} is neither pending nor running.".format(sub))

        def _respond(self, rt, msg):
                response = Response(rt, msg)
                #_log_global('G', str(response), 'debug')
                return response


class Bot:
        def __init__(self, slack_token: str):
                self.goldberry = Goldberry(2, self.notify_job_status)
                self.slack_token = slack_token

        def __enter__(self):
                self.sc = SlackClient(self.slack_token)
                self.sc.server.auto_reconnect = True
                if not self.sc.rtm_connect():
                        raise SlackConnectionError("Couldn't connect to slack.")
                request = self.sc.api_call("users.list")
                self._users = {
                        (u['profile']['first_name'] + ' ' + u['profile']['last_name']).lower().replace('–', '-').replace('matthew', 'matt')
                        : u['id']
                        for u in request['members']
                        if not u['is_bot'] and 'first_name' in u['profile'].keys()
                }
                self.starting()
                return self

        def refresh(self):
                valar_obj.close()
                valar_obj.open()
                #self.sc = SlackClient(self.slack_token)

        def __exit__(self, *exc):
                valar_obj.close()
                self.finishing()
                return False

        def notify_job_status(self, sub: str, error: Exception):
                sub_obj = Submissions.select(Submissions, Users).where(Submissions.lookup_hash == sub).join(Users, JOIN.LEFT_OUTER, on=Submissions.user_id == Users.id).first()
                if sub_obj is None or sub_obj.user is None:
                        self.announce("<@{}> Processed {} :scream:".format(username, sub))
                user = sub_obj.user
                user = (user.first_name + ' ' + user.last_name).lower().replace('–', '-').replace('matthew', 'matt')
                username = self._users[user] if user in self._users else user
                if error is None:
                        self.announce("<@{}> Processed {} :relieved:".format(username, sub))
                else:
                        self.announce("<@{}> Processing {} failed :disappointed: :\n```{}\n```\n".format(username, sub, error.extended_message() if hasattr(error, 'extended_message') else str(error)))

        def _extract_subs(self, txt):
                return [s for s in re.findall('[0-9a-f]{12}', txt) if len(s.strip())>0]

        def handle(self, message, user, channel, tagged_users):
                message = message.replace('please', '').strip()
                if any((g == message for g in {'hello', 'hi', 'hey', 'yo', 'hola'})):
                        self.reply(message, user, channel)
                elif message == 'insert all':
                        response = self.goldberry.insert_all()
                        self.reply(response.message, user, channel)
                elif message == 'insert mine':
                        response = self.goldberry.insert_mine(user)
                        self.reply(response.message, user, channel)
                elif message.startswith('insert from'):
                        response = self.goldberry.insert_from(message.replace('insert from', '').strip())
                        self.reply(response.message, user, channel)
                elif message == 'clear':
                        response = self.goldberry.clear()
                        self.reply(response.message, user, channel)
                elif message == 'archive all':
                        response = self.goldberry.archive_all()
                        self.reply(response.message, user, channel)
                elif any([message == t for t in {'status', 'list', "list queue contents"}]):
                        def name_of(s):
                                r = Runs.select(Runs, Submissions).join(Submissions).where(Submissions.id == s.id).first()
                                z = ''
                                if r is not None:
                                        z = WellFeatures.select(WellFeatures.id, WellFeatures.well_id, Wells.id, Wells.run_id).join(Wells).first()
                                        if z is not None:
                                                z = '<has features>'
                                        else:
                                                z = '<no features>'
                                        r = 'r' + str(r.id)
                                return "• *{} ({} / {}) ({})*\n\t\t{}\n\t\t'{}'".format(s.lookup_hash, '<no run>' if r is None else r, z,  s.user.username, s.experiment.name, s.description)
                        def names(lst):
                                lst = [Submissions.fetch_or_none(s) for s in lst]
                                lst = [l for l in lst if l is not None]
                                return '\n'.join([
                                        name_of(s)      
                                        for s in lst
                                ])
                        self.reply("Running: {}".format(names(self.goldberry.queue.running)), user, channel)
                        self.reply("Pending: {}".format(names([x for x,y in self.goldberry.queue.pending])), user, channel)
                        self.reply("Not queued: {}".format(names([s for s in PATHS.pending_subs() if s not in self.goldberry.queue])), user, channel)
                        if len(self.goldberry.queue.running) + len(PATHS.pending_subs()) >= 10:
                                self.reply("That’s too many! :fearful: Humans need to fix this ASAP.", user, channel)
                elif any([message.startswith(t) for t in {'hold off on', 'stall', 'pause', 'wait to insert', "don’t insert", 'dequeue'}]):
                        if len(self._extract_subs(message)) == 0:
                                self.reply("That’s not a valid submission lookup hash. :unamused:", user, channel)
                                return
                        for sub in self._extract_subs(message):
                                response = self.goldberry.pause(sub)
                                self.reply(response.message, user, channel)
                elif any([message.startswith(t) for t in {'prioritize'}]):
                        if len(self._extract_subs(message)) == 0:
                                self.reply("That’s not a valid submission lookup hash. :unamused:", user, channel)
                                return
                        for sub in self._extract_subs(message):
                                response = self.goldberry.prioritize(sub)
                                self.reply(response.message, user, channel)
                elif any([message.startswith(t) for t in {'about'}]):
                        if len(self._extract_subs(message)) == 0:
                                self.reply("That’s not a valid submission lookup hash. :unamused:", user, channel)
                                return
                        for sub in self._extract_subs(message):
                                response = self.goldberry.about(sub)
                                self.reply(response.message, user, channel)
                elif any([message.startswith(t) for t in {'calculate'}]):
                        m = re.compile("calculate +([^ ]+) +on +(.*)").match(message)
                        if m is None:
                                self.reply("Not valid. :face_with_rolling_eyes:", user, channel)
                                return
                        feature = m.group(1)
                        sub_text = m.group(2)
                        if len(self._extract_subs(sub_text)) == 0:
                                self.reply("That’s not a valid submission lookup hash. :unamused:", user, channel)
                                return
                        for sub in self._extract_subs(sub_text):
                                response = self.goldberry.calculate(feature, sub)
                                self.reply(response.message, user, channel)
                elif any([message.startswith(t) for t in {'archive'}]):
                        if len(self._extract_subs(message)) == 0:
                                self.reply("That’s not a valid submission lookup hash. :unamused:", user, channel)
                                return
                        force = 'force' in message
                        for sub in self._extract_subs(message):
                                response = self.goldberry.archive(sub, force=force)
                                self.reply(response.message, user, channel)
                elif any([message.startswith(t) for t in {'unarchive'}]):
                        if len(self._extract_subs(message)) == 0:
                                self.reply("That’s not a valid submission lookup hash. :unamused:", user, channel)
                                return
                        force = 'force' in message
                        for sub in self._extract_subs(message):
                                response = self.goldberry.unarchive(sub, force=force)
                                self.reply(response.message, user, channel)
                elif any([message.startswith(t) for t in {'reinsert'}]):
                        if len(self._extract_subs(message)) == 0:
                                self.reply("That’s not a valid submission lookup hash. :unamused:", user, channel)
                                return
                        for sub in self._extract_subs(message):
                                response = self.goldberry.reinsert(sub)
                                self.reply(response.message, user, channel)
                elif any([message.startswith(t) for t in {'replace', 'fix'}]):
                        m = re.compile("(?:replace)|(?:fix) +([a-z0-9]{12}) +using +([a-z0-9]{12})").match(message)
                        if m is not None:
                                response = self.goldberry.replace(m.group(1), m.group(2))
                                self.reply(response.message, user, channel)
                elif any([message.startswith(t) for t in {'show layout'}]):
                        m = re.compile("show layout +({})").match(message)
                        if m is not None:
                                response = self.goldberry.show_hide(m.group(1), TemplatePlates, 'hidden', True)
                                self.reply(response.message, user, channel)
                elif any([message.startswith(t) for t in {'hide layout'}]):
                        m = re.compile("hide layout +({})").match(message)
                        if m is not None:
                                response = self.goldberry.show_hide(m.group(1), TemplatePlates, 'hidden', False)
                                self.reply(response.message, user, channel)
                elif any([message.startswith(t) for t in {'insert', 'resume', 'start', 'queue', 'enqueue'}]):  # TODO
                        if len(self._extract_subs(message)) == 0:
                                self.reply("Not a valid submission lookup hash. :unamused:", user, channel)
                                return
                        for sub in self._extract_subs(message):
                                response = self.goldberry.insert(sub, force=False)
                                self.reply(response.message, user, channel)
                else:
                        self.reply("I didn’t understand that. :confused:", user, channel)

        def starting(self):
                _log_global('G', 'Starting Goldberry', 'global')
                self.announce("Hello from Goldberry :tada:")

        def finishing(self):
                _log_global('G', 'Exiting Goldberry', 'global')
                self.announce("Goodbye :sleeping:")

        def announce(self, message):
                self.sc.rtm_send_message('C59L9A1FB', message)

        def reply(self, message, user, channel):
                #_log_global('G', "Said '{}' to '{}' in channel '{}'".format(message, user, channel), 'debug')
                self.sc.rtm_send_message(channel, "<@{}> {}".format(user, message))

        def handle_bombadil(self, message: str, user, channel):
                print("Handling Bombadil!!")
                m = re.compile(' *(?:uploaded)?(?:insert)? *([0-9a-f]{12}) *').search(message)
                #if m is not None:
                subs = self._extract_subs(message)
                for sub in subs:
                        sub = m.group(1)
                        self.goldberry.insert(sub, force=False)
                        self.reply("Queued {}.".format(sub), user, channel)

        def listen_forever(self):
                while True:
                        try:
                                read = self.sc.rtm_read()
                                for event in read:
                                        if event.get('type') == 'message':
                                                self.process(event)
                        except (slackclient.server.SlackConnectionError, WebSocketConnectionClosedException):
                                self.refresh()
                        #except  as e:
                        #       _log_global('G', "Blocking IO error", 'error')
                        #       continue
                        except (Exception, BlockingIOError) as e:
                                print('-'*60)
                                _log_global('G', 'Reading from Slack encountered error {}'.format(type(e)), 'error')
                                print(traceback.format_exception(None, e, e.__traceback__))
                                print('-'*60)
                                print('')
                        except KeyboardInterrupt as e:
                                raise e

        def process(self, event):
                # channel for notifications is C59L9A1FB
                # bombadil bot_id is B8D5W076K
                # TODO tagged_users
                bot, message, user, channel, tagged_users = event.get('bot_id'), event.get('text'), event.get('user'), event.get('channel'), None
                m = re.compile(' *(?:<@([A-Z0-9]+>))? *(?:<@([A-Z0-9]+>))? *(.+)').match(message.strip())
                if bot is None and message is not None and ('<@U6ZU9QFA6>' in message or channel.startswith('D')):
                        self.refresh()
                        message = m.group(3); tagged_users = {m.group(1), m.group(2)}
                        message = message.strip()
                        self.handle(message, user, channel, tagged_users)
                elif message is not None and bot == 'B8D5W076K':
                        self.refresh()
                        # TODO
                        #message = m.group(3); tagged_users = {m.group(1), m.group(2)}
                        message = message.strip()
                        self.handle_bombadil(message, 'B8D5W076K', channel)


if __name__ == "__main__":
        slack_token = 'xoxb-237961831346-bbPtzmYfRBboZDptwxzbXFbo'
        print("Found {} submissions in Valar".format(Submissions.select().count()))
        with Bot(slack_token) as bot:
                bot.listen_forever()


