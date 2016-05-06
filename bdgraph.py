#!/usr/bin/python3
''' bdgraph.py
python bdgraph.py input_file [output_file]
'''

import sys, getopt, copy

# GLOBALS
nice_line_length = 25
no_output = False

node_list = []
node_dict = {}

key_list = []

available_options = [
    'color_complete', 'color_urgent', 'color_next', 'cleanup'
    ]
options_list = []
options_dict = {
    '@' : ['color_complete', ' [color="green"];'],
    '!' : ['color_urgent',' [color="red"];'],
    '_' : ['color_next', '[color="0.499 0.386 1.000"];'] 
    }


# HELPERS
''' string -> string'''
clean_str = lambda elm : str(elm).strip()

''' string -> string'''
cleanup = lambda tok : tok[1:].strip() if tok[0] in options_dict else tok


# CLASSES
class Node:
    def __init__(self, name):
        self._name = name
        self._orig_name = name
        self._children = []
        self._prepped = False
        self._action = ['', '']

    @property
    def name(self): return self._name
    @name.setter
    def name(self, value): self._name = value

    @property
    def orig_name(self): return self._orig_name

    @property
    def children(self): return self._children

    def add_child(self, child):
        self._children.append(child)

    @property
    def prepped(self): return self._prepped
    @prepped.setter
    def prepped(self, value): self._prepped = value

    @property
    def action(self): 
        return self._action[1] if self._action[0] in options_list else ''
    @property
    def action_type(self): return self._action[0]
    @action.setter
    def action(self, value): self._action = value

    def set_action(self):
        if self._name[0] in options_dict: 
            self._action = options_dict[self._name[0]]


# FUNCTIONS
def split_on_nearest_space(word, start):
    ''' string, int -> string
    searches left and right of the start point for a space
    and inserts a newline character there
    '''

    length = len(word)
    right = left = start

    while right < length and left > 0:
        if word[right] == ' ':
            return word[:right] + '\\n' + word[right:]

        if word[left] == ' ':
            return word[:left] + '\\n' + word[left:]

        left = left - 1
        right = right + 1

    return word

def file_write(output, string):
    ''' string, string -> none
    '''
    if not no_output:
        output.write(string)
    return

def cleanup_input(ordered_node, filename):
    ''' list of nodes, string -> none
    '''
    ordered_elems = sorted(node_list, key=lambda x: int(x[0]))

    with open(filename, 'w') as output:
        for elem in ordered_elems:
            if elem[1] != -1:
                output.write(format(elem[1], " 3d"))

                if elem[3].orig_name[0] in options_dict:
                    output.write(': ' + elem[3].orig_name + '\n')
                else:
                    output.write(':  ' + elem[3].orig_name + '\n')
            else:
                output.write("\n")

        output.write("options\n")
        for option in options_list:
            output.write("  " + option + "\n")

        # filter out newlines and make a copy for nested iteration
        ordered_elems[:] = filter(lambda x : x[1] != -1, ordered_elems)
        ordered_copy = copy.deepcopy(ordered_elems)

        output.write("\ndependencies\n")

        # for each node element
        for outer_elem in ordered_elems:

            # if it has children
            if outer_elem[3].children:
                child_count = 0
                num_children = len(outer_elem[3].children)
                output.write("  ")

                # for each child
                for child in outer_elem[3].children:
                    key = " "

                    # find the child in the ordered list
                    for inner_elem in ordered_copy:

                        if inner_elem[3].orig_name == child.orig_name:
                            key = str(inner_elem[1])

                    if child_count < num_children -1:
                        output.write(key + ",")
                        child_count = child_count +1

                    else:
                        output.write(key + " -> ")

                output.write(str(outer_elem[1]) + "\n")
    return

