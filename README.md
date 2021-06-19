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

### SAT solver

For easiness to use, this includes a pre-compiled version of Minisat. This pre-compiled version does not allow the use of time/memory limits. If you want to try another SAT solver (or use time/memory contraints), you should re-define the assignment to variable `command` in file `src/main.py` and provide the adequate `parseOutput()` function to parse the output of the solver used.

By default, the assginment to the variable is as follows (in `src/main.py`):

    command = './minisat {} {}'.format(name_formula_file, name_output_satsolver)

You need to adapt it to the corresponding SAT solver, for example to use Minisat with time/memory constraints (commented out in the code):

    command = '/path/to/SATsolver/minisat -mem-lim={} -cpu-lim={} {} {}'.format(mem_limit, time_for_sat, name_formula_file, name_output_satsolver)

Then, you need to adapt function `parseOutput(...)` in `src/CNF.py`, to parse the output of your SAT solver  (currently works for versions of Minisat).

**RECOMMENDATION:** install a version of Minisat from *http://minisat.se/*, comment line 117 of *main.py* and uncomment line 118. Using another version of Minisat will allow the use of time/memory constraints (newer version is also faster), and does not require the modification of *parseOutput(...)*. The results shown in the paper were obtained using a newer version of Minisat, not the pre-compiled one.



## Example usage (basic)

From the `src/*` directory run the following command:


```shell
$ python main.py ../F-domains/islands/domain.pddl ../F-domains/islands/p03.pddl
```

This would run the solver for the task 03 of the Islands domain. The path to the domain and the task must be included.

## Other options (arguments when calling)

```shell
  -h, --help            show this help message and exit
  --time_limit TIME_LIMIT
                        Time limit (int) for solver in seconds (default:
                        3600).
  --mem_limit MEM_LIMIT
                        Memory limit (int) for solver in MB (default: 4096)
  --name_temp NAME_TEMP
                        Name for temp files; erased after solver is done
                        (default: temp)
  --strong              Search for strong solutions (instead of default strong
                        cyclic solutions) - (default: False)
  --start START         Size of the policy to start trying (default: 1)
  --inc INC             Increments in controller size per step. By default the
                        planner looks for a solution of size *2*, if it does
                        not find one it looks for a solution of size *3*, and
                        so on. If inc is set to *i*, the planner looks for a
                        solution of size *2*, if it does not find one it looks
                        for a solution of size *2+i*, and so on (default: 1)
  --gen-info            Show info about SAT formula generation (default:
                        False)
  --show-policy         Show final policy, if found (default: False)
  --draw-policy         Draw final policy (controller), if found (default:
                        False)
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
