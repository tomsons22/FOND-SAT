import sys


class MyTask():
	def __init__(self):
		self.atoms = None # Set
		self.initial = None # Set of atoms
		self.goal = None # Set of atoms
		self.actions = None # Dictionary, name --> [precs, adds, dels]
		self.action_nondet = {} # name --> list other actions
		self.action_cardinality = {} # name --> number
		self.mutex_groups = None # list of list; each sub-list has atoms belonging to the same mutex group
		self.compatible_actions = {} # action name --> set of compatible actions
		self.mutex_groups_set = [] # list of sets of mutex groups
		self.relevant_actions_atom = {} # dictionary: atom --> relevant actions
		self.relevant_actions_atom_aname = {} # dictionary: (atom, a_name) --> relevant actions
		self.action_names = None # set
		self.other_actions_name = {} # Dictionary name --> list of other actions
		self.action_name_to_actions = {} # action_name --> list of actions

	def getOrderedActions(self):
		return self.ordered_actions

	def is_fair(self):
		for a in self.actions:
			if '_unfair_' in a:
				return False
		return True

	def get_initial(self):
		return self.initial

	def get_goal(self):
		return self.goal

	def get_atoms(self):
		return self.atoms

	def get_actions(self):
		return self.actions

	def get_action_names(self):
		return self.action_names

	def get_preconditions(self, action):
		return self.actions[action][0]

	def get_add_list(self, action):
		return self.actions[action][1]

	def get_del_list(self, action):
		return self.actions[action][2]

	def get_mutex_groups(self):
		return self.mutex_groups

	def get_action_cardinality(self, action):
		return self.action_cardinality[action]

	def get_actions_with_name(self, name):
		return self.action_name_to_actions[name]

	def get_other_actions_name(self, action):
		return self.other_actions_name[action]

	def get_action_name(self, action):
		return action.split('(')[0]

	def set_atoms(self, atoms, debug = False):
		"""Set of all atoms"""
		self.atoms = atoms
		print('# Atoms: %i' % len(atoms))
		if debug:
			print('Set atoms: %s' % str(self.atoms))

	def set_initial(self, initial, debug = False):
		""""Set of initial"""
		self.initial = initial
		if debug:
			print('Set initial %s' % str(self.initial))

	def set_goal(self, goal, debug = False):
		"""Goal"""
		self.goal = goal
		if debug:
			print('Goal %s' % str(self.goal))

	def set_actions_atomic(self, actions, debug = False):
		"""Actions"""
		self.actions = actions
		print('# Actions: %i' % len(actions))
		print('\tSetting other actions')
		self.generate_other_actions()
		print('\tSetting action card')
		self.generate_action_cardinality()
		if debug:
			for a in self.actions:
				print(a, self.action_nondet[a])
				print(actions[a])

	def set_mutex_groups(self, m_groups, debug = False):
		"""Mutex groups"""
		self.mutex_groups = m_groups
		if debug:
			for mg in self.mutex_groups:
				print(mg)

	def generate_action_cardinality(self):
		# self.action_nondet = {} # name --> list other actions
		# self.action_cardinality = {} # name --> number
		for a in self.actions:
			others = self.action_nondet[a]
			self.action_cardinality[a] = len(others) + 1
			name = self.get_action_name(a)
			self.action_cardinality[name] = len(others) + 1

	def generate_other_actions(self):
		counter = 0
		total = len(self.actions)
		for a in self.actions:
			if counter % 1000 == 0:
				print(counter, '/', total)
			counter += 1
			if '_DETDUP_' not in a:
				# No nondet effects
				self.action_nondet[a] = []
				continue
			other = []
			for a2 in self.actions:
				if a2 == a:
					continue
				if self.__check_if_belong_same_det(a, a2):
					other.append(a2)
			self.action_nondet[a] = other

	def __check_if_belong_same_det(self, a1, a2):
		# I know that a1 has '_DETDUP_' in name
		sep = '_DETDUP_'
		if sep not in a2:
			return False
		if a1.split(sep)[0] != a2.split(sep)[0]:
			return False
		if a1.split('(')[1] != a2.split('(')[1]:
			return False
		return True

	def get_other_actions(self, action):
		return self.action_nondet[action]

	def set_relevant_actions(self, debug = False):
		# action a is relevant to atom p if:
		# - p \in del(b)
		# - p \in add(b)
		# - p \not \in add(b) and some sibling action adds p
		for p in self.atoms:
			rel_actions = self._compute_relevant_actions(p)
			self.relevant_actions_atom[p] = rel_actions

	def _compute_relevant_actions(self, atom):
		rel_actions = set([])
		for a in self.actions:
			add_list = self.get_add_list(a)
			del_list = self.get_del_list(a)
			if atom in del_list or atom in add_list:
				rel_actions.add(a)
			siblings = self.get_other_actions(a)
			for s in siblings:
				add_sibling = self.get_add_list(s)
				if atom in add_sibling and atom not in add_list:
					rel_actions.add(a)
		return rel_actions

	def get_relevant_actions(self, atom):
		return self.relevant_actions_atom[atom]

	def create_compatible_actions(self, debug = False):
		self.mutex_groups_set = [set(mg) for mg in self.mutex_groups]
		counter = 0
		total = len(self.actions)
		for a1 in self.actions:
			if counter % 1000 == 0:
				print(counter, '/', total)
			counter += 1
			compatible_acts = set([])
			other_actions = self.action_nondet[a1]
			#for a2 in self.actions:
			for a2 in self.get_actions_with_name(self.get_action_name(a1)):
				if a2 == a1 or a2 in other_actions:
					continue
				if self._actions_are_compatible(a1, a2):
					compatible_acts.add(a2)
			self.compatible_actions[a1] = compatible_acts

	def _actions_are_compatible(self, a1, a2):
		precs1 = self.get_preconditions(a1)
		precs2 = self.get_preconditions(a2)
		pairs = self._get_all_pairs(precs1, precs2)
		for p1, p2 in pairs:
			if p1 == p2:
				continue
			if self._atoms_belong_to_same_mutex(p1, p2):
				return False
		return True

	def _atoms_belong_to_same_mutex(self, p1, p2):
		for mg in self.mutex_groups_set:
			if p1 in mg and p2 in mg:
				return True
		return False

	def _get_all_pairs(self, coll1, coll2):
		pairs = []
		for i in coll1:
			for j in coll2:
				pairs.append([i, j])
		return pairs

	def actions_are_compatible(self, a1, a2):
		return a2 in self.compatible_actions[a1]

	def initialize_splitting(self, debug):
		self.action_names = self.compute_action_names()
		self.other_actions_name = self.compute_other_actions_name()
		self.action_name_to_actions = self.compute_actions_name_to_actions()

	def compute_actions_name_to_actions(self):
		a_names_to_actions = {}
		for a_name in self.action_names:
			a_names_to_actions[a_name] = []
		for a in self.actions:
			name = self.get_action_name(a)
			a_names_to_actions[name].append(a)
		return a_names_to_actions

	def compute_other_actions_name(self):
		other = {}
		for a in self.action_names:
			if '_DETDUP_' not in a:
				other[a] = []
				continue
			other_names = []
			for a2 in self.action_names:
				if a2 == a:
					continue
				if self.get_action_name(a).split('_DETDUP_')[0] == self.get_action_name(a2).split('_DETDUP_')[0]:
					other_names.append(a2)
			other[a] = other_names
		return other

	def compute_action_names(self):
		names = set([])
		for a in self.actions:
			name = self.get_action_name(a)
			names.add(name)
		return names

	def decompose_action(self, action):
		name = self.get_action_name(action)
		args = self.get_action_args(action)
		return [name] + args

	def print_task(self):
		print('ATOMS ================================================')
		for a in self.atoms:
			print(a)
		print('INITIAL ==============================================')
		for a in self.initial:
			print(a)
		print('GOAL =================================================')
		for a in self.goal:
			print(a)
		print('ACTIONS ==============================================')
		for a in self.actions:
			print(a, self.get_other_actions(a))
			print(a, self.actions[a])