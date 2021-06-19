import sys
import os

cd_fond_sat = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cd_fond_sat)

import shutil
from CNF import CNF
from parser import Parser
from myTask import MyTask
from timeit import default_timer as timer
import time
import argparse

TMP_DIR = os.path.join(cd_fond_sat, 'tmp') # subdir where to store all aux files generated (e.g., SAS files)

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
    '--start',
    type=int,
    default=1,
    help='Size of the policy to start trying (default: %(default)s)')
args_parser.add_argument(
    '--inc',
    type=int,
    default=1,
    help='Increments in controller size per step. By default the planner looks for a solution of size *2*, if it does not find one it looks for a solution of size *3*, and so on. If inc is set to *i*, the planner looks for a solution of size *2*, if it does not find one it looks for a solution of size *2+i*, and so on (default: %(default)s)')
args_parser.add_argument(
    '--gen-info',
    action='store_true',
    default=False,
    help='Show info about SAT formula generation (default: %(default)s)')
args_parser.add_argument(
    '--show-policy',
    action='store_true',
    default=False,
    help='Show final policy, if found (default: %(default)s)')
args_parser.add_argument(
    '--draw-policy',
    action='store_true',
    default=False,
    help='Draw final policy (controller), if found (default: %(default)s)')
args_parser.add_argument(
    '--no-clean',
    action='store_true',
    default=False,
    help='Do not clean temporary files created (default: %(default)s)')

params = vars(args_parser.parse_args())  # vars returns a dictionary of the arguments

print(params)  # just print the options that will be used

if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

time_start = timer()
time_limit = params['time_limit']
time_buffer = 2
mem_limit = params['mem_limit']

print_policy = params['show_policy']
draw_policy = params['draw_policy']
strong = params['strong']
show_gen_info = params['gen_info']
no_clean = params['no_clean']


# Parse the PDDL domain and problem and generate SAS files (http://www.fast-downward.org/TranslatorOutputFormat)
# (all aux files created in temporary directory)
p = Parser()    # build utility object Parser
p.set_domain(os.path.abspath(params['path_domain']))
p.set_problem(os.path.abspath(params['path_instance']))
name_SAS_file = os.path.join(TMP_DIR, 'output-sas-{}.txt'.format(params['name_temp']))                # aux file

# Seb: change to FOND-SAT folder and remember where we where. FOND-SAT must be in its src/ folder to run
current_dir = os.getcwd()
os.chdir(cd_fond_sat)

p.generate_file(name_SAS_file)
p.generate_task(name_SAS_file)

my_task = p.translate_to_atomic()
fair = my_task.is_fair()

# Before we start iterating (on no of controller states), create a CNF object
name_formula_file = os.path.join(TMP_DIR, 'formula-{}.txt'.format(params['name_temp']))                # aux file
name_formula_file_extra = os.path.join(TMP_DIR, 'formula-extra-{}.txt'.format(params['name_temp']))    # aux file
name_output_satsolver = os.path.join(TMP_DIR, 'outsat-{}.txt'.format(params['name_temp']))             # aux file
cnf = CNF(name_formula_file, name_formula_file_extra, fair, strong)  # generate CNF formla into aux files

solver_time = []
for i in range(params['start'], 1000):   # try up to controller of size 1000
    if timer() - time_start > time_limit - time_buffer:
        clean(name_formula_file, name_output_satsolver, name_SAS_file, name_formula_file_extra, name_final,
                       '-> OUT OF TIME')

    # GENERATE set of CONTROLLER STATES (depending on iteration and scaling rate)
    controllerStates = generateControllerStates(i * params['inc'])

    print('#######################################################################################')
    print('Trying with {} states'.format(len(controllerStates)))
    print('Looking for strong plans: {}'.format((strong)))
    print('Fair actions: {}'.format(str(fair)))
    print('# Atoms: {}'.format(len(my_task.get_atoms())))
    print('# Actions: {}'.format(len(my_task.get_actions())))

    cnf.reset()
    start_g = timer()

    ## 1 - GENERATE CNF for the particular size of the controller
    #       Use n0 and ng are the atoms for initial and goal controller states
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

    time_for_sat = int(time_limit - (timer() - time_start))
    if time_for_sat < time_buffer:
        clean(name_formula_file, name_output_satsolver, name_SAS_file, name_formula_file_extra, name_final,
                       '-> OUT OF TIME')

    ## 2 - NOW, WE SOLVE THE SAT PROBLEM VIA MINISAT SOLVER (http://minisat.se/)
    print('Will now call SAT solver with {:d}MB and {:d} seconds limits'.format(mem_limit, time_for_sat))
    command = './minisat {} {}'.format(name_formula_file, name_output_satsolver)
    # command = '/path/to/SATsolver/minisat -mem-lim={} -cpu-lim={} {} {}'.format(mem_limit, time_for_sat, name_formula_file, name_output_satsolver)
    start_solver_time = timer()
    os.system(command)  # actual call to solver!
    end_solver_time = timer()
    solver_time.append(end_solver_time - start_solver_time)
    print('Done solver. Round time: {:f}'.format(end_solver_time - start_solver_time))
    print('Cumulated solver time: {}'.format(sum(solver_time)))

    ## 3 - PARSE OUTPUT OF SAT SOLVER AND CHECK IF IT WAS SOLVED
    #TODO: would be nice to have this return a representation of the policy, and then have a print facility
    result = None
    if not draw_policy:
        result = cnf.parseOutput(name_output_satsolver, controllerStates, p, print_policy)
    else:
        file_name = os.path.join(current_dir, "policy.sol")
        out_file_name = os.path.join(current_dir, "policy_graph")
        result = cnf.parseOutputPrintController(name_output_satsolver, controllerStates, p,file_name,out_file_name)

    if result is None:  # clean-up whatever aux files were generated for this iteration
        clean(name_formula_file, name_output_satsolver, name_SAS_file, name_formula_file_extra, name_final,
                       '-> OUT OF TIME/MEM')
    if result:  # plan found, get out of the iteration!
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

# Seb: return to there it was called
os.chdir(current_dir)

exit(0)

