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

class Node(object):
    ''' Class

    the Node object contains all the information for a given node in the graph.
    in particular the Node.provides and Node.requires attributes define the
    graph '''

    node_counter = 1    # ensures Node.number is unique and contiguous

    def __init__(self, label, logging=False):
        ''' string -> Node | ValueError

        label       : number this Node is assigned in the input file
        description : description of the node from the input file
        pretty_desc : description of the node, with newlines inserted
        node_option : optional Node_Option
        provides    : list of nodes that this node is the parent to
        requires    : list of nodes that this node is a child to
        number      : new number assigned to this Node '''

        self.log('node ' + label)
        self.label = ''             # string
        self.description = ''       # string
        self.pretty_desc = ''       # string
        self.node_option = None     # Node_Option

        self.provides = []          # list of Node
        self.requires = []          # list of Node
        self.logging = logging      # bool

        self.number = str(Node.node_counter)
        self.label, self.description = [x.strip() for x in label.split(':')]

        # break up description to multiple lines
        desc_len = len(self.description)
        if desc_len < 50:
            # break in half
            self.pretty_desc = self.split_on_nearest_space(
                    self.description, desc_len // 2)
        else:
            # break in thirds
            self.pretty_desc = self.split_on_nearest_space(
                    self.description, desc_len // 3)
            self.pretty_desc = self.split_on_nearest_space(
                    self.pretty_desc, 2 * (desc_len // 3))

        # check for options flags
        self.parse_options()

        # update node counter
        Node.node_counter += 1

    def show(self):
        ''' none -> IO

        prints a representation of the node to the console '''

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
        only this uses the Node.pretty_desc attribute. each node is written in
        the following way
            1 -> 2,3        # provides
            1 <- 4,5        # requires
            1 [options];    # options '''

        graph_option_labels = ' '.join([x.label for x in graph_options])

        left = '"' + self.pretty_desc

        if 'publish' not in graph_option_labels:
            left += ' (' + self.number + ')"'
        else:
            left += '"'

        # write self -> other relationships
        for node in self.provides:
            right = '"' + node.pretty_desc + ' (' + node.number + ')"'


            # write edges
            fd.write('  ' + left + ' -> ' + right + '\n')

        # write other -> self relationships
        for node in self.requires:
            right = '"' + node.pretty_desc + ' (' + node.number + ')"'

            # write edges
            fd.write('  ' + right + ' -> ' + left + '\n')

        # apply options if they're enabled at the graph level
        if self.node_option and self.node_option.type in graph_option_labels:
            left += ' ' + self.node_option.color

        # write node by itself
        fd.write('  ' + left + '\n')

    def write_definition(self, fd):
        ''' file descriptor -> None

        writes the node definition in config format
            1: @Applesauce
            ${number}: ${flag}${description} '''

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

        writes dependency information for the node in config format
            1 <- 3,4
            3,4 -> 1 '''

        if self.provides:
            fd.write('  %s -> %s\n' %
                    (self.number, ','.join([x.number for x in self.provides])))

        if self.requires:
            fd.write('  %s <- %s\n' %
                    (self.number, ','.join([x.number for x in self.requires])))

    def parse_options(self):
        ''' none -> none
        checks the node's label for an option flag. if they exist, they're saved
        and the flag is removed from the label '''

        flag = self.description[0]

        if flag in ['@', '!', '_', '&']:

            self.log('found option: ' + flag)
            self.node_option = Node_Option(flag)

            # remove the flag from the descriptions
            self.description = self.description[1:]
            self.pretty_desc = self.pretty_desc[1:]

    def transitive_reduction(self, node, skip=False):
        ''' Node, bool -> none | RuntimeError

        skip allows us to jump over immediate children, since we don't want to
        affect their relationships. see Graph.transitive_reduction() for an
        explaination of the algorithm '''

        if not skip:
            # remove relationships with non-immediate children
            if self in node.provides:
                node.provides.remove(self)
                self.requires.remove(node)

        # recurse
        for child in self.provides:
            child.transitive_reduction(node)

    def log(self, comment):
        ''' string -> maybe IO

        debugging function, only print if global `logging` is true '''

        try:
            if self.logging:
                print(comment)
        except AttributeError:
            pass

    def split_on_nearest_space(self, word, start):
        ''' string, int -> string

        searches left and right of the start point for a space and inserts a
        newline character there. this is useful when writing the dot file so that
        the bubbles aren't stretched out by long descriptions '''

        right = left = start

        while right < len(word) and left > 0:
            if word[right] == ' ':
                return word[:right] + '\\n' + word[right:]

            if word[left] == ' ':
                return word[:left] + '\\n' + word[left:]

            left = left - 1
            right = right + 1

        return word


class Node_Option:
    '''
    '''
    def __init__(self, flag, logging=False):
        ''' string -> Node_Option | SyntaxError

        handles option flag information. these add colors to nodes. flags may
        be set by the user by appending them to the descriptions in the
        definitions section of the graph, or generated

        raises SyntaxError is an invalid option is provided '''

        self.color = None       # string
        self.type  = None       # string
        self.flag  = flag       # char
        self.logging = logging  # bool

        self.log('option: ' + flag)

        if flag == '@':
            self.type  = 'color_complete'
            self.color = '[color="springgreen"];'

        elif flag == '!':
            self.type  = 'color_urgent'
            self.color = '[color="crimson"];'

        # the '&' flag marks nodes that will be removed by graph.handle_options()
        elif flag == '&':
            self.type  = 'remove_marked'
            self.color = ''

        # bdgraph detects which nodes are eligble for color_next, not the user,
        # so we remove the output flag
        elif flag == '_':
            self.flag  = ''
            self.type  = 'color_next'
            self.color = '[color="lightskyblue"]'

        else:
            self.log('unrecongized option' + flag)
            raise SyntaxError

    def log(self, comment):
        ''' string -> maybe IO

        debugging function, only print if global `logging` is true '''

        if self.logging:
            print(comment)
