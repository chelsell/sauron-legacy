from klgists.common import *
from klgists.files.wrap_cmd_call import wrap_cmd_call
from klgists.files import make_dirs
from klgists.files.file_hasher import FileHasher
from ..task_utils import *

import hashlib, shutil, logging
hasher = FileHasher(hashlib.sha256, '.sha256')


class MakeVideoError(Exception):
	pass


class TaskMakeVideo:
	"""
	DAG Task for converting frames obtained from a run of SauronX to a compressed video. Takes compressed file of camera
	frames, extracts all frames, compresses frames to a video, and then generates a file containing the hash of the
	compressed video file.
	"""
	@staticmethod
	def run(sub: str, path: str, **kwargs):
		ti = kwargs["ti"]
		v_path = TaskUtils.video_file(path)
		sz_path = pjoin(path, 'frames.7z')
		if not pexists(sz_path):
			raise MakeVideoError("{} not found! ".format(sz_path))
		tmp_frames_path = pjoin(path, "tmpframes")
		logging.info("Extracting frames to {}".format(tmp_frames_path))
		TaskUtils.update_status('extracting', ti.xcom_pull(task_ids='retrieve_sub_info'))
		wrap_cmd_call(['7za', 'x', sz_path, "-o{}".format(tmp_frames_path), '-aos'])
		logging.info("Frames successfully extracted.")
		TaskUtils.update_status('extracted', ti.xcom_pull(task_ids='retrieve_sub_info'))
		if pexists(tmp_frames_path):
			logging.info("Making video at {}".format(v_path))
			make_dirs(os.path.dirname(v_path))
			TaskUtils.update_status('compressing', ti.xcom_pull(task_ids='retrieve_sub_info'))
			wrap_cmd_call([
					'ffmpeg',
					'-pattern_type', 'glob',
					'-i', "{}/**/*.jpg".format(tmp_frames_path),
					'-safe', '0',
					'-vf', "scale=trunc(iw/2)*2:trunc(ih/2)*2",
					'-c:v', 'libx265',
					'-crf', str(ConfigUtils.get_key('crf')),
					'-pix_fmt', 'yuv420p',
					'-y', v_path
			])
			logging.info("Video successfully created.")
			TaskUtils.update_status('compressed', ti.xcom_pull(task_ids='retrieve_sub_info'))
			hasher.add_hash(v_path)
			shutil.rmtree(tmp_frames_path)


__all__ = ['TaskMakeVideo']