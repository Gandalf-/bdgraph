#!/usr/bin/python3

import bdgraph


class NodeOption:
    '''
    '''

    flags = ['@', '!', '_', '&']

    def __init__(self, flag, logging=False):
        ''' string -> NodeOption | BdgraphSyntaxError

        handles option flag information. these add colors to nodes. flags may
        be set by the user by appending them to the descriptions in the
        definitions section of the graph, or generated

        raises SyntaxError is an invalid option is provided '''

        self.color = None       # string
        self.type = None        # string
        self.flag = flag        # char
        self.logging = logging  # bool

        self.log('option: ' + flag)

        if flag == '@':
            self.type = bdgraph.Option.Complete
            self.color = '[color="springgreen"];'

        elif flag == '!':
            self.type = bdgraph.Option.Urgent
            self.color = '[color="crimson"];'

        # '&' marks nodes that will be removed by graph.handle_options()
        elif flag == '&':
            self.type = bdgraph.Option.Remove
            self.color = ''

        # bdgraph detects which nodes are eligble for color_next, not the user,
        # so we remove the output flag
        elif flag == '_':
            self.flag = ''
            self.type = bdgraph.Option.Next
            self.color = '[color="lightskyblue"]'

        else:
            self.log('unrecongized option' + flag)
            raise bdgraph.BdgraphSyntaxError

    def log(self, comment):
        ''' string -> maybe IO

        debugging function, only print if global `logging` is true '''

        if self.logging:
            print(comment)
