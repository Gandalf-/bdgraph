#!/usr/bin/python3

import bdgraph


class GraphOption:
    ''' Class

    Encapsulates the graph level options that are available for nodes to use.
    For a NodeOption to be valid, it must exist at the graph level as well '''

    def __init__(self, line):
        ''' string -> Graph_Option | BdgraphSyntaxError

        raises SyntaxError if an invalid option is provided '''

        if line in bdgraph.Option.options:
            self.label = line
        else:
            raise bdgraph.BdgraphSyntaxError
