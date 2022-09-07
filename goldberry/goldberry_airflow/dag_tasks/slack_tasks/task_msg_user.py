from slackclient import SlackClient
from airflow.hooks.base_hook import BaseHook
from valarpy.model import *
import os

SLACK_CONN_ID = 'slack'
slack_token = BaseHook.get_connection(SLACK_CONN_ID).password

class MessageUser:
	"""
	DAG Task for finding and Messaging Slack User associated with a given run
	"""
	@staticmethod
	def run(sub: str, message: str):
		sc = SlackClient(slack_token)
		request = sc.api_call("users.list")
		_users = {
			(u['real_name']).lower().replace('–', '-').replace('matthew', 'matt')
			: u['id']
			for u in request['members']
			if not u['is_bot'] and 'real_name' in u.keys()
		}
		sub_usr = Submissions.select(Submissions, Users).where(Submissions.lookup_hash == sub). \
			join(Users, JOIN.LEFT_OUTER, on=Submissions.user_id == Users.id).first()
		user_name = sub_usr.user
		user = (user_name.first_name + ' ' + user_name.last_name).lower().replace('–', '-').replace('matthew', 'matt')
		username = '@'+_users[user] if user in _users else '#notifications'
		sc.api_call(
			"chat.postMessage",
			channel="{}".format(username),
			text='{} {}.'.format(message, sub),
			as_user=True
		)


__all__ = ['MessageUser']