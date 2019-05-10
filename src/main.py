from CNF import CNF
import os
import sys
from parser import Parser
from myTask import MyTask
from timeit import default_timer as timer
import time
import argparse


def clean_and_exit(n1, n2, n3, n4, n5, msg):
	print(msg)
	os.system('rm %s %s %s %s %s' % (n1, n2, n3, n4, n5))
	exit()


def generateControllerStates(i):
	controllerStates = ['n0']
	for j in range(i):
		controllerStates.append('n' + str(j + 1))
	controllerStates.append('ng')
	return controllerStates


# PARSE ARGUMENTS
args_parser = argparse.ArgumentParser(description = 'Process arguments to SAT FOND planner')
args_parser.add_argument(
	'path_domain',
	help = 'Path to domain file (pddl)')
args_parser.add_argument(
	'path_instance',
	help = 'Path to problem instance file (pddl)')
args_parser.add_argument(
	'--time_limit',
	type = int,
	default = 3600,
	help = 'Time limit (int) for solver in seconds (default: %(default)s).')
args_parser.add_argument(
	'--mem_limit',
	type = int,
	default = 4096,
	help = 'Memory limit (int) for solver in MB (default: %(default)s)')
args_parser.add_argument(
	'--name_temp',
	default = 'temp',
	help = 'Name for temp files; erased after solver is done (default: %(default)s)')
args_parser.add_argument(
	'--strong',
	action='store_true',
	dest='STRONG',
	default=False,
	help = 'Search for strong  solutions (instead of default strong cyclic solutions) - (default: %(default)s)')
args_parser.add_argument(
	'--inc',
	type = int,
	default = 1,
	help = 'Increments in controller size per step (default: %(default)s)')
args_parser.add_argument(
	'--gen-info',
	action='store_true',
	dest='GEN_INFO',
	default=False,
	help = 'Show info about SAT formula generation %(default)s)')
args_parser.add_argument(
	'--show-policy',
	action='store_true',
	dest='SHOW_POLICY',
	default = False,
	help = 'Show final policy, if found %(default)s)')

params = vars(args_parser.parse_args())	# vars returns a dictionary of the arguments

print(params)	# just print the options that will be used

time_start = timer()
time_limit = params['time_limit']
time_buffer = 2
mem_limit = params['mem_limit']

p = Parser()
p.set_domain(params['path_domain'])
p.set_problem(params['path_instance'])

name_formula_file = 'formula-' + params['name_temp'] + '.txt'
name_formula_file_extra = 'formula-extra-' + params['name_temp'] + '.txt'
name_output_satsolver = 'outsat-' + params['name_temp'] + '.txt'
name_sas_file = 'outputtrans-' + params['name_temp'] + '.sas'
p.generate_file(name_sas_file)
p.generate_task(name_sas_file)
my_task = p.translate_to_atomic()
fair = my_task.is_fair()

print_policy  = params['SHOW_POLICY']
strong = params['STRONG']
show_gen_info = params['GEN_INFO']

cnf = CNF(name_formula_file, name_formula_file_extra, fair, strong)

solver_time = []
for i in range(1000):
	if timer() - time_start > time_limit - time_buffer:
		clean_and_exit(name_formula_file, name_output_satsolver, name_sas_file, name_formula_file_extra, name_final, '-> OUT OF TIME')

	controllerStates = generateControllerStates(i * params['inc'])

	print('=================================================')
	print('Trying with %i states' % len(controllerStates))
	print('Looking for strong plans: %s' % str(strong))
	print('Fair actions: %s' % str(fair))
	print('# Atoms: %i' % len(my_task.get_atoms()))
	print('# Actions: %i' % len(my_task.get_actions()))

	cnf.reset()
	start_g = timer()
	cnf.generate_clauses(my_task, 'n0', 'ng', controllerStates, len(controllerStates), p, show_gen_info)
	
	print('SAT formula generation time = %f' % (timer() - start_g))
	print('# Clauses = %i' % cnf.getNumberClauses())
	print('# Variables = %i' % cnf.getNumberVariables())

	if timer() - time_start > time_limit - time_buffer:
		clean_and_exit(name_formula_file, name_output_satsolver, name_sas_file, name_formula_file_extra, name_final, '-> OUT OF TIME')

	print('Creating formula...')
	name_final = cnf.generateInputSat(name_formula_file)
	
	print('Done creating formula. Calling solver...')
	start_solv = timer()

	time_for_sat = int(time_limit - (timer() - time_start))
	if time_for_sat < time_buffer:
		clean_and_exit(name_formula_file, name_output_satsolver, name_sas_file, name_formula_file_extra, name_final, '-> OUT OF TIME')

	command = './minisat %s %s' % (name_formula_file, name_output_satsolver)
	# command = '/path/to/SATsolver/minisat -mem-lim=%i -cpu-lim=%i %s %s' % (mem_limit, time_for_sat, name_formula_file, name_output_satsolver)
	print('SAT solver called with %i MB and %i seconds' % (mem_limit, time_for_sat))
	os.system(command)
	end_solv = timer()
	solver_time.append(end_solv - start_solv)
	print('Done solver. Round time: %f' % (end_solv - start_solv))
	print('Cumulated solver time: %f' % sum(solver_time))

	result = cnf.parseOutput(name_output_satsolver, controllerStates, p, print_policy)
	if result is None:
		clean_and_exit(name_formula_file, name_output_satsolver, name_sas_file, name_formula_file_extra, name_final, '-> OUT OF TIME/MEM')
	if result:
		break
	print('UNSATISFIABLE')

print('Elapsed total time (s): %f' % (timer() - time_start))
print('Elapsed solver time (s): %f' % sum(solver_time))
print('Elapsed solver time (s): %s' % str(solver_time))
print('Looking for strong plans: %s' % str(strong))
print('Fair actions: %s' % str(fair))
clean_and_exit(name_formula_file, name_output_satsolver, name_sas_file, name_formula_file_extra, name_final, 'Done')