from __future__ import print_function

# Import Python wrapper for or-tools constraint solver.
from ortools.constraint_solver import pywrapcp

def main():
  # Create the solver.
  solver = pywrapcp.Solver('jobshop')

  machines_count = 1
  jobs_count = 3
  all_machines = range(0, machines_count)
  all_jobs = range(0, jobs_count)
  # Define data.
  # machines = [[0, 0, 0],
  #             [0, 2, 1],
  #             [1, 2]]

  machines = [[0, 0, 0],
              [0, 0, 0],
              [0, 0]]

  processing_times = [[3, 2, 2],
                      [2, 1, 4],
                      [4, 3]]


  # to add due date constraints, make job's last operation end before a certain time (EndBefore)
  # to add fixed schedule constraints, apppend some var like solver.FixedInterval(2, 3,'swimming')
  # Computes horizon.
  horizon = 0
  for i in all_jobs:
    horizon += sum(processing_times[i])
  horizon += horizon
  # Creates jobs.
  all_tasks = {}
  for i in all_jobs:
    for j in range(0, len(machines[i])):
      all_tasks[(i, j)] = solver.FixedDurationIntervalVar(0,
                                                          horizon,
                                                          processing_times[i][j],
                                                          False,
                                                          'Job_%i_%i' % (i, j))

  # Creates sequence variables and add disjuctive constraints.
  all_sequences = []
  all_machine_jobs = 0
  for i in all_machines:
    machines_jobs = []
    for j in all_jobs:
      for k in range(0, len(machines[j])):
        if machines[j][k] == i:
          machines_jobs.append(all_tasks[(j, k)])
    
    machines_jobs.append(solver.FixedInterval(2, 3,'swimming'))
    machines_jobs.append(solver.FixedInterval(6, 1,'piano'))
    #machines_jobs.append(solver.FixedInterval(10, 1,'sleep'))
    disj = solver.DisjunctiveConstraint(machines_jobs, 'machine %i' % i)
    all_sequences.append(disj.SequenceVar())
    solver.Add(disj)
    all_machine_jobs += len(machines_jobs)

  # Add conjunctive contraints.
  for i in all_jobs:
    for j in range(0, len(machines[i]) - 1):
      solver.Add(all_tasks[(i, j + 1)].StartsAfterEnd(all_tasks[(i, j)]))

  # Set the objective.
  obj_var = solver.Max([all_tasks[(i, len(machines[i])-1)].EndExpr()
                        for i in all_jobs])
  objective_monitor = solver.Minimize(obj_var, 1)
  # Create search phases.
  sequence_phase = solver.Phase([all_sequences[i] for i in all_machines],
                                solver.SEQUENCE_DEFAULT)
  vars_phase = solver.Phase([obj_var],
                            solver.CHOOSE_FIRST_UNBOUND,
                            solver.ASSIGN_MIN_VALUE)
  main_phase = solver.Compose([sequence_phase, vars_phase])
  # Create the solution collector.
  collector = solver.AllSolutionCollector()

  # Add the interesting variables to the SolutionCollector.
  collector.Add(all_sequences)
  collector.AddObjective(obj_var)

  for i in all_machines:
    sequence = all_sequences[i];
    sequence_count = sequence.Size();
    for j in range(0, sequence_count):
      t = sequence.Interval(j)
      collector.Add(t.StartExpr().Var())
      collector.Add(t.EndExpr().Var())
  # Solve the problem.
  disp_col_width = 10

  if solver.Solve(main_phase, [objective_monitor, collector]):
    print("\nOptimal Schedule Length:", collector.ObjectiveValue(0), "\n")
    sol_line = ""
    sol_line_tasks = ""
    print("Optimal Schedule", "\n")

    for i in all_machines:
      seq = all_sequences[i]
      sol_line += "Machine " + str(i) + ": "
      sol_line_tasks += "Machine " + str(i) + ": "
      sequence = collector.ForwardSequence(0, seq)
      seq_size = len(sequence)

      for j in range(0, seq_size):
        t = seq.Interval(sequence[j]);
         # Add spaces to output to align columns.
        sol_line_tasks +=  t.Name() + " " * (disp_col_width - len(t.Name()))

      for j in range(0, seq_size):
        t = seq.Interval(sequence[j]);
        sol_tmp = "[" + str(collector.Value(0, t.StartExpr().Var())) + ","
        sol_tmp += str(collector.Value(0, t.EndExpr().Var())) + "] "
        # Add spaces to output to align columns.
        sol_line += sol_tmp + " " * (disp_col_width - len(sol_tmp))

      sol_line += "\n"
      sol_line_tasks += "\n"

    print(sol_line_tasks)
    print("Time Intervals for Tasks\n")
    print(sol_line)

if __name__ == '__main__':
  main()