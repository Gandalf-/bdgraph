#!/usr/bin/python3
''' bdgraph.py
python bdgraph.py input_file [output_file]
'''

import sys, getopt, copy, os

# GLOBALS
shebang = '''#!/usr/local/bin/bdgraph
# a <- b,c,d == if a,b,c then d
# a -> b,c,d == if a then b,c,d
'''
nice_line_length = 25
no_output = False
had_syntax_error = False

decl_list = []
node_dict = {}
key_list = []

avail_opts = [
    'color_complete', 'color_urgent', 'color_next', 'cleanup'
    ]
opts_list = []
opt_dict = {
    '@' : ['color_complete', ' [color="springgreen"];'],
    '!' : ['color_urgent',' [color="red"];'],
    '_' : ['color_next', '[color="0.499 0.386 1.000"];'] 
    }


# HELPERS
''' string -> string'''
clean_str = lambda elm : str(elm).strip()

''' string -> string'''
cleanup = lambda tok : tok[1:].strip() if tok[0] in opt_dict else tok


# CLASSES
class Node:
    ''' encapsulates node's name, children, and state
    '''
    def __init__(self, name):
        self._name = name
        self._orig_name = name
        self._children = []
        self._prepped = False
        self._alt_syntax = False
        self._action = ['', '']
        return

    @property
    def name(self): 
        return self._name
    @name.setter
    def name(self, value): 
        self._name = value
        return

    @property
    def orig_name(self): 
        return self._orig_name

    @property
    def children(self): 
        return self._children

    def add_child(self, child):
        self._children.append(child)
        return

    @property
    def prepped(self): 
        return self._prepped
    @prepped.setter
    def prepped(self, value): 
        self._prepped = value
        return

    @property
    def alt_syntax(self):
        return self._alt_syntax
    def alt_syntax(self, value):
        self._alt_syntax = value
        return

    @property
    def action(self): 
        return self._action[1] if self._action[0] in opts_list else ''
    @property
    def action_type(self): 
        return self._action[0]
    @action.setter
    def action(self, value): 
        self._action = value
        return
    def set_action(self):
        if self._name[0] in opt_dict: 
            self._action = opt_dict[self._name[0]][1]
        return

class Decl:
    ''' encapsulates declerations's line, element number, name, and node
    '''
    def __init__(self, line_num, elem_num, name, node):
        self._line_num = line_num
        self._elem_num = elem_num
        self._name = name
        self._node = node
        return
  
    @property
    def line_num(self):
        return self._line_num
    @property
    def elem_num(self):
        return self._elem_num
    @property
    def name(self):
        return self._name
    @property
    def node(self):
        return self._node


