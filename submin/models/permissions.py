from submin import models
from submin.hooks.common import trigger_hook
storage = models.storage.get("permissions")

from submin.models.repository import Repository

class Permissions(object):
	def list_paths(self, repository, vcs_type):
		return storage.list_paths(repository, vcs_type)

	#def list_permissions(*args):
	#	raise Exception(str(args))
	def list_permissions(self, repos, vcs_type, path):
		return storage.list_permissions(repos, vcs_type, path)

	def list_readable_user_paths(self, repository, vcs_type, user):
		"""Return a list of paths for this *repository* that the *user* is
		   able to read. The *user* is a User object."""
		groups = user.member_of()
		user_paths = []
		for path in self.list_paths(repository, vcs_type):
			for perm in self.list_permissions(repository, vcs_type, path):
				# due to lazy evaluation, user perms overrule group and 'all'
				if (perm['type'] == 'user' and perm['name'] == user.name) or \
						(perm['type'] == 'group' and perm['name'] in groups) or \
						(perm['type'] == 'all'):
					if perm['permission'] in ['r', 'rw']:
						user_paths.append(path)

		return set(user_paths) # remove double entries

	def list_writeable_user_paths(self, repository, vcs_type, user):
		"""Return a list of paths for this *repository* that the *user* is
		   able to write. The *user* is a User object."""
		groups = user.member_of()
		user_paths = []
		for path in self.list_paths(repository, vcs_type):
			for perm in self.list_permissions(repository, vcs_type, path):
				# due to lazy evaluation, user perms overrule group and 'all'
				if (perm['type'] == 'user' and perm['name'] == user.name) or \
						(perm['type'] == 'group' and perm['name'] in groups) or \
						(perm['type'] == 'all'):
					if perm['permission'] == 'rw':
						user_paths.append(path)

		return set(user_paths) # remove double entries

	def is_writeable(self, repository, vcs_type, user, path):
		for perm in self.list_permissions(repository, vcs_type, path):
			# due to lazy evaluation, user perms overrule group and 'all'
			if (perm['type'] == 'user' and perm['name'] == user.name) or \
					(perm['type'] == 'group' and perm['name'] in groups) or \
					(perm['type'] == 'all'):
				if perm['permission'] == 'rw':
					return True
				else:
					return False

		if path == '/': # fall through, so '/' failed, and '/' has no parent
			return False
		parent = '/'.join(path.split('/')[:-1])
		if not parent: # happens when path.split('/')[:-1] == ['']
			parent = '/'
		return self.is_writeable(repository, vcs_type, user, parent)

	def add_permission(self, repos, repostype, path,
			subject, subjecttype, perm):
		"""Sets permission for repos:path, raises a
		Repository.DoesNotExistError if repos does not exist."""
		if repos != "":
			r = Repository(repos, repostype) # check if exists

		self.check_permission(repostype, path, perm)

		storage.add_permission(repos, repostype, path, subject, subjecttype,
				perm)
		trigger_hook('permission-update', repositoryname=repos,
				repository_path=path, vcs_type=repostype)

	def check_permission(self, repostype, path, perm):
		if repostype == "git":
			if path != "/" and perm != "w": # only "w"
				raise InvalidPermissionError()
			if path == "/" and perm != "rw" and perm != "r": # only "r, rw"
				raise InvalidPermissionError()

	def change_permission(self, repos, repostype, path,
			subject, subjecttype, perm):
		"""Changes permission for repos:path, raises a
		Repository.DoesNotExistError if repos does not exist."""
		r = Repository(repos, repostype) # just for the exception
		self.check_permission(repostype, path, perm)
		storage.change_permission(repos, repostype, path, subject, subjecttype,
				perm)
		trigger_hook('permission-update', repositoryname=repos,
				repository_path=path, vcs_type=repostype)

	def remove_permission(self, repos, repostype, path, subject, subjecttype):
		storage.remove_permission(repos, repostype, path, subject, subjecttype)
		trigger_hook('permission-update', repositoryname=repos,
				repository_path=path, vcs_type=repostype)

__doc__ = """
Storage Contract
================

* list_paths(repos)
	Returns an array of paths (strings) that have permissions set.

* list_permissions(repos, repostype, path)
	Returns a list of permissions of *path* in *repos*. Each permission is
	in the following form:
		{'name': 'testUser', 'type': 'user', 'permission': 'rw'}

* add_permission(repos, repostype, path, subject, subjecttype, perm)
	Set the permission of *repos*:*path* to *subject* (user, group, all)
	to *perm*. If the *subjecttype* is 'all', then an anonymous user is
	assumed.

* change_permission(repos, repostype, path, subject, subjecttype, perm)
	Change the permission of *repos*:*path* with *subject* and type
	*subjecttype* to *perm*.

* remove_permission(repos, repostype, path, subject, subjecttype)
	Removes the permission from *repos*:*path* for *subject* with type
	*subjecttype*

"""