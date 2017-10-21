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

import sys
import copy
import bdgraph


class Graph(object):
    ''' Class

    The Graph class encapsulates everything about the input file, internal
    representation, and handles parsing options, and writing output files '''

    def __init__(self, contents, logging=False):
        ''' string, bool -> Graph

        construct a Graph object, handles parsing the input file to create
        internal representation and options list '''

        # clean input, convert to list of lines, remove comments
        contents = [line.strip() for line in contents.split('\n')]
        contents = [line for line in contents if line and line[0] != '#']

        self.contents = contents        # list of string
        self.nodes = []                 # list of Node
        self.graph_options = []         # list of Graph_Option
        self.option_strings = []        # list of string
        self.logging = logging          # bool

        mode = 'definition'             # default parsing state

        for line in contents:
            # state machine, determine state and then take appropriate action
            if line == 'options':
                mode = line
                continue

            elif line == 'dependencies':
                mode = line
                continue

            # actions, we know our state so do something with the line
            if mode == 'definition':
                self.log('definition: ' + line)
                try:
                    self.nodes.append(bdgraph.Node(line, logging=self.logging))

                except bdgraph.BdgraphNodeNotFound:
                    raise bdgraph.BdgraphRuntimeError(
                        'error: unrecongized syntax: ' + line)

            elif mode == 'options':
                self.log('options: ' + line)
                for option in line.split(' '):
                    try:
                        self.graph_options.append(bdgraph.GraphOption(option))

                    except bdgraph.BdgraphSyntaxError:
                        raise bdgraph.BdgraphRuntimeError(
                            'error: unrecongized option: ' + option)

            elif mode == 'dependencies':
                self.log('dependencies: ' + line)
                try:
                    self.update_dependencies(line)

                except bdgraph.BdgraphSyntaxError:
                    raise bdgraph.BdgraphRuntimeError(
                        'error: unrecongized dependency type: ' + line)

                except bdgraph.BdgraphNodeNotFound:
                    raise bdgraph.BdgraphRuntimeError(
                        'error: unrecongized node reference: ' + line)

        self.options = [x.label for x in self.graph_options]

    def __del__(self):
        ''' '''
        bdgraph.node.Node.node_counter = 1

    def show(self):
        ''' none -> IO

        prints a representation of the graph to the console '''

        options = ' '.join(self.option_strings)
        print('graph options: ' + options)
        print()

        for node in self.nodes:
            node.show()

    def write_dot(self, file_name):
        ''' string -> IO

        writes the graph to a file in graphviz dot format. nodes write
        themselves and handle their own options '''

        with open(file_name, 'w') as fd:
            # header
            fd.write('digraph g{\n'
                     '  rankdir=LR;\n'
                     '  ratio=fill;\n'
                     '  node [style=filled];\n'
                     '  overlap=false;\n')

            if bdgraph.Option.Circular in self.option_strings:
                fd.write('  layout=neato;\n')

            # graph contents
            for node in self.nodes:
                node.write_dot(fd, self.graph_options)

            # footer
            fd.write('}\n')

    def write_config(self, file_name):
        ''' string -> IO

        rewrites the input file. this reformats definitions, options, and
        dependencies. it's also run after the Graph.compress_representation()
        function so the dependency description is minimal '''

        with open(file_name, 'w') as fd:
            # header
            fd.write('#!/usr/local/bin/bdgraph\n')
            fd.write('# 1 <- 2,3 => 1 requires 2 and 3 \n')
            fd.write('# 2 -> 3,4 => 2 provides 3 and 4 \n')
            fd.write('\n')

            # definitions
            for node in self.nodes:
                node.write_definition(fd)
            fd.write('\n')

            # options
            fd.write('options\n')
            fd.write('  ' + ' '.join(self.option_strings))
            fd.write('\n\n')

            # dependencies
            fd.write('dependencies\n')
            for node in self.nodes:
                node.write_dependencies(fd)

    def update_dependencies(self, line):
        ''' string -> none | BdgraphSyntaxError, BdgraphNodeNotFound

        update the Nodes referenced in the dependency line provided.
        inputs are in the form:
            1,2,3 -> 4,5,6
            1,2,3 <- 4,5,6

        unrecongized dependency type throws a SyntaxError
        unrecongized node references through AttributeError '''

        left, right = 0, 1

        # determine dependency type
        require = line.split('<-')
        allow = line.split('->')

        # 1,2,3 <- 4,5,6
        if len(require) > 1:
            requiring_nodes = require[left].split(',')
            providing_nodes = require[right].split(',')

        # 1,2,3 -> 4,5,6
        elif len(allow) > 1:
            providing_nodes = allow[left].split(',')
            requiring_nodes = allow[right].split(',')

        # unrecongized dependency type
        else:
            raise bdgraph.BdgraphSyntaxError

        # clean up labels
        providing_nodes = [x.strip() for x in providing_nodes]
        requiring_nodes = [x.strip() for x in requiring_nodes]

        # for each node
        for requiring_label in requiring_nodes:
            requiring_node = self.find_node(requiring_label)

            for providing_label in providing_nodes:
                providing_node = self.find_node(providing_label)

                # update requirements and provisions
                requiring_node.add_require(providing_node)
                providing_node.add_provide(requiring_node)

    def find_node(self, label):
        ''' string -> Node | BdgraphNodeNotFound

        search through the graph's nodes for the node with the same label as
        the one provided '''

        for node in self.nodes:
            if node.label == label:
                self.log('found: ' + label)
                return node

        self.log('failed to find: ' + label)
        raise bdgraph.BdgraphNodeNotFound

    def find_most(self, mode):
        ''' ('provide' | 'require') -> Node

        search through the nodes for the one that requires the most nodes or
        provides to the most nodes, depending on mode. used by
        Graph.compress_representation() '''

        highest = self.nodes[0]

        for node in self.nodes:
            if mode == 'provide':
                if len(node.provides) > len(highest.provides):
                    highest = node

            elif mode == 'require':
                if len(node.requires) > len(highest.requires):
                    highest = node

        return highest

    def compress_representation(self):
        ''' none -> none
        analyzes relationships between nodes to find an equivalent graph of
        minimum size (# edges)

        we use a copy of the graph to search for the current most
        representative node. this is the node with the highest number of
        provides or requires.

        on the original graph, we remove all the inverses of the relationship
        we just found. on the copy, we remove the relationship we found.

            1 <- 2,3    1 <- 2,3    # found relationships
            2 -> 1      2 -> 1      # relationship inverses
            3 -> 1      3 -> 1      # relationship inverses
            4 -> 5      4 -> 5

        for example, in the graph above, we find 1.requires as the most
        representative node. next, we make a copy of the graph so we can keep
        track of relationships we remove. in the copied graph, we remove both
        found node's relationships and their inverses. in the original graph,
        we only remove the inverses

            1 <- 2,3
            4 -> 5      4 -> 5

        this process continues until the copied graph is empty of relationships
        '''

        # copy the graph so we can remove the most representative nodes as
        # they're found. this way they won't be found on the next iteration
        graph_copy = copy.deepcopy(self)

        while True:
            most_provide = graph_copy.find_most('provide')
            most_require = graph_copy.find_most('require')

            num_provides = len(most_provide.provides)
            num_requires = len(most_require.requires)

            # there are no more relationships in the copied graph, stop
            if num_provides == num_requires == 0:
                break

            # the most representative relationship is a provision
            elif num_provides > num_requires:

                copy_node = most_provide
                real_node = self.find_node(copy_node.label)

                # inverse of provide is require
                for inverse in copy_node.provides:
                    try:
                        inverse.requires.remove(copy_node)
                        copy_node.provides.remove(inverse)
                    except ValueError:
                        pass

                # remove inverses from real graph
                for inverse in real_node.provides:
                    try:
                        inverse.requires.remove(real_node)
                    except ValueError:
                        pass

            # the most representative relationship is a requirement
            else:
                copy_node = most_require
                real_node = self.find_node(copy_node.label)

                # remove inverses and node from copied graph
                for inverse in copy_node.requires:
                    try:
                        inverse.provides.remove(copy_node)
                        copy_node.requires.remove(inverse)
                    except ValueError:
                        pass

                # remove inverses from real graph
                for inverse in real_node.requires:
                    try:
                        inverse.provides.remove(real_node)
                    except ValueError:
                        pass

    def handle_options(self):
        ''' string -> none

        handles non-user specified options, such as color_next and cleanup. '''

        if bdgraph.Option.Remove in self.option_strings:
            to_remove = []

            # find all nodes to be deleted
            for node in self.nodes:
                try:
                    if node.node_option.type == bdgraph.Option.Remove:
                        to_remove.append(node)
                except AttributeError:
                    pass

            # remove all marked nodes from the tree and other nodes
            for node_to_remove in to_remove:
                self.nodes.remove(node_to_remove)

                for node in self.nodes:
                    if node_to_remove in node.requires:
                        node.requires.remove(node_to_remove)

                    if node_to_remove in node.provides:
                        node.provides.remove(node_to_remove)

        if bdgraph.Option.Next in self.option_strings:
            for node in self.nodes:

                # all requiring nodes have the complete flag? this is also true
                # when the current node doesn't have any requiring nodes
                requirements_satisfied = True

                for req_node in node.requires:
                    if not req_node.node_option:
                        requirements_satisfied = False

                    elif req_node.node_option.type != bdgraph.Option.Complete:
                        requirements_satisfied = False

                if (not node.node_option) and requirements_satisfied:
                    node.node_option = bdgraph.NodeOption('_')

    def transitive_reduction(self):
        ''' none -> none

        for all non-immediate children of each node, if that child has a
        relationship with the current node, remove it. this removes redundant
        transitive relationships

            1 -> 2,3     becomes    1 -> 2,3
            1 -> 3

        cycles are currently not supported and are detected by
        sys.getrecursionlimit() exceeding the number of nodes in the graph '''

        if bdgraph.Option.NoReduce in self.option_strings:
            return

        # limit recursion depth to catch cycles in the graph, 5 is arbitrary
        old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(len(self.nodes) + 5)

        try:
            # apply the transitive_reduction algorithm to every node
            for node in self.nodes:
                for child in node.provides:
                    child.transitive_reduction(node, skip=True)

        except bdgraph.BdgraphGraphLoopDetected:
            print('warn: cycle detected, not computing transitive reductions')

        finally:
            sys.setrecursionlimit(old_limit)

    def log(self, comment):
        ''' string -> maybe IO

        debugging function, only print if global `logging` is true '''

        if self.logging:
            print(comment)
