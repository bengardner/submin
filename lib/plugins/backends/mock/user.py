from models.exceptions import UserExistsError

mock_users = [] # [{'id': 0, 'name': 'test'}]

def clear_users():
	global mock_users
	mock_users = []

class NoMD5PasswordError(Exception):
	def __init__(self):
		Exception.__init__(self, "Password is not encrypted with MD5")

def id2name(userid):
	return mock_users[userid]["name"]

def list():
	"""Generator for sorted list of users"""
	return mock_users

def add(username, password):
	for user in mock_users:
		if user['name'] == username:
			raise UserExistsError("User `%s' already exists" % username)

	mock_users.append({'name': username, 'password': password, 'email': '',
		'fullname': username, 'is_admin': False})
	u = mock_users[-1]
	u['id'] = mock_users.index(u)

def check_password(userid, password):
	return mock_users[userid]['password'] == password

def set_password(userid, password):
	mock_users[userid]['password'] = password

# Remove functions, removes users from various tables
def remove_from_groups(userid):
	pass

def remove_permissions_repository(userid):
	pass

def remove_permissions_submin(userid):
	pass

def remove_notifications(userid):
	pass

def remove(userid):
	del mock_users[userid]

def user_data(username):
	for user in mock_users:
		if user['name'] == username:
			return user

	return None

def field_setter(field):
	def set_field(userid, value):
		mock_users[userid][field] = value
	return set_field

set_name     = field_setter("name")
set_email    = field_setter("email")
set_fullname = field_setter("fullname")
set_is_admin = field_setter("is_admin")

def member_of(userid):
	pass

def nonmember_of(userid):
	pass
