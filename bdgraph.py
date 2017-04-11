#!/usr/bin/python3
''' bdgraph.py
python bdgraph.py input_file [output_file]
'''

import sys, os

logging = True

# GLOBALS
SHEBANG = '''#!/usr/local/bin/bdgraph
# a <- b,c,d == if a,b,c then d
# a -> b,c,d == if a then b,c,d
'''
opt_dict = {
    '@' : ['color_complete', ' [color="springgreen"];'],
    '!' : ['color_urgent',' [color="red"];'],
    '_' : ['color_next', '[color="0.499 0.386 1.000"];']
    }

# HELPERS
def log(comment):
    if logging:
        print(comment)

# CLASSES
class Graph:
    '''
    '''
    def __init__(self, contents):
        ''' list of strings -> Graph
        creates the graph from an list of strings, which come from the input
        file
        '''
        self.contents = contents        # list of string
        self.nodes = []                 # list of Node
        self.options = []               # list of Option

        mode = 'definition'

        for line in contents:
            # state machine
            if line == 'options':
                mode = 'options'

            elif line == 'dependencies':
                mode = 'dependencies'

            # actions
            if mode == 'definition':
                log('definition: ' + line)
                self.nodes.append(Node(line))

            elif mode == 'options':
                log('options: ' + line)
                self.options.append(Option(line))

            elif mode == 'dependencies':
                log('dependencies: ' + line)
                self.update_dependencies(line)

    def show(self):
        '''
        prints a representation of the graph to the console
        '''
        for node in self.nodes:
            node.show()

    def update_dependencies(self, line):
        ''' string -> none
        update the Nodes referenced in the dependency line provided. Inputs are
        in the form
        1,2,3 -> 4,5,6
        1,2,3 <- 4,5,6
        '''

        # determine dependency type
        require = line.split('<-')
        allow   = line.split('->')

        # 1,2,3 <- 4,5,6
        if len(require) > 1:
            requiring_nodes = [x.strip() for x in require[0].split(',')]
            providing_nodes = [x.strip() for x in require[1].split(',')]

        # 1,2,3 -> 4,5,6
        elif len(allow) > 1:
            providing_nodes = [x.strip() for x in allow[0].split(',')]
            requiring_nodes = [x.strip() for x in allow[1].split(',')]

        # unrecongized, ignore
        else:
            return

        # update requirements and provisions for each node
        for r_label in requiring_nodes:
            requiring_node = self.find_node(r_label)

            for p_label in providing_nodes:
                providing_node = self.find_node(p_label)

                requiring_node.add_require(providing_node)
                providing_node.add_provide(requiring_node)


    def find_node(self, label):
        ''' string -> Node
        search through the graph's nodes for the node with the same label as
        the one provided
        '''
        for node in self.nodes:
            if node.label == label:
                log('found: ' + label)
                return node

        log('failed to find: ' + label)
        return None

class Node:
    '''
    '''
    def __init__(self, label):
        ''' string -> Node
        '''
        log('node ' + label)
        self.label = ''             # string
        self.description = ''       # string
        self.provides = []          # list of Node
        self.requires = []          # list of Node

        try:
            self.label, self.description = [x.strip() for x in label.split(':')]

        # ignore unrecongized syntax
        except ValueError:
            return

    def show(self):
        '''
        '''
        print(self.label + ': ' + self.description)
        if self.provides:
            print('-> ' + ' '.join([x.label for x in self.provides]))
        if self.requires:
            print('<- ' + ' '.join([x.label for x in self.requires]))
        print()

    def add_require(self, providing_node):
        '''
        '''
        if providing_node not in self.requires:
            self.requires.append(providing_node)

    def add_provide(self, requiring_node):
        '''
        '''
        if requiring_node not in self.provides:
            self.provides.append(requiring_node)

class Option:
    '''
    '''
    def __init__(self, label):
        ''' string -> Option
        '''
        pass

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

    print(content)

    graph = Graph(content)
    graph.show()

    print(output_fn)
    return

if __name__ == '__main__':
    main(sys.argv[1:])
