#!/usr/bin/python3

class Option():

    Complete = 'color_complete'
    Next     = 'color_next'
    Urgent   = 'color_urgent'
    Cleanup  = 'cleanup'
    Circular = 'circular'
    Publish  = 'publish'
    Remove   = 'remove_marked'

    options = [Complete, Next, Urgent, Cleanup, Circular, Publish, Remove]

    def __init__(self):
        pass
