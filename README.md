# FOND-SAT: A SAT-based FOND planning system for compact controllers

FOND solver based on SAT, as per the following paper:

* Tomas Geffner, Hector Geffner: [Compact Policies for Fully Observable Non-Deterministic Planning as SAT](https://arxiv.org/pdf/1806.09455.pdf). ICAPS 2018: 88-96

## Planner setup & pre-requisites

### Files

* `F-domains/` contains the FOND domains used
* `src/` contains the code for the solver, and a pre-compiled version of Minisat
  * `src/translate` contains the the parser from [PRP](https://github.com/QuMuLab/planner-for-relevant-policies).

### Python Modules

```bash
$ pip install graphviz # to draw controllers
```

### SAT solvers

Two SAT solvers are already provided: [MiniSat](https://github.com/master-keying/minisat/) (default) and [Glucose](https://www.labri.fr/perso/lsimon/glucose/).

For easiness to use, binary Linux version of both are packaged in FOND-SAT. The version of MiniSAT form has been obtained (and compiled) from [master-keying /
minisat](https://github.com/master-keying/minisat/), which is a much more maintained repo than the one in the [original site](http://minisat.se/).

To add a new solver:

1. Add a new choice for option `--solver`.
2. Modify `main.py` to account for the new solver and define the corresponding `command` for it.
3. Provide the adequate `parseOutput()` function in `src/CNF.py` to parse the output of the solver used.

## Running the planner

The general execution is as follows:

```shell
$ python src/main.py [OPTIONS] path_domain path_instance
```

The path to the domain and the task must be included. For a list of options available use `-h`:

```shell
$ python src/main.py -h
usage: main.py [-h] [--solver {minisat,glucose}] [--time-limit TIME_LIMIT] [--mem-limit MEM_LIMIT] [--strong]
               [--start START] [--inc INC] [--end END] [--gen-info] [--show-policy] [--draw-policy] [--name-tmp NAME_TMP]
               [--tmp]
               path_domain path_instance
```

An easy/quick solvable run would be:

```shell
$ python src/main.py F-domains/islands/domain.pddl F-domains/islands/p03.pddl --solver glucose --tmp
```

This would run the solver for the task 03 of the Islands domain, using Glucose as SAT solver and leaving behind the temporary files.

A more challenging ask (taking around 500secs/8min) would be:

```shell
$ python src/main.py F-domains/islands/domain.pddl F-domains/islands/p47.pddl --solver glucose

....
s SATISFIABLE
SAT
Done solver. Round time: 12.916486
Cumulated solver time: 39.73258573602652
PLANFOUND!
Elapsed total time (s): 501.258223
Elapsed initialisation time (s): 6.977923776998068
Elapsed grounding time (s): 442.8925411340024
Elapsed grounding time (s): [22.89034552499652, 30.071642617011094, 44.89836094499333, 47.62225245599984, 57.385479142991244, 62.35428485700686, 73.23855525600084, 104.43162033500266]
Elapsed solver time (s): 39.732586
Elapsed solver time (s): [2.222133905001101, 1.909849037998356, 3.3073226740089012, 3.8610715660033748, 3.949099778008531, 4.780444735995843, 6.786178249007207, 12.916485790003208]
Elapsed result output time (s): 0.00218252201739233
Elapsed result output time (s): [0.00031191699963528663, 0.0002279759937664494, 0.0005103060102555901, 0.0004846640076721087, 0.0002168909995816648, 0.00019257400708738714, 0.00023819399939384311]
Looking for strong plans: False
Fair actions: True
Done
```

It found a policy with 10 states. So, if we directly start with 10 states we should get a single SAT iteration that is shorter:

```shell
$ python src/main.py F-domains/islands/domain.pddl F-domains/islands/p03.pddl --start 10 --solver glucose

...

s SATISFIABLE
SAT
Done solver. Round time: 17.831398
Cumulated solver time: 17.831397656991612
PLANFOUND!
Elapsed total time (s): 157.229258
Elapsed initialisation time (s): 5.736119034991134
Elapsed grounding time (s): 115.8947535949992
Elapsed grounding time (s): [115.8947535949992]
Elapsed solver time (s): 17.831398
Elapsed solver time (s): [17.831397656991612]
Elapsed result output time (s): 0
Elapsed result output time (s): []
Looking for strong plans: False
Fair actions: True
Done
```

Let's try the same but with MiniSAT:

```shell
$ python src/main.py F-domains/islands/domain.pddl F-domains/islands/p03.pddl --start 10 --solver glucose

...

SATISFIABLE
Done solver. Round time: 91.031980
Cumulated solver time: 91.03197950900358
PLANFOUND!
Elapsed total time (s): 228.864515
Elapsed initialisation time (s): 5.941680243995506
Elapsed grounding time (s): 112.23787351899955
Elapsed grounding time (s): [112.23787351899955]
Elapsed solver time (s): 91.031980
Elapsed solver time (s): [91.03197950900358]
Elapsed result output time (s): 0
Elapsed result output time (s): []
Looking for strong plans: False
Fair actions: True
Done
```

As one can see, using glucose seems to be much faster than using minisat.

Finally, if we tell FOND-SAT to try between 6 and 8 states, the planner will not find any solution;

```shell
$ python src/main.py F-domains/islands/domain.pddl F-domains/islands/p03.pddl --start 6 --end 8

...

```





## Interpreting the policy

The policy displayed has 4 sections:

* `Atom (CS)`: For each controller state `CS` it prints out which atoms are true.
* `(CS, Action with arguments)`: For each controller state `CS`, it prints what actions are applied in it.
* `(CS, Action name, CS)`: For each controller state `CS`, it prints the action applied in that state (without arguments, for action with arguments check second section) and successor `CS`.
* `(CS1, CS2)`: The controller can evolve from `CS1` to `CS`. In other words, the action applied in `CS1` may lead to controller state `CS2`.

## Dual FOND planning

The paper talks about what we call *Dual FOND planning*. Dual FOND problems are those in which some actions are *fair* and some are *unfair*. To set some action (or actions) as unfair, add `_unfair_` as the last part of the action name in the *pddl* file. The planner will then set this action as unfair.