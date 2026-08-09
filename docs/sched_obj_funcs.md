# Constraint Satisfaction Problems (CSP)

A CSP consists of:
- Variables
- A domain of possible values for each variable
- Constraints that restrict which combinations of values are allowed

The goal is to assign values to every variable while satisfying all hard constraints.

## Backtracking Search
- Assign variables one at a time.
- If an assignment eventually creates an impossible situation, undo it and try another value.
- Basic backtracking can become expensive because it may discover failure very late.

## Forward Checking
- After assigning a variable, remove values from neighboring variables that can no longer work.
- Helps detect impossible branches earlier instead of waiting until several more assignments have been made.

### Most-Constrained Variable
Also called the **Minimum Remaining Values (MRV)** heuristic.

- Choose the variable with the fewest legal values remaining.
- Idea: **fail early**.
- If something is going to become impossible, discover it now instead of later.
- This can greatly reduce unnecessary search.

### Least-Constraining Value
- Once a variable has been selected, prefer the value that eliminates the fewest options from neighboring variables.
- Idea: leave the rest of the problem as flexible as possible.

These two heuristics work together:

1. Pick the variable most likely to cause trouble.
2. Give it the value least likely to cause trouble for everything else.

## Arc Consistency / AC-3
- A stronger form of domain elimination.
- Looks at pairs of connected variables.
- Removes a value from one variable's domain if there is no compatible value remaining in the neighboring variable's domain.
- Continues propagating these removals through the constraint graph until no more values can be eliminated.
- If a domain becomes empty, the current state cannot possibly lead to a valid solution.

AC-3 does not necessarily solve the CSP by itself. It reduces the search space so that later search has much less work to do.

# Search Strategies

## Greedy Search
- Makes the choice that looks best right now.
- Fast and simple.
- Can make an early decision that later produces a poor overall solution.

## Beam Search
- Instead of keeping only one partial solution, keep the best `k` candidates at each stage.
- Provides more exploration than greedy search without keeping every possible state.
- The evaluation function needs to provide useful information while the schedule is still incomplete.
- If quality can only be calculated after the entire schedule is finished, beam search has little information for deciding which partial schedules to keep.

## Local Search
- Usually starts with a **complete solution** rather than constructing one variable at a time.
- Makes small changes to the current solution and compares their scores.
- Exploits **locality**: changing one part of a schedule often affects only a limited number of scoring rules.

Example:

Current schedule
→ move one event
→ calculate new score
→ keep the move if it improves the schedule

### Local Optima
Local search can become stuck at a **local optimum**.

A local optimum is a schedule where:
- every nearby change looks worse,
- but a much better schedule exists somewhere farther away.

Ways algorithms try to escape include:
- randomness,
- occasionally accepting worse moves,
- changing several variables/events at once,
- remembering recently explored moves.

Simulated Annealing and Tabu Search are examples of methods designed partly to deal with this problem.


# University Course Scheduling

University course scheduling is usually a **multi-objective optimization problem**.

A schedule should be judged by many independent objectives rather than one single rule.

Examples:
- preferred times,
- preferred days,
- spacing between classes,
- faculty preferences,
- student conflicts,
- room preferences,
- workload distribution.

## Hard Constraints
- Determine whether a schedule is valid.
- A hard constraint cannot be violated.

Examples:
- No overlapping events.
- Required classes must be scheduled.
- A professor cannot teach two classes simultaneously.
- A room cannot contain two classes at the same time.

## Soft Constraints
- Determine the **quality** of an otherwise valid schedule.
- Violating one does not invalidate the schedule.
- Instead, the violation creates a reward loss or penalty.

Example:

Preferred time satisfied: +10  
Preferred spacing satisfied: +5  
Unwanted evening event: -8

## Objective / Scoring Function
The scoring function combines many independent objectives into one measure of schedule quality.

The search algorithm itself does not understand what a "good" schedule means.

It only knows:

`Schedule A score > Schedule B score`

Therefore:

**The scoring function defines what "better" means.**

Some objectives may also be much more important than others, so scoring rules may need different weights or priorities.


# Vehicle Routing Objective Functions

Vehicle Routing Problems (VRP) ask how vehicles should visit a set of locations while satisfying constraints.

A common objective is:

**Minimize total travel distance or cost.**

Possible constraints include:
- Every customer must be visited.
- Vehicle capacity cannot be exceeded.
- Vehicles must begin/end at the depot.
- Time windows may need to be respected.

## Exact Algorithms
- Attempt to find and prove the globally optimal solution.
- Useful for smaller problems.
- Become increasingly expensive as the number of possible combinations grows.

## Heuristics and Metaheuristics
- Usually do not guarantee the absolute best solution.
- Trade guaranteed optimality for much faster computation.
- Can often produce very good solutions to problems that are too large for exhaustive search.

A common approach is:

1. Build a reasonable solution.
2. Make a small modification.
3. Evaluate the objective function.
4. Keep useful improvements.
5. Repeat.

This is the basic idea behind **local search**.


# Timetabling Optimization

Timetabling problems have extremely large search spaces, so many systems use heuristics or metaheuristics instead of attempting to examine every possible timetable.

## Common Metaheuristics

### Simulated Annealing
- Usually works with one current solution.
- Sometimes deliberately accepts a worse solution.
- This allows it to escape local optima.

### Tabu Search
- Performs local search while remembering recently visited moves/states.
- The "tabu list" prevents the algorithm from immediately returning to choices it recently made.
- Helps prevent cycling and encourages exploration.

### Genetic Algorithms
- Maintain a population of candidate solutions.
- Better solutions are selected to produce new solutions.
- Uses ideas such as selection, crossover, and mutation.

### Particle Swarm Optimization
- Uses a population of candidate solutions.
- Candidates are influenced by their own best discoveries and by good solutions discovered by the group.

### Ant Colony Optimization
- Inspired by ants reinforcing useful paths with pheromones.
- Good choices become increasingly likely to be selected as the search progresses.

### Artificial Bee Colony
- Inspired by bees exploring potential food locations.
- Some candidates explore new areas while others concentrate on promising solutions.


# Exploration vs. Exploitation

Optimization algorithms must balance two competing behaviors.

## Exploitation

You think treasure is under one tree, so you carefully search around that tree.

In optimization:
- Search near an already promising solution.
- Try to squeeze additional improvements from it.
- Strong exploitation improves good solutions quickly.

Too much exploitation can cause the algorithm to become stuck at a local optimum.

## Exploration

You think:

> "Maybe the treasure isn't under this tree at all."

So you search other parts of the park.

In optimization:
- Investigate very different solutions.
- Discover unexplored areas of the search space.
- Helps escape local optima.

Too much exploration wastes time jumping around without improving promising solutions.

Good optimization methods balance both:

**explore enough to discover better regions, then exploit those regions to refine the solution.**


# No Free Lunch Principle

There is no universally best optimization algorithm.

An algorithm that performs extremely well on one scheduling problem may perform poorly on another.

For example:
- Genetic Algorithms may work well for one timetable structure.
- Simulated Annealing may perform better for another.
- Local Search may be extremely effective when good neighboring moves are easy to define.

Therefore, the quality of the algorithm depends partly on the structure of the specific scheduling problem.

This is another reason the scoring system should be separate from the search algorithm:

**Different search algorithms can use the same definition of schedule quality.**