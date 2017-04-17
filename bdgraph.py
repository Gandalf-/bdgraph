#!/usr/bin/python3
''' bdgraph.py

Author:
    Austin Voecks

Description:
    Reads an input markup file containing definitions, dependencies, and graph
    options, and writes a corresponding output graphviz dot file

Usage:
    python3 bdgraph.py input_file [output_file]
'''

import sys, os
from classes.graph import Graph

# MAIN
def main(argv):
    ''' list -> none
    handles IO '''

    input_fn,output_fn = '', ''

    # parse commandline arguments
    if len(argv) > 0:
        input_fn = str(argv[0])

        if not os.path.exists(input_fn):
            print('error: file "' + input_fn + '" does not exist')
            sys.exit(1)

        # output file name is input + .dot if not provided
        output_fn = str(argv[1]) if len(argv) > 1 else input_fn + '.dot'

    else:
        print('python bdgraph.py input_file [output_file]')
        sys.exit(1)

    # read contents into list
    with open(input_fn, 'r') as input_fd:
        content = [line.strip() for line in input_fd.readlines()]

        # remove comments and blank lines
        content = [line for line in content if line and line[0] != '#']

    graph = Graph(content, logging=True)
    graph.handle_options()
    graph.transitive_reduction()
    graph.compress_representation()
    graph.write_dot(output_fn)

    # rewrite the input file?
    options = [x.label for x in graph.graph_options]
    if 'cleanup' in options:
        graph.write_config(input_fn)

if __name__ == '__main__':
    main(sys.argv[1:])