def get_and_prep_elem(key):
    ''' string -> Node
    retrieves elements from the node_dict dictionary and inserts
    newline characters to make them look nicer
    '''
    node = node_dict[clean_str(key)]

    if not node.prepped: 
        token = node.name

        length = len(token)
        half = length // 2

        # split in half if shortish
        if length < 2 * nice_line_length:
            token = split_on_nearest_space(token, half)

        # split it in thirds if longish
        else:
            first_third = length // 3
            second_third = 2 * (length // 3)

            token = split_on_nearest_space(token, first_third)
            token = split_on_nearest_space(token, second_third)

        # update the node
        node.set_action()
        node.name = cleanup(token)
        node.prepped = True

    return node

def parse_options(line):
    ''' string -> none
    sets which actions are allowed
    '''
    option = clean_str(line.lower())

    if option in available_options:
        options_list.append(option)

    return

def parse_dependencies(line, output):
    ''' string -> none
    prints the required output for lines of the form
        1 -> 2
        1,2,3,4 -> 5
    '''
    parts = line.split('->', 1)

    if len(parts) > 1:
        # get the right side once
        right_node = get_and_prep_elem(clean_str(parts[1]) )

        # for each left side
        # supports 1,2,3 -> 4
        for elem in parts[0].split(','):

            # get each left hand side 
            left_node = get_and_prep_elem(clean_str(elem) )
            right_node.add_child(left_node)

            file_write(output, '"' + left_node.name + '" -> "' + 
                       right_node.name + '"' + right_node.action + '\n')
    return

# MAIN
def main(argv):
    ''' list -> none
    handles IO
    '''
    fname,oname = '', ''
    found_deps = False
    found_options = False

    # parse args
    if len(argv) > 0:
        fname = str(argv[0])
    else:
        print('python bdgraph.py input_file [output_file]')
        sys.exit(1)

    # read input
    with open(fname, 'r') as f:
        content = [elem.strip('\n') for elem in f.readlines()]

    # optional output file name
    oname = str(argv[1]) if len(argv) > 1 else fname + ".dot"

    # parse input and write output
    with open(oname, 'w') as output:
        file_write(output, "digraph g{\n")
        file_write(output, "rankdir=LR;\n")
        file_write(output, "ratio = fill;\n")
        file_write(output, "node [style=filled];\n")

        line_num = 0
        elem_num = 1

        for line in content:
            line = clean_str(line)

            if line.lower() == "dependencies":
                found_deps = True
                found_options = False

            if line.lower() == "options":
                found_options = True
                found_deps = False
            
            # parse in the bindings
            # 1 : Put on socks
            if not found_deps and not found_options:
                parts = line.split(':', 1)

                if len(parts) > 1:
                    left = clean_str(parts[0])
                    right = Node(clean_str(parts[1]))

                    node_list.append([line_num, elem_num, left, right])
                    elem_num = elem_num + 1

                    if left not in key_list:
                        key_list.append(left)

                    node_dict[left] = right

                # keep track of extra line breaks so we can reconstruct 
                # them in cleanup mode
                else:
                    node_list.append([line_num, -1, '', ''])

                line_num = line_num +1

            elif found_options: 
                parse_options(line)

            elif found_deps: 
                parse_dependencies(line, output)

        # decorate nodes without unmet dependencies
        for key in key_list:
            tmp_node = get_and_prep_elem(key)

            if not tmp_node.action:
                all_deps_met = True

                for child in tmp_node.children:
                    if 'color_complete' not in child.action_type:
                        all_deps_met = False

                if all_deps_met:
                    tmp_node.action = options_dict['_']


        # write all nodes, nodes with dependencies will be
        # repeated, but that's by design
        for key in key_list:
            tmp_node = get_and_prep_elem(key)
            file_write(output, '"' + tmp_node.name + '"' + tmp_node.action + '\n')

        file_write(output, "}\n")
    
    # clean up the input file?
    if 'cleanup' in options_list:
        cleanup_input(node_list, fname)

    return

if __name__ == '__main__':
    main(sys.argv[1:])
