#!/usr/bin/python3

# plint: disable=import-error
import pytest

#from app.graph import Graph
from app.node import Node

def test_node_label_description_parsing():
    label = '1'
    description = 'label'
    node = Node(label + ': ' + description)

    assert(node.label == label)
    assert(node.description == description)

    label = '560'
    description = 'very long label with lots of words and text'
    node = Node(label + ': ' + description)

    assert(node.label == label)
    assert(node.description == description)

def test_node_creation_validation():
    with pytest.raises(Exception):
        node = Node('junk')
