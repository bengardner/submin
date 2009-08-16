import plugins.backends.sql as backend
from config.authz import md5crypt

class UserExistsError(Exception):
	pass

class NoMD5PasswordError(Exception):
	def __init__(self):
		Exception.__init__(self, "Password is not encrypted with MD5")

def row_dict(cursor, row):
	# description returns a tuple; the first entry is the name of the field
	# zip makes (field_name, field_value) tuples, which can be converted into
	# a dictionary
	return dict(zip([x[0] for x in cursor.description], row))

all_fields = "id, name, email, fullname, is_admin"

def list():
	"""Generator for sorted list of users"""
	cur = backend.db.cursor()
	backend.execute(cur, """
		SELECT %s
		FROM users
		ORDER BY name ASC
	""" % all_fields)
	for x in cur:
		yield row_dict(cur, x)

def _pw_hash(password, salt=None, magic='apr1'):
	if salt is None:
		salt = md5crypt.makesalt()
	newhash = md5crypt.md5crypt(password, salt, '$' + magic + '$')
	return newhash

def add(username, password):
	if password:
		password = _pw_hash(password)
	else:
		password = ""

	cur = backend.db.cursor()
	try:
		backend.execute(cur, "INSERT INTO users (name, password) VALUES (?, ?)",
				(username, password))
	except backend.SQLIntegrityError, e:
		raise UserExistsError("User `%s' already exists" % username)

def check_password(userid, password):
	cur = backend.db.cursor()
	backend.execute(cur, "SELECT password FROM users WHERE id=?", (userid,))
	row = cur.fetchone()
	vals = row[0][1:].split('$')
	if not len(vals) == 3:
		raise NoMD5PasswordError
	magic, salt, encrypted = vals
	return _pw_hash(password, salt, magic) == row[0]

def set_password(userid, password):
	password = _pw_hash(password)
	backend.execute(backend.db.cursor(), """UPDATE users
		SET password=? WHERE id=?""", (password, userid))

# Remove functions, removes users from various tables
def remove_from_groups(userid):
	backend.execute(backend.db.cursor(), """DELETE FROM group_members
		WHERE userid=?""", (userid,))

def remove_permissions_repository(userid):
	backend.execute(backend.db.cursor(), """DELETE FROM permissions_repository
		WHERE subjecttype="user" AND subjectid=?""", (userid,))

def remove_permissions_submin(userid):
	backend.execute(backend.db.cursor(), """DELETE FROM permissions_submin
		WHERE subjecttype="user" AND subjectid=?""", (userid,))

def remove_notifications(userid):
	backend.execute(backend.db.cursor(), """DELETE FROM notifications
		WHERE userid=?""", (userid,))

def remove(userid):
	backend.execute(backend.db.cursor(), """DELETE FROM users
		WHERE id=?""", (userid,))

def user_data(username):
	cur = backend.db.cursor()
	backend.execute(cur, """
		SELECT %s
		FROM users
		WHERE name=?""" % all_fields, (username,))
	row = cur.fetchone()
	if not row:
		return None

	return row_dict(cur, row)

def field_setter(field):
	def set_field(userid, value):
		cur = backend.db.cursor()
		sql = "UPDATE users SET %s=? WHERE id=?" % field
		backend.execute(cur, sql, (value, userid))
	return set_field

set_name     = field_setter("name")
set_email    = field_setter("email")
set_fullname = field_setter("fullname")
set_is_admin = field_setter("is_admin")


member_query = """
		SELECT groups.name FROM group_members
		LEFT JOIN groups ON group_members.groupid %s groups.id
		WHERE group_members.userid = ?
		ORDER BY groups.name ASC
"""

def member_of(userid):
	"""Returns list of groups a user is a member of"""
	cur = backend.db.cursor()
	backend.execute(cur, member_query % "=", (userid,))

	return [row[0] for row in cur]

def nonmember_of(userid):
	"""Returns list of groups a user is not a member of"""
	cur = backend.db.cursor()
	backend.execute(cur, member_query % "!=", (userid,))

	return [row[0] for row in cur]

