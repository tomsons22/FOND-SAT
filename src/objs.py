import sys

class MyObjError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class Variable():
	def __init__(self):
		self.name = None
		self.possible_values = []
		self.map_value_string = {}

	def set_name(self, name):
		self.name = name
		return name.split('var')[1]

	def add_value(self, v, v_str):
		self.possible_values.append(v)
		name = v_str
		if 'NegatedAtom' in v_str:
			self.map_value_string[v] = '-' + name
		elif 'Atom' in v_str:
			self.map_value_string[v] = name
		else:
			print('WARNING: variable not Atom nor NegatedAtom;', name)
			self.map_value_string[v] = name

	def print_me(self):
		print(self.name)
		for i in self.possible_values:
			print(i, '-->', self.map_value_string[i])

	def get_str(self, v):
		return self.map_value_string[v]

	def get_atoms(self):
		atoms = set([])
		for v in self.possible_values:
			name = self.map_value_string[v]
			if self.map_value_is_neg[v]:
				atoms.add(name[1:])
			else:
				atoms.add(name)
		return atoms

class Operator:
	def __init__(self, variables = None):
		self.name = None
		self.prec = []
		self.effects = []
		self.variables = variables # map from integer to variable

	def set_name(self, name):
		name = name.split(' ')
		self.name = name[0] + '('
		for i in name[1:]:
			self.name += i + ','
		self.name = self.name[:-1] + ')'

	def add_prec_eff(self, var, pre, eff):
		self.add_precondition(var, pre)
		self.add_effect(var, pre, eff)

	def add_precondition(self, var, value):
		if value != -1:
			if [var, value] not in self.prec:
				self.prec.append([var, value])

	def add_effect(self, var, pre, effect):
		if [var, pre, effect] not in self.effects:
			self.effects.append([var, pre, effect])

	def print_me(self):
		print(self.name, self.prec, self.effects)