import os
import subprocess
from objs import Variable, Operator
from myTask import MyTask
from timeit import default_timer as timer

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSLATE_BIN=os.path.join(FILE_DIR, "translate/translate.py")

def generate_atom(name, val):
    return '(' + name + '=' + str(val) + ')'


class MyError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Parser:
    def __init__(self):
        self.domain = None
        self.problem = None
        self.task = None
        self.variables = {}  # map, int (vars number) --> Variable object
        self.initial = {}
        self.goal = {}
        self.operators = set([])
        # list containing mutex groups; each is a list of tuples, each tuple has 2 elements, (var, val)
        self.mutex_groups = []

    def print_task(self):
        self.print_variables()
        print('==============================')
        self.print_initial()
        print('==============================')
        self.print_goal()
        print('==============================')
        self.print_operators()

    def print_operators(self):
        for o in self.operators:
            print(o.name)
            print('PRE')
            for p in o.prec:
                var = p[0]
                val = p[1]
                print(self.variables[var].get_str(val))
            print('EFFECTS')
            for p in o.effects:
                var = p[0]
                val1 = p[1]
                val2 = p[2]
                if val1 == -1:
                    print('---------', self.variables[var].get_str(val2))
                else:
                    print(self.variables[var].get_str(val1),
                          self.variables[var].get_str(val2))
            print('-----------------------')

    def print_variables(self):
        for v in self.variables:
            print(v)
            self.variables[v].print_me()
            print('-----------------------')

    def print_initial(self):
        for i in self.initial:
            print(self.variables[i].get_str(self.initial[i]))

    def print_goal(self):
        for i in self.goal:
            print(self.variables[i].get_str(self.goal[i]))

    def set_domain(self, path_domain):
        self.domain = path_domain

    def set_problem(self, path_problem):
        self.problem = path_problem

    def generate_file(self, sas_file_name):
        if self.domain == None or self.problem == None:
            raise MyError('Domain and/or problem not set!')
        time_limit = 1000

        ## We generate the SAS FastDownward output file: http://www.fast-downward.org/TranslatorOutputFormat
        print("Translating PDDL to SAS.....")
        # command = f'python {TRANSLATE_BIN} {time_limit} {self.domain} {self.problem} {sas_file_name} | grep "noprint"'
        # subprocess.run(command, shell=True)

        command = ['python', TRANSLATE_BIN, str(time_limit), self.domain, self.problem, sas_file_name]
        subprocess.run(command, stdout=subprocess.DEVNULL)

    def generate_task(self, sas_file_name):
        try:
            f_task = open(sas_file_name, 'r')
        except:
            raise MyError('Error opening sas file!')

        lines = f_task.readlines()
        lines = self.__process_lines(lines)
        limits = self.__get_limits(lines)
        for (init, end) in limits:
            self.process(lines[init + 1: end], lines[init])

    def process(self, lines, title):
        if 'version' in title:
            self.process_version(lines)
        if 'metric' in title:
            self.process_metric(lines)
        if 'variable' in title:
            self.process_variable(lines)
        if 'mutex_group' in title:
            self.process_mutex_group(lines)
        if 'state' in title:
            self.process_initial_state(lines)
        if 'goal' in title:
            self.process_goal(lines)
        if 'operator' in title:
            self.process_operator(lines)
        if 'rule' in title:
            self.process_rule(lines)

    def process_version(self, lines):
        # TODO
        return None

    def process_metric(self, lines):
        # TODO
        return None

    def process_variable(self, lines):
        v = Variable()
        value = int(v.set_name(lines[0]))
        rg = int(lines[2])
        for i in range(rg):
            v.add_value(i, lines[2 + i + 1])
        self.variables[value] = v

    def process_mutex_group(self, lines):
        mutex_g = []
        for line in lines[1:]:
            var = int(line.split(' ')[0])
            val = int(line.split(' ')[1])
            mutex_g.append((var, val))
        self.mutex_groups.append(mutex_g)

    def process_initial_state(self, lines):
        for i, line in enumerate(lines):
            self.initial[i] = int(line)  # var, value

    def process_goal(self, lines):
        first = True
        for line in lines:
            if first:
                first = False
                continue
            var = int(line.split(' ')[0])
            value = int(line.split(' ')[1])
            self.goal[var] = value

    def process_operator(self, lines):
        o = Operator(self.variables)
        o.set_name(lines[0])
        num_prev_cond = int(lines[1])
        if num_prev_cond != 0:
            self.__process_prevail_conditions(lines[2:2 + num_prev_cond], o)
        line_num_effects = 2 + num_prev_cond
        num_effects = int(lines[line_num_effects])
        if num_effects != 0:
            self.__process_effects(
                lines[line_num_effects + 1:line_num_effects + num_effects + 1], o)
        self.operators.add(o)
        # o.print_me()

    def process_rule(self, lines):
        # TODO
        return None

    def __process_effects(self, lines, operator):
        for line in lines:
            l_split = line.split(' ')
            if len(l_split) != 4:
                raise MyError(
                    'Incorrect number of components in effects of an operator!')
            if l_split[0] != '0':
                raise MyError('First component of effects != 0!')
            var = int(l_split[1])
            pre = int(l_split[2])
            eff = int(l_split[3])
            operator.add_prec_eff(var, pre, eff)

    def __process_prevail_conditions(self, lines, operator):
        for line in lines:
            try:
                var, value = line.split(' ')
            except:
                raise MyError('Error processing prevail conditions!')
            operator.add_precondition(int(var), int(value))

    def __get_limits(self, lines):
        initis = []
        ends = []
        for i, line in enumerate(lines):
            if 'begin_' in line:
                initis.append(i)
            if 'end_' in line:
                ends.append(i)
        if len(initis) != len(ends):
            raise MyError('Inits and ends of different size!')
        return zip(initis, ends)

    def __process_lines(self, lines):
        p_lines = []
        for line in lines:
            p_lines.append(line.split('\n')[0])
        return p_lines

    def translate_to_atomic(self):
        task = MyTask()
        debug = False
        print('Setting atoms')
        task.set_atoms(self.get_atoms(), debug)
        print('Setting initial')
        task.set_initial(self.get_initial_atomic(), debug)
        print('Setting goal')
        task.set_goal(self.get_goal_atomic(), debug)
        print('Setting actions')
        task.set_actions_atomic(self.get_actions_atomic(), debug)
        print('Setting mutexes')
        task.set_mutex_groups(self.get_mutex_groups_atomic(), debug)
        print('Setting relevant actions')
        task.set_relevant_actions(debug)
        print('Setting splitting')
        task.initialize_splitting(debug)
        start = timer()
        print('Setting compatible actions')
        task.create_compatible_actions(debug)
        print(timer() - start)
        return task

    def get_atoms(self):
        atoms = set([])
        for v in self.variables:
            var = self.variables[v]
            for val in var.possible_values:
                atoms.add(generate_atom(var.name, val))
        return atoms

    def get_initial_atomic(self):
        initial = set([])
        for var in self.initial:
            value = self.initial[var]
            initial.add(generate_atom(self.variables[var].name, value))
        # print initial
        return initial

    def get_goal_atomic(self):
        goal = set([])
        for var in self.goal:
            value = self.goal[var]
            goal.add(generate_atom(self.variables[var].name, value))
        # print goal
        return goal

    def get_actions_atomic(self):
        actions = {}
        for action in self.operators:
            act_name = action.name
            preconditions = set([])
            add_list = set([])
            del_list = set([])
            for var, val in action.prec:
                preconditions.add(generate_atom(self.variables[var].name, val))
            for var, pre, post in action.effects:
                name = self.variables[var].name
                if pre != -1:
                    # -1 is for value not important
                    atom_pre = generate_atom(name, pre)
                    preconditions.add(atom_pre)
                    if pre != post:
                        # the var changed --> old value to del list
                        del_list.add(atom_pre)
                if post != -1:
                    add_list.add(generate_atom(name, post))
                    # also, delete all other possible values! (if not in prec)
                    if pre == -1:
                        var_values = self.variables[var].possible_values
                        for v in var_values:
                            if v == post:
                                continue
                            atom_del = generate_atom(name, v)
                            del_list.add(atom_del)
            actions[act_name] = [
                list(preconditions), list(add_list), list(del_list)]
        return actions

    def get_mutex_groups_atomic(self):
        mutex_groups_atomic = []
        for mutex_group in self.mutex_groups:
            # mutex_group is a list of tuples
            mg = []
            for var, val in mutex_group:
                name = self.variables[var].name
                mg.append(generate_atom(name, val))
            mutex_groups_atomic.append(mg)
        return mutex_groups_atomic

    def get_var_string(self, name):
        # name = (varX=Y)
        s = name[1:len(name) - 1]
        # s = varX=Y
        var = int(s.split('=')[0].split('var')[1])
        val = int(s.split('=')[1])
        return self.variables[var].get_str(val)
