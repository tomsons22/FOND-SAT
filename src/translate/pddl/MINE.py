import pddl_file

domain = '/home/tomas/Desktop/haz-planner-for-relevant-policies-5424747c19a5/fond-benchmarks/tireworld/domain.pddl'
problem = '/home/tomas/Desktop/haz-planner-for-relevant-policies-5424747c19a5/fond-benchmarks/tireworld/p01.pddl'

pddl_file.open(problem, domain).dump()