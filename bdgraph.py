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

import sys, os, time
from classes.graph import Graph

def run(input_fn, output_fn):
    ''' string, string -> none

    read in the input file, create the graph, handle user options, run graph
    operations, and write output
    '''

    # read contents into list
    with open(input_fn, 'r') as input_fd:
        content = [line.strip() for line in input_fd.readlines()]

        # remove comments and blank lines
        content = [line for line in content if line and line[0] != '#']

    graph = Graph(content)
    graph.handle_options()
    graph.transitive_reduction()
    graph.compress_representation()
    graph.write_dot(output_fn)

    # rewrite the input file?
    options = [x.label for x in graph.graph_options]
    if 'cleanup' in options:
        graph.write_config(input_fn)

    del graph

# MAIN
def main(argv):
    ''' list -> none

    handles IO and parses user options '''

    arg_counter = 0
    monitor = False
    input_fn, output_fn = '', ''

    # parse commandline arguments
    if len(argv) > 0:

        if str(argv[arg_counter]) == '-m':
            monitor = True
            arg_counter += 1

        input_fn = str(argv[arg_counter])
        arg_counter += 1

        if not os.path.exists(input_fn):
            print('error: file "' + input_fn + '" does not exist')
            sys.exit(1)

        # output file name is input + .dot if not provided
        try:
            output_fn = str(argv[arg_counter])

        except IndexError:
            output_fn = input_fn + '.dot'

    else:
        print('usage: python3 bdgraph.py [-m] input_file [output_file]')
        sys.exit(1)

    if monitor:
        last_change = os.stat(input_fn).st_mtime

        # poll for changes to the input file
        while True:
            current = os.stat(input_fn).st_mtime

            if current != last_change:
                run(input_fn, output_fn)
                last_change = os.stat(input_fn).st_mtime

            time.sleep(0.25)

    else:
        run(input_fn, output_fn)

if __name__ == '__main__':
    main(sys.argv[1:])
