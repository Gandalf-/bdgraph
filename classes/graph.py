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

import sys, copy
from classes.node import Node, Node_Option


class Graph(object):
    ''' Class

    The Graph class encapsulates everything about the input file, internal
    representation, and handles parsing options, and writing output files '''

    def __init__(self, contents, logging=False):
        ''' list of strings, bool -> Graph

        construct a Graph object, handles parsing the input file to create
        internal representation and options list '''

        self.contents = contents        # list of string
        self.nodes = []                 # list of Node
        self.graph_options = []         # list of Graph_Option
        self.logging = logging          # bool

        mode = 'definition'             # default parsing state

        for line in contents:
            # state machine, determine state and then take appropriate action
            if line == 'options':
                mode = 'options'
                continue

            elif line == 'dependencies':
                mode = 'dependencies'
                continue

            # actions, we know our state so do something with the line
            if mode == 'definition':
                self.log('definition: ' + line)
                try:
                    self.nodes.append(Node(line, logging=self.logging))

                except ValueError:
                    print('error: unrecongized syntax: ' + line)
                    sys.exit(1)

            elif mode == 'options':
                self.log('options: ' + line)
                for option in line.split(' '):
                    try:
                        self.graph_options.append(Graph_Option(option))

                    except SyntaxError:
                        print('error: unrecongized option: ' + option)
                        sys.exit(1)

            elif mode == 'dependencies':
                self.log('dependencies: ' + line)
                try:
                    self.update_dependencies(line)

                except SyntaxError:
                    print('error: unrecongized dependency type: ' + line)
                    sys.exit(1)

                except ValueError:
                    print('error: unrecongized node reference: ' + line)
                    sys.exit(1)

    def show(self):
        ''' none -> IO

        prints a representation of the graph to the console '''

        options = ' '.join([x.label for x in self.graph_options])
        print('graph options: ' + options)
        print()

        for node in self.nodes:
            node.show()

    def write_dot(self, file_name):
        ''' string -> IO

        writes the graph to a file in graphviz dot format. nodes write
        themselves and handle their own options '''

        options = [x.label for x in self.graph_options]

        with open(file_name, 'w') as fd:
            # header
            fd.write('digraph g{\n')
            fd.write('  rankdir=LR;\n')
            fd.write('  ratio=fill;\n')
            fd.write('  node [style=filled];\n')
            fd.write('  overlap=false;\n')

            if 'circular' in options:
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
            fd.write('  ' + ' '.join(
                [option.label for option in self.graph_options]))
            fd.write('\n\n')

            # dependencies
            fd.write('dependencies\n')
            for node in self.nodes:
                node.write_dependencies(fd)


    def update_dependencies(self, line):
        ''' string -> none | SyntaxError, ValueError

        update the Nodes referenced in the dependency line provided.
        inputs are in the form:
            1,2,3 -> 4,5,6
            1,2,3 <- 4,5,6

        unrecongized dependency type throws a SyntaxError
        unrecongized node references through AttributeError '''

        # determine dependency type
        require = line.split('<-')
        allow   = line.split('->')

        # 1,2,3 <- 4,5,6
        if len(require) > 1:
            requiring_nodes = require[0].split(',')
            providing_nodes = require[1].split(',')

        # 1,2,3 -> 4,5,6
        elif len(allow) > 1:
            providing_nodes = allow[0].split(',')
            requiring_nodes = allow[1].split(',')

        # unrecongized dependency type
        else:
            raise SyntaxError

        # clean up labels
        providing_nodes = [x.strip() for x in providing_nodes]
        requiring_nodes = [x.strip() for x in requiring_nodes]

        # update requirements and provisions for each node
        for r_label in requiring_nodes:
            requiring_node = self.find_node(r_label)

            for p_label in providing_nodes:
                providing_node = self.find_node(p_label)

                requiring_node.add_require(providing_node)
                providing_node.add_provide(requiring_node)

    def find_node(self, label):
        ''' string -> Node | ValueError

        search through the graph's nodes for the node with the same label as
        the one provided '''

        for node in self.nodes:
            if node.label == label:
                self.log('found: ' + label)
                return node

        self.log('failed to find: ' + label)
        raise ValueError

    def find_most(self, mode):
        ''' string -> Node

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
                    except ValueError: pass

                # remove inverses from real graph
                for inverse in real_node.provides:
                    try:
                        inverse.requires.remove(real_node)
                    except ValueError: pass

            # the most representative relationship is a requirement
            else:
                copy_node = most_require
                real_node = self.find_node(copy_node.label)

                # remove inverses and node from copied graph
                for inverse in copy_node.requires:
                    try:
                        inverse.provides.remove(copy_node)
                        copy_node.requires.remove(inverse)
                    except ValueError: pass

                # remove inverses from real graph
                for inverse in real_node.requires:
                    try:
                        inverse.provides.remove(real_node)
                    except ValueError: pass

    def handle_options(self):
        ''' string -> none

        handles non-user specified options, such as color_next and cleanup. '''

        options = [x.label for x in self.graph_options]

        if 'remove_marked' in options:
            to_remove = []

            # find all nodes to be deleted
            for node in self.nodes:
                if node.node_option and node.node_option.type == 'remove_marked':
                    to_remove.append(node)

            # remove all marked nodes from the tree and other nodes
            for node_to_remove in to_remove:
                self.nodes.remove(node_to_remove)

                for node in self.nodes:
                    if node_to_remove in node.requires:
                        node.requires.remove(node_to_remove)

                    if node_to_remove in node.provides:
                        node.provides.remove(node_to_remove)

        if 'color_next' in options:
            for node in self.nodes:

                # all requiring nodes have the complete flag? this is also true
                # when the current node doesn't have any requiring nodes
                requirements_satisfied = True

                for req_node in node.requires:
                    if not req_node.node_option:
                        requirements_satisfied = False

                    elif req_node.node_option.type != 'color_complete':
                        requirements_satisfied = False

                if (not node.node_option) and requirements_satisfied:
                    node.node_option = Node_Option('_')

    def transitive_reduction(self):
        ''' none -> none

        for all non-immediate children of each node, if that child has a
        relationship with the current node, remove it. this removes redundant
        transitive relationships

            1 -> 2,3     becomes    1 -> 2,3
            1 -> 3

        cycles are currently not supported and are detected by
        sys.getrecursionlimit() exceeding the number of nodes in the graph '''

        # limit recursion depth to catch cycles in the graph
        old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(len(self.nodes) + 5)

        try:
            # apply the transitive_reduction algorithm to every node
            for node in self.nodes:
                for child in node.provides:
                    child.transitive_reduction(node, skip=True)

        except RuntimeError:
            print('warn: cycle detected, not computing transitive reductions')

        finally:
            sys.setrecursionlimit(old_limit)

    def log(self, comment):
        ''' string -> maybe IO

        debugging function, only print if global `logging` is true '''

        if self.logging:
            print(comment)

class Graph_Option:
    ''' Class

    Encapsulates the graph level options that are available for nodes to use.
    For a Node_Option to be valid, it must exist at the graph level as well '''

    def __init__(self, line):
        ''' string -> Graph_Option | SyntaxError

        raises SyntaxError if an invalid option is provided '''

        options = [
                'color_complete', 'color_next', 'cleanup', 'color_urgent',
                'circular', 'publish', 'remove_marked',
                ]

        if line in options:
            self.label = line
        else:
            raise SyntaxError
