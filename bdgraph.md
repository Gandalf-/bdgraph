:projects:python:

# [[vfile:~/google_drive/code/python/bdgraph|directory]]

# todo 
  :todo:
  - [ ] add flag to enable/disable transitive reduction
  - [ ] testing
    - [ ] unit tests
    - [ ] integration tests

  - [ ] cyclic transitive reduction
  - [ ] release version

# notes

  ## general
    - bdgraph is a markup language parser for graphviz dot graphs. Its useful for
      describing the relationships between sequences of actions with
      requirements.
```
      1,2,3 -> 4,5        1,2,3 allow 4,5 to happen. 

      which is equivalent to

      4,5 <- 1,2,3        4,5 require 1,2,3 to happen.
```
    - Any number of items can be place on either side of the arrow. bdgraph reads
      in all the dependencies and requirements described in the input file,
      constructs an internal dependency graph, produces an output dot graph, and
      rewrite the input file to a miminal representation.

  ## Minimal Representation

    - Several representations exist for each dependency described in the input
      file. For instance
```
      1 <- 2
      1 <- 3

      is equivalent to 

      1 <- 2,3

      This becomes more complicated with chained relationships.

      1 -> 2,3
      2 -> 3,4,5
```
  ## Transitive Reduction
    - bdgraph can detect and remove redundant transitive relationships. For
      instance:
```
      1 -> 2,3
      2 -> 3
```
      the relationship 1 -> 3 is already preset through the transitive property
      and can be removed to clean up the graph and reduce clutter
