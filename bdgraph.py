#!/usr/bin/python3
''' bdgraph.py
Works with 
    http://www.webgraphviz.com/
    xdot

    Input file format:
        1 :  Put on socks
        2 : !Put on shoes
        3 : @Go to work

        Options
            color_next
            color_complete
            color_urget

        Dependencies
            1 -> 2
            1,2 -> 3

    Output: dot format file
'''

import sys, getopt, copy

# globals
nice_line_length = 25

''' string : Node '''
node_dict = {}

node_order = []

''' string '''
key_list = []

''' char : list of strings '''
special_chars = {
        '@' : ['color_complete', ' [color="green"];'],
        '!' : ['color_urgent',' [color="red"];'],
        '_' : ['color_next', '[color="0.499 0.386 1.000"];'] }

''' string '''
options = []


# helpers
''' string -> string'''
clean_str = lambda elm : str(elm).strip()

''' string -> string'''
cleanup = lambda tok : tok[1:].strip() if tok[0] in special_chars else tok


# classes
class Node:

    def __init__(self, name):
        self._name = name
        self._orig_name = name
        self._children = []
        self._prepped = False
        self._action = ['', '']
        self._properties = []

    @property
    def prepped(self): return self._prepped
    @prepped.setter
    def prepped(self, value): self._prepped = value

    @property
    def name(self): return self._name
    @name.setter
    def name(self, value): self._name = value

    @property
    def orig_name(self): return self._orig_name

    @property
    def action(self): 
        return self._action[1] if self._action[0] in options else ''
    @property
    def action_type(self): return self._action[0]
    @action.setter
    def action(self, value): self._action = value

    def set_action(self):
        if self._name[0] in special_chars: 
            self._action = special_chars[self._name[0]]

    @property
    def children(self): return self._children

    def add_child(self, child):
        self._children.append(child)


# functions
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

        # split in half
        if length < 2 * nice_line_length:
            token = split_on_nearest_space(token, half)

        # split it in thirds
        else:
            first_third = length // 3
            second_third = 2 * (length // 3)

            token = split_on_nearest_space(token, first_third)
            token = split_on_nearest_space(token, second_third)

        #node.action = get_action(node.name)
        node.set_action()
        node.name = cleanup(token)
        node.prepped = True

    return node

def parse_options(line):
    ''' string -> none
    sets which actions are allowed
        color_next
        color_complete
        color_urget
    '''
    if line.lower() == 'color_next':
        options.append('color_next')

    elif line.lower() == 'color_complete':
        options.append('color_complete')

    elif line.lower() == 'color_urgent':
        options.append('color_urgent')

    elif line.lower() == 'cleanup':
        options.append('cleanup')

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

        # supports 1,2,3 -> 4
        for elem in parts[0].split(','):

            # get each left hand side 
            left_node = get_and_prep_elem(clean_str(elem) )
            right_node.add_child(left_node)

            output.write('"' + left_node.name + '" -> "' + 
                         right_node.name + '"' + right_node.action + '\n')
    return

# main
def main(argv):
    ''' list -> none
    handles IO
    '''

    fname,oname = '', ''
    found_deps = False
    found_options = False

    # parse args
    fname = str(argv[0])
    oname = str(argv[1])

    if not fname or not oname:
        print('python bdgraph.py <input_file> <output_file>')
        sys.exit(1)

    # read input
    with open(fname, 'r') as f:
        content = [elem.strip('\n') for elem in f.readlines()]

    # write output
    with open(oname, 'w') as output:
        output.write("digraph g{\n")
        output.write("rankdir=LR;\n")
        output.write("ratio = fill;\n")
        output.write("node [style=filled];\n")

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

                    node_order.append([line_num, elem_num, left, right])
                    elem_num = elem_num + 1

                    if left not in key_list:
                        key_list.append(left)

                    node_dict[left] = right

                # keep track of extra line breaks for cleanup
                else:
                    node_order.append([line_num, -1, '', ''])

                line_num = line_num +1

            elif found_options: parse_options(line)

            elif found_deps: parse_dependencies(line, output)

        # decorate nodes without unmet dependencies
        for key in key_list:
            tmp_node = get_and_prep_elem(key)

            if not tmp_node.action:
                all_deps_met = True

                for child in tmp_node.children:
                    if 'completed' not in child.action_type:
                        all_deps_met = False

                if all_deps_met:
                    tmp_node.action = special_chars['_']


        # write all nodes, nodes with dependencies will be
        # repeated, but that's by design
        for key in key_list:
            tmp_node = get_and_prep_elem(key)
            output.write('"' + tmp_node.name + '"' + tmp_node.action + '\n')

        output.write("}\n")
    
        # clean up the input file?
        if 'cleanup' in options:
            ordered_elems = sorted(node_order, key=lambda x: int(x[0]))

            with open("rewrite.bdot", 'w') as output:
                for e in ordered_elems:
                    if e[1] != -1:
                        output.write(format(e[1], " 3d") + ':  ' + e[3].orig_name + '\n')
                    else:
                        output.write("\n")

                output.write("options\n")
                for e in options:
                    output.write("  " + e + "\n")

                # filter out newlines
                ordered_elems[:] = filter(lambda x : x[1] != -1, ordered_elems)
                ordered_copy = copy.deepcopy(ordered_elems)

                output.write("\ndependencies\n")

                # for each element
                for e in ordered_elems:

                    # if it has children
                    if e[3].children:
                        child_count = 0
                        num_children = len(e[3].children)
                        output.write("  ")

                        # for each child
                        for child in e[3].children:
                            number = " "

                            # find the child in the ordered list
                            for elem in ordered_copy:

                                if elem[3].orig_name == child.orig_name:
                                    number = str(elem[1])

                            if child_count < num_children -1:
                                output.write(number + ",")
                                child_count = child_count +1

                            else:
                                output.write(number + " -> ")

                        output.write(str(e[1]) + "\n")

    return

if __name__ == '__main__':
    main(sys.argv[1:])
