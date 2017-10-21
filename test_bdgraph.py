#!/usr/bin/python3

import unittest
from bdgraph import Node, NodeOption
from bdgraph import Graph, GraphOption
from bdgraph import BdgraphRuntimeError

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


class TestGraph(unittest.TestCase):
    ''' graph '''

    def test_simple_graph(self):
        Graph(simple)

    def test_invalid_dependency(self):
        graph = template.format(h='1: apple', d='1 <- 2', o='')

        with self.assertRaises(BdgraphRuntimeError):
            Graph(graph)

    def test_empty_graph(self):
        ''' an empty graph is not an error '''
        Graph('')

    def test_find_node(self):
        graph = Graph(simple)
        graph.show()
        self.assertIsNotNone(graph.find_node('1'))

    def test_find_most(self):
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

    def test_invalid_option(self):
        with self.assertRaises(Exception):
            NodeOption('invalid')


if __name__ == '__main__':
    unittest.main()
