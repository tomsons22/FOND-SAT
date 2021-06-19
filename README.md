# FOND-SAT

FOND solver based on SAT, as per the following paper:

* Tomas Geffner, Hector Geffner: [Compact Policies for Fully Observable Non-Deterministic Planning as SAT](https://arxiv.org/pdf/1806.09455.pdf). ICAPS 2018: 88-96

## Setup

### Files

- `F-domains/*` contains the FOND domains used
- `src/*` contains the code for the solver, and a pre-compiled version of Minisat

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

## Example usage

The general execution is as follows:

```shell
$ python src/main.py [OPTIONS] path_domain path_instance
```

The path to the domain and the task must be included. For example:

```shell
$ python src/main.py F-domains/islands/domain.pddl F-domains/islands/p03.pddl --solver glucose --tmp
```

This would run the solver for the task 03 of the Islands domain, using Glucose as SAT solver and leaving behind the temporary files.

## Other options (arguments when calling)

```shell
  -h, --help            show this help message and exit
  --solver {minisat,glucose}
                        SAT solver to use - (default: minisat)
  --time_limit TIME_LIMIT
                        Time limit (int) for solver in seconds (default: 3600).
  --mem_limit MEM_LIMIT
                        Memory limit (int) for solver in MB (default: 4096)
  --strong              Search for strong solutions (instead of default strong cyclic solutions) - (default: False)
  --start START         Size of the policy to start trying (default: 1)
  --inc INC             Increments in controller size per step. By default the planner looks for a solution of size *2*, if it does not find one it looks for
                        a solution of size *3*, and so on. If inc is set to *i*, the planner looks for a solution of size *2*, if it does not find one it
                        looks for a solution of size *2+i*, and so on (default: 1)
  --gen-info            Show info about SAT formula generation (default: False)
  --show-policy         Show final policy, if found (default: False)
  --draw-policy         Draw final policy (controller), if found (default: False)
  --name-tmp NAME_TMP   Name for temporary folder; generally erased at the end.
  --tmp                 Do not clean temporary files created (default: False)
```


## Interpreting the policy

The policy displayed has 4 sections:

- **Atom (CS):** For each Controller State (CS) it prints out which atoms are true.
- **(CS, Action with arguments):** For each CS it prints what actions are applied in it.
- **(CS, Action name, CS):** For each CS it prints the action applied in that state (without arguments, for action with arguments check second section) and successor CS.
- **(CS, CS):** *(cs1, cs2)* means that the controller can go from *cs1* to *cs2*. In other words, the action applied in *cs1* may lead to *cs2*. 


## Dual FOND planning

The paper talks about what we call *Dual FOND planning*. Dual FOND problems are those in which some actions are *fair* and some are *unfair*. To set some action (or actions) as unfair, add `_unfair_` as the last part of the action name in the *pddl* file. The planner will then set this action as unfair.

## Note
The solver uses the parser from [PRP](https://bitbucket.org/haz/planner-for-relevant-policies/wiki/Home)
