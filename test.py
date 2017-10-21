#!/usr/bin/python3

import unittest
from bdgraph import Node, NodeOption
from bdgraph import Graph, GraphOption
from bdgraph import BdgraphRuntimeError, BdgraphNodeNotFound

template = '''
{h}
options
{o}
dependencies
{d}
'''

simple = '''
1: apple
2: sauce

options
color_next

dependencies
1 <- 2
'''


def read_graph(filename):
    ''' string -> string
    '''
    filename = 'bdgraph/test/sources/' + filename

    with open(filename, 'r') as input_fd:
        return input_fd.read()


class TestRegression(unittest.TestCase):
    ''' no errors on graphs that used to work '''

    def test_references(self):
        contents = read_graph('references.bdot')
        graph = Graph(contents)
        self.assertIsNotNone(graph)

        graph.handle_options()
        graph.transitive_reduction()
        graph.compress_representation()

    def test_example(self):
        contents = read_graph('example.bdot')
        graph = Graph(contents)
        self.assertIsNotNone(graph)

        graph.handle_options()
        graph.transitive_reduction()
        graph.compress_representation()

    def test_simple(self):
        contents = read_graph('simple.bdot')
        graph = Graph(contents)
        self.assertIsNotNone(graph)

        graph.handle_options()
        graph.transitive_reduction()
        graph.compress_representation()


class TestGraph(unittest.TestCase):
    ''' graph '''

    def test_simple_graph(self):
        ''' check if our sanity is intact '''
        Graph(simple)

    def test_complex_graph(self):
        contents = read_graph('references.bdot')
        self.assertIsNotNone(Graph(contents))

    def test_invalid_dependency(self):
        ''' dependency states 1 <- 2, but 2 doesn't exist '''
        graph = template.format(h='1: apple', d='1 <- 2', o='')

        with self.assertRaises(BdgraphRuntimeError):
            Graph(graph)

    def test_empty_graph(self):
        ''' an empty graph is not an error '''
        Graph('')

    def test_find_node(self):
        ''' search for the node with label == 1 '''
        graph = Graph(simple)
        self.assertIsNotNone(graph.find_node('1'))

    def test_find_node_invalid(self):
        ''' search for a node that doesn't exist '''
        graph = Graph(simple)
        with self.assertRaises(BdgraphNodeNotFound):
            graph.find_node('5')

    def test_find_most(self):
        pass

    def test_find_most_invalid(self):
        pass

    def test_compress_representation(self):
        pass

    def test_transitive_reduction(self):
        pass


class TestGraphOption(unittest.TestCase):
    ''' graph options '''

    def test_complete(self):
        pass

    def test_next(self):
        pass

    def test_urgent(self):
        pass

    def test_cleanup(self):
        pass

    def test_circular(self):
        pass

    def test_publish(self):
        pass

    def test_remove(self):
        pass

    def test_noreduce(self):
        pass


class TestNode(unittest.TestCase):
    ''' node '''

    def test_simple_node_creation(self):
        label = '1'
        description = 'label'
        node = Node(label + ': ' + description)

        self.assertEqual(node.label, label)
        self.assertEqual(node.description, description)

    def test_complex_node_creation(self):
        label = '560'
        description = 'very long label with lots of words and text'
        node = Node(label + ': ' + description)

        self.assertEqual(node.label, label)
        self.assertEqual(node.description, description)

    def test_invalid_syntax(self):
        with self.assertRaises(Exception):
            Node('junk')

    def test_add_require(self):
        pass

    def test_add_provide(self):
        pass


class TestNodeOption(unittest.TestCase):
    ''' node option '''

    def test_valid_complete(self):
        NodeOption('@')

    def test_valid_urgent(self):
        NodeOption('!')

    def test_valid_remove(self):
        NodeOption('&')

    def test_valid_next(self):
        NodeOption('_')

    def test_invalid_option(self):
        with self.assertRaises(Exception):
            NodeOption('invalid')


if __name__ == '__main__':
    unittest.main()
