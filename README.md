# FOND-SAT
FOND solver based on SAT

## Files
- *F-domains/* contains the FOND domains used
- *src/* contains the code for the solver, and a compiled version of Minisat

## Example usage (basic)
From the *src/* directory run the following command:
> python main.py ../F-domains/islands/domain.pddl ../F-domains/islands/p03.pddl

This would run the solver for the task 03 of the islands domain.