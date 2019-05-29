import shutil

from CNF import CNF
import os
import sys
from parser import Parser
from myTask import MyTask
from timeit import default_timer as timer
import time
import argparse

TMP_DIR = 'tmp'
# TMP_LOGS_DIR = os.path.join(TMP_DIR, 'logs-run')


def clean(n1, n2, n3, n4, n5, msg):
    print(msg)
    os.system('rm %s %s %s %s %s' % (n1, n2, n3, n4, n5))


def generateControllerStates(i):
    controllerStates = ['n0']
    for j in range(i):
        controllerStates.append('n' + str(j + 1))
    controllerStates.append('ng')
    return controllerStates


# PARSE ARGUMENTS
args_parser = argparse.ArgumentParser(description='Process arguments to SAT FOND planner')
args_parser.add_argument(
    'path_domain',
    help='Path to domain file (pddl)')
args_parser.add_argument(
    'path_instance',
    help='Path to problem instance file (pddl)')
args_parser.add_argument(
    '--time_limit',
    type=int,
    default=3600,
    help='Time limit (int) for solver in seconds (default: %(default)s).')
args_parser.add_argument(
    '--mem_limit',
    type=int,
    default=4096,
    help='Memory limit (int) for solver in MB (default: %(default)s)')
args_parser.add_argument(
    '--name_temp',
    default='temp',
    help='Name for temp files; erased after solver is done (default: %(default)s)')
args_parser.add_argument(
    '--strong',
    action='store_true',
    default=False,
    help='Search for strong  solutions (instead of default strong cyclic solutions) - (default: %(default)s)')
args_parser.add_argument(
    '--inc',
    type=int,
    default=1,
    help='Increments in controller size per step (default: %(default)s)')
args_parser.add_argument(
    '--gen-info',
    action='store_true',
    default=False,
    help='Show info about SAT formula generation %(default)s)')
args_parser.add_argument(
    '--show-policy',
    action='store_true',
    default=False,
    help='Show final policy, if found %(default)s)')
args_parser.add_argument(
    '--no-clean',
    action='store_true',
    default=False,
    help='Do not clean temporary files created %(default)s)')

params = vars(args_parser.parse_args())  # vars returns a dictionary of the arguments

print(params)  # just print the options that will be used

if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

time_start = timer()
time_limit = params['time_limit']
time_buffer = 2
mem_limit = params['mem_limit']

print_policy = params['show_policy']
strong = params['strong']
show_gen_info = params['gen_info']
no_clean = params['no_clean']


# Let's now parse the PDDL domain and problem and generate SAS files (http://www.fast-downward.org/TranslatorOutputFormat)
p = Parser()    # build utlity object Parser
p.set_domain(params['path_domain'])
p.set_problem(params['path_instance'])
name_SAS_file = os.path.join(TMP_DIR, 'output-sas-{}.txt'.format(params['name_temp']))                # aux file
p.generate_file(name_SAS_file)
p.generate_task(name_SAS_file)



my_task = p.translate_to_atomic()
fair = my_task.is_fair()

# Before we start iterationg, create a CNF object
name_formula_file = os.path.join(TMP_DIR, 'formula-{}.txt'.format(params['name_temp']))                # aux file
name_formula_file_extra = os.path.join(TMP_DIR, 'formula-extra-{}.txt'.format(params['name_temp']))    # aux file
name_output_satsolver = os.path.join(TMP_DIR, 'outsat-{}.txt'.format(params['name_temp']))             # aux file
cnf = CNF(name_formula_file, name_formula_file_extra, fair, strong)  # generate CNF formla into aux files

solver_time = []
for i in range(1000):   # try up to controller of size 1000
    if timer() - time_start > time_limit - time_buffer:
        clean(name_formula_file, name_output_satsolver, name_SAS_file, name_formula_file_extra, name_final,
                       '-> OUT OF TIME')

    # generate set of controller states (depending on iteration and scaling rate)
    controllerStates = generateControllerStates(i * params['inc'])

    print('#######################################################################################')
    print('Trying with {} states'.format(len(controllerStates)))
    print('Looking for strong plans: {}'.format((strong)))
    print('Fair actions: {}'.format(str(fair)))
    print('# Atoms: {}'.format(len(my_task.get_atoms())))
    print('# Actions: {}'.format(len(my_task.get_actions())))

    cnf.reset()
    start_g = timer()

    ## GENERATE CNF for the particular size of the controller
    # Use n0 and ng are the atoms for initial and goal controller states
    cnf.generate_clauses(my_task, 'n0', 'ng', controllerStates, len(controllerStates), p, show_gen_info)

    print('SAT formula generation time = {:f}'.format(timer() - start_g))
    print('# Clauses = {}'.format(cnf.getNumberClauses()))
    print('# Variables = {}'.format(cnf.getNumberVariables()))

    if timer() - time_start > time_limit - time_buffer:
        clean(name_formula_file, name_output_satsolver, name_SAS_file, name_formula_file_extra, name_final,
                       '-> OUT OF TIME')

    print('Creating formula...')
    name_final = cnf.generateInputSat(name_formula_file)

    print('\t Done creating formula. Calling solver...')
    start_solv = timer()

    time_for_sat = int(time_limit - (timer() - time_start))
    if time_for_sat < time_buffer:
        clean(name_formula_file, name_output_satsolver, name_SAS_file, name_formula_file_extra, name_final,
                       '-> OUT OF TIME')

    ## NOW, WE SOLVE THE SAT PROBLEM VIA MINISAT SOLVER (http://minisat.se/)
    # command = '/path/to/SATsolver/minisat -mem-lim=%i -cpu-lim=%i %s %s' % (mem_limit, time_for_sat, name_formula_file, name_output_satsolver)
    command = './minisat {} {}'.format(name_formula_file, name_output_satsolver)

    print('SAT solver called with {:d}MB and {:d} seconds limits'.format(mem_limit, time_for_sat))
    os.system(command)
    end_solv = timer()
    solver_time.append(end_solv - start_solv)
    print('Done solver. Round time: {:f}'.format(end_solv - start_solv))
    print('Cumulated solver time: {}'.format(sum(solver_time)))

    result = cnf.parseOutput(name_output_satsolver, controllerStates, p, print_policy)
    if result is None:
        clean(name_formula_file, name_output_satsolver, name_SAS_file, name_formula_file_extra, name_final,
                       '-> OUT OF TIME/MEM')
    if result:
        break
    print('UNSATISFIABLE')

print('Elapsed total time (s): {:f}'.format(timer() - time_start))
print('Elapsed solver time (s): {:f}'.format(sum(solver_time)))
print('Elapsed solver time (s): {}'.format(str(solver_time)))
print('Looking for strong plans: {}'.format(str(strong)))
print('Fair actions: {}'.format(str(fair)))

# clean up all auxiliarly files created
if not no_clean:
    clean(name_formula_file, name_output_satsolver, name_SAS_file, name_formula_file_extra, name_final, 'Done')
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)
exit(0)

