#!/usr/bin/python3
''' bdgraph.py
python bdgraph.py input_file [output_file]
'''

import sys, os, copy


# GLOBALS
logging = False


# HELPERS
def log(comment):
    ''' string -> maybe IO

    debugging function, only print if global `logging` is true
    '''
    if logging:
        print(comment)

def split_on_nearest_space(word, start):
    ''' string, int -> string

    searches left and right of the start point for a space and inserts a
    newline character there. this is useful when writing the dot file so that
    the bubbles aren't stretched out by long descriptions
    '''
    right = left = start

    while right < len(word) and left > 0:
        if word[right] == ' ':
            return word[:right] + '\\n' + word[right:]

        if word[left] == ' ':
            return word[:left] + '\\n' + word[left:]

        left = left - 1
        right = right + 1

    return word


# CLASSES
class Graph(object):
    ''' Class

    The Graph class encapsulates everything about the input file, internal
    representation, and handles parsing options, and writing output files
    '''
    def __init__(self, contents):
        ''' list of strings -> Graph

        construct a Graph object, handles parsing the input file to create
        internal representation and options list
        '''
        self.contents = contents        # list of string
        self.nodes = []                 # list of Node
        self.graph_options = []         # list of Graph_Option

        mode = 'definition'             # default parsing state

        for line in contents:
            # state machine, determine state and then take appropriate action
            if line == 'options':
                mode = 'options'
                continue

            elif line == 'dependencies':
                mode = 'dependencies'
                continue

            # actions
            if mode == 'definition':
                log('definition: ' + line)
                try:
                    self.nodes.append(Node(line))

                except ValueError:
                    print('error: unrecongized syntax: ' + line)
                    sys.exit(1)

            elif mode == 'options':
                log('options: ' + line)
                try:
                    self.graph_options.append(Graph_Option(line))

                except SyntaxError:
                    print('error: unrecongized option: ' + line)
                    sys.exit(1)

            elif mode == 'dependencies':
                log('dependencies: ' + line)
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

        prints a representation of the graph to the console
        '''
        options = ' '.join([x.label for x in self.graph_options])
        print('graph options: ' + options)

        for node in self.nodes:
            node.show()

    def write_dot(self, file_name):
        ''' string -> IO

        writes the graph to a file in graphviz dot format. nodes write
        themselves and handle their own options '''

        with open(file_name, 'w') as fd:
            # header
            fd.write('digraph g{\n')
            fd.write('  rankdir=LR;\n')
            fd.write('  ratio=fill;\n')
            fd.write('  node [style=filled];\n')

            # graph contents
            for node in self.nodes:
                node.write_dot(fd, [x.label for x in self.graph_options])

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
            fd.write('# 1,2,3 <- 4,5,6 == 1,2,3 each require 4,5,6\n')
            fd.write('# 1,2,3 -> 4,5,6 == 1,2,3 each allow 4,5,6\n')
            fd.write('\n')

            # definitions
            for node in self.nodes:
                node.write_definition(fd)
            fd.write('\n')

            # options
            fd.write('options\n')
            for option in self.graph_options:
                fd.write('  ' + option.label + '\n')
            fd.write('\n')

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
                log('found: ' + label)
                return node

        log('failed to find: ' + label)
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


class Node:
    '''
    '''
    node_counter = 1

    def __init__(self, label):
        ''' string -> Node | ValueError
        '''
        log('node ' + label)
        self.label = ''             # string
        self.description = ''       # string
        self.pretty_desc = ''       # string
        self.node_option = None     # Node_Option

        self.provides = []          # list of Node
        self.requires = []          # list of Node

        self.number = str(Node.node_counter)
        self.label, self.description = [x.strip() for x in label.split(':')]

        # break up description to multiple lines
        desc_len = len(self.description)
        if desc_len < 50:
            # break in half
            self.pretty_desc = split_on_nearest_space(
                    self.description, desc_len // 2)
        else:
            # break in thirds
            self.pretty_desc = split_on_nearest_space(
                    self.description, desc_len // 3)
            self.pretty_desc = split_on_nearest_space(
                    self.pretty_desc, 2 * (desc_len // 3))

        # check for options flags
        self.parse_options()

        # update node counter
        Node.node_counter += 1

    def show(self):
        '''
        '''
        print(self.number + ' : ' + self.description)
        if self.node_option:
            print('option: ' + self.node_option.type)

        if self.provides:
            print('-> ' + ' '.join([x.number for x in self.provides]))
        if self.requires:
            print('<- ' + ' '.join([x.number for x in self.requires]))

        print()

    def add_require(self, providing_node):
        ''' Node -> none

        providing_node -> self

        adds the supplied node to the list of nodes that this node requires.
        this is equivalent to adding the current node as a child of the
        providing_node '''

        if providing_node not in self.requires:

            # add the providing_node to our requirements
            self.requires.append(providing_node)

    def add_provide(self, requiring_node):
        ''' Node -> none

        self -> requiring_node

        adds the supplied node to the list of nodes that this node provides to.
        this is equivalent to adding the current node as a parent of the
        requiring_node '''

        if requiring_node not in self.provides:

            # add the requiring_node to our provisions
            self.provides.append(requiring_node)

    def write_dot(self, fd, graph_options):
        ''' file descriptor -> IO
        writes this node's graph data to the fd provided in graphviz dot format
        '''
        left = '"' + self.pretty_desc + '"'

        # write self -> other relationships
        for node in self.provides:
            right = '"' + node.pretty_desc + '" '

            # write edges
            fd.write('  ' + left + ' -> ' + right + '\n')

        # write other -> self relationships
        for node in self.requires:
            right = '"' + node.pretty_desc + '" '

            # write edges
            fd.write('  ' + right + ' -> ' + left + '\n')

        # apply options if they're enabled at the graph level
        if self.node_option and self.node_option.type in graph_options:
            left += ' ' + self.node_option.color

        # write node by itself
        fd.write('  ' + left + '\n')

    def write_definition(self, fd):
        ''' file descriptor -> None
        '''
        if len(self.number) < 2:
            fd.write('   ' + self.number + ': ')

        elif len(self.number) < 3:
            fd.write('  ' + self.number + ': ')

        else:
            fd.write(' ' + self.number + ': ')

        if self.node_option:
            fd.write(self.node_option.flag)

        fd.write(self.description + '\n')

    def write_dependencies(self, fd):
        ''' file descriptor -> None
        '''
        if self.provides:
            fd.write(
                    '  ' + self.number + ' -> ' +
                    ','.join([x.number for x in self.provides]) +
                    '\n')

        if self.requires:
            fd.write(
                    '  ' + self.number + ' <- ' +
                    ','.join([x.number for x in self.requires]) +
                    '\n')

    def parse_options(self):
        ''' none -> none
        checks the node's label for an option flag. if they exist, they're saved
        and the flag is removed from the label
        '''
        flag = self.description[0]

        if flag in ['@', '!', '_']:
            log('found option: ' + flag)
            self.node_option = Node_Option(flag)
            self.description = self.description[1:]
            self.pretty_desc = self.pretty_desc[1:]


class Graph_Option:
    '''
    '''
    def __init__(self, line):
        ''' string -> Graph_Option | SyntaxError
        '''
        options = ['color_complete', 'color_next', 'cleanup', 'color_urgent']
        if line in options:
            self.label = line
        else:
            raise SyntaxError


class Node_Option:
    '''
    '''
    def __init__(self, flag):
        ''' string -> Node_Option
        handles option flag information. these add colors to nodes. flags may
        be set by the user by appending them to the descriptions in the
        definitions section of the graph, or generated
        '''
        self.color = None
        self.type  = None
        self.flag  = flag

        log('option: ' + flag)

        if flag == '@':
            self.type  = 'color_complete'
            self.color = '[color="springgreen"];'

        elif flag == '!':
            self.type  = 'color_urgent'
            self.color = '[color="crimson"];'

        # bdgraph detects which nodes are eligble for color_next, not the user,
        # so we remove the output flag
        elif flag == '_':
            self.flag  = ''
            self.type  = 'color_next'
            self.color = '[color="lightskyblue"]'

        else:
            log('unrecongized option' + flag)


# MAIN
def main(argv):
    ''' list -> none
    handles IO
    '''
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

    graph = Graph(content)
    graph.handle_options()
    graph.compress_representation()
    graph.write_dot(output_fn)

    # rewrite the input file?
    options = [x.label for x in graph.graph_options]
    if 'cleanup' in options:
        graph.write_config(input_fn)


if __name__ == '__main__':
    main(sys.argv[1:])
