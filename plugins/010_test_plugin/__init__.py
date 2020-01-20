"""
Plugin

ons for other plugins
"""

import json

__version__ = '0.0.1'


MANAGER = None

VERBOSE = True


def action_init(params):
    global MANAGER
    try:
        MANAGER = params['manager']
        MANAGER.app_log.warning("Init Test Plugin")
    except:
        # Better ask forgiveness than permission
        pass


def action_post_init(params):
    try:
        MANAGER.app_log.warning("Post Init Test Plugin")
    except:
        # Better ask forgiveness than permission
        pass

