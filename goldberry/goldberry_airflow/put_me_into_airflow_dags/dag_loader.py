from airflow import DAG
import pickle
import sys, os
sys.path.insert(0,os.path.abspath(os.environ['GOLDBERRY']))
sys.path.append(os.path.abspath(os.environ['KALE']))
from kale.core.valar_singleton import *
from klgists.common import *

pickle_dir = os.environ['AIRFLOW_PICKLED_DAGS']
for f in os.listdir(pickle_dir):
	ext = os.path.splitext(os.path.basename(f))[1]
	sub = os.path.splitext(os.path.basename(f))[0]
	if ext == '.obj':
		globals()[sub] = pickle.load(open(pjoin(pickle_dir, f), 'rb'))