# FUNCTIONS
def split_on_nearest_space(word, start):
    ''' string, int -> string
    searches left and right of the start point for a space
    and inserts a newline character there
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

def file_write(output, string):
    ''' string, string -> none
    wrapper for file writing that abides by the no_output flag
    '''
    if not no_output:
        output.write(string)
    return

def print_dependency(outer_elem, ordered_copy, output):
    ''' node, list of nodes, file handle -> none
    '''
    # if it has children
    if outer_elem.node.children:
        child_count = 0
        num_children = len(outer_elem.node.children)
        output.write('  ')

        output.write(str(outer_elem.elem_num).ljust(2 ,' ') + ' <- ')

        if outer_elem.node.alt_syntax:
            pass
            print("alt syntax node", outer_elem.node.orig_name)

        # for each child
        for child in outer_elem.node.children:
            key = ' '

            # find the child in the ordered list
            for inner_elem in ordered_copy:

                if inner_elem.node.orig_name == child.orig_name:
                    key = str(inner_elem.elem_num)

            if child_count < num_children -1:
                output.write(key + ',')
                child_count = child_count +1

            else:
                output.write(key + '\n')
    return

def cleanup_input(ordered_node, filename):
    ''' list of nodes, string -> none
    reconstructs the input file so that inputs are ordered correctly and
    intentional spacing is maintained
    '''
    ordered_decls = sorted(decl_list, key=lambda x: int(x.line_num))

    with open(filename, 'w') as output:
        output.write(shebang + '\n')
        found_first_decl = False

        # declarations
        for decl in ordered_decls:
            if decl.elem_num != -1:
                found_first_decl = True
                output.write(format(decl.elem_num, ' 3d'))

                if decl.node.orig_name[0] in opt_dict:
                    output.write(': ' + decl.node.orig_name + '\n')
                else:
                    output.write(':  ' + decl.node.orig_name + '\n')
            else:
                if found_first_decl:
                    output.write('\n')

        # options
        output.write('options\n')
        for option in opts_list:
            output.write('  ' + option + '\n')

        # filter out newlines and make a copy for nested iteration
        ordered_decls[:] = filter(lambda x : x.elem_num != -1, ordered_decls)
        ordered_copy = copy.deepcopy(ordered_decls)

        # dependencies
        output.write('\ndependencies\n')

        for outer_decl in ordered_decls:
            print_dependency(outer_decl, ordered_decls, output)

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

def parse_inputs(line, line_num, elem_num):
    ''' string, int, int -> int
    builds key_list and decl_list structures from each input line
        1 : Chop wood
        2 : Buy matches
    '''
    parts = line.split(':', 1)

    if len(parts) > 1:
        decl_name = clean_str(parts[0])
        decl_node = Node(clean_str(parts[1]))

        decl_list.append( Decl(line_num, elem_num, decl_name, decl_node))
        elem_num = elem_num + 1

        if decl_name not in key_list:
            key_list.append(decl_name)

        node_dict[decl_name] = decl_node

    # try to catch syntax errors
    elif ((parts[0].lower() not in ['', 'options']) and
        (parts[0] and parts[0][0] != '#')):

        had_syntax_error = True
        print('ignoring unknown syntax on line: '+ 
                str(line_num +1)+ ', "' + parts[0] + '"')

    # keep track of extra line breaks so we can reconstruct 
    # them in cleanup mode
    else:
        decl_list.append( Decl(line_num, -1, '', None))

    return elem_num

def parse_options(line):
    ''' string -> none
    sets which actions are allowed
    '''
    option = clean_str(line.lower())

    if option in avail_opts:
        opts_list.append(option)

    return

def parse_dependencies(line, output, line_num):
    ''' string -> none
    prints the required output for lines of the form
        2 <- 1
        5 <- 1,2,3,4
        1 -> 2,5
    '''
    parts = line.split('<-', 1)

    if len(parts) > 1:
        # get the left side once
        try:
            right_node = get_and_prep_elem(clean_str(parts[0]) )
        except KeyError:
            print('error: unknown dependency "'+clean_str(parts[0]) +
                    '" on line number: ' + str(line_num) +', "' + line +'"')
            sys.exit(1)

        # for each right side
        for elem in parts[1].split(','):

            # get each left hand side 
            left_node = get_and_prep_elem(clean_str(elem) )
            right_node.add_child(left_node)

            file_write(output, '    "' + left_node.name + '" -> "' + 
                       right_node.name + '"' + right_node.action + '\n')
    else:
      parts = line.split('->', 1)

      if len(parts) > 1:
        # get the right side once
        try:
            right_node = get_and_prep_elem(clean_str(parts[0]) )
        except KeyError:
            print('error: unknown dependency "'+clean_str(parts[0]) +
                    '" on line number: ' + str(line_num) +', "' + line +'"')
            sys.exit(1)

        # for each left side
        for elem in parts[1].split(','):
            print('adding dep')

            left_node = get_and_prep_elem(clean_str(elem) )
            left_node.add_child(right_node)
            print("setting", left_node.name, "to alt syn")
            left_node.alt_syntax = True

            file_write(output, '    "' + right_node.name + '" -> "' + 
                       left_node.name + '"' + left_node.action + '\n')

      elif parts[0].lower() not in ['', 'dependencies']:
          had_syntax_error = True
          print('ignoring unknown syntax on line: '+ 
                  str(line_num +0) + ', "' + parts[0] + '"')
    return

# MAIN
def main(argv):
    ''' list -> none
    handles IO
    '''
    input_fn,output_fn = '', ''
    inputs_done = False
    options_done = False

    # parse args
    if len(argv) > 0:
        input_fn = str(argv[0])

        if not os.path.exists(input_fn):
            print('error: file "' + input_fn + '" does not exist')
            sys.exit(1)
    else:
        print('python bdgraph.py input_file [output_file]')
        sys.exit(1)

    # read input
    with open(input_fn, 'r') as f:
        content = [elem.strip('\n') for elem in f.readlines()]

    # optional output file name
    if len(argv) > 1:
        output_fn = str(argv[1])
    else:
        output_fn = input_fn + '.dot'

    # parse input and write output
    with open(output_fn, 'w') as output:
        file_write(output, 'digraph g{\n')
        file_write(output, '    rankdir=LR;\n')
        file_write(output, '    ratio = fill;\n')
        file_write(output, '    node [style=filled];\n')

        line_num = 0
        elem_num = 1
        had_syntax_error = False

        for line in content:
            line = clean_str(line)

            if line.lower() == 'options':
                inputs_done = True

            if line.lower() == 'dependencies':
                options_done = True
            
            if not inputs_done:
                elem_num = parse_inputs(line, line_num, elem_num)

            elif not options_done:
                parse_options(line)

            else:
                parse_dependencies(line, output, line_num)

            line_num = line_num +1

        # decorate nodes without unmet dependencies
        for key in key_list:
            tmp_node = get_and_prep_elem(key)

            if not tmp_node.action:
                all_deps_met = True

                for child in tmp_node.children:
                    if 'color_complete' not in child.action_type:
                        all_deps_met = False

                if all_deps_met:
                    tmp_node.action = opt_dict['_']

        # write all nodes, nodes with dependencies will be
        # repeated, but that's by design
        for key in key_list:
            tmp_node = get_and_prep_elem(key)

#TODO this is a work around
            modifier = tmp_node.action
            modifier = modifier[1] if len(modifier) > 1 else modifier
            file_write(
                    output,
                    '    "' + tmp_node.name + '"' + modifier + '\n')

        file_write(output, "}\n")
    
    # clean up the input file?
    if 'cleanup' in opts_list:
        if not had_syntax_error:
            cleanup_input(decl_list, input_fn)
        else:
            print('cleanup requested but not performed due to syntax error')

    return

if __name__ == '__main__':
    main(sys.argv[1:])
