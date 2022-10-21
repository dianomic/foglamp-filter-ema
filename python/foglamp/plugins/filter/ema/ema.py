# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: https://foglamp-foglamp-documentation.readthedocs-hosted.com
# FOGLAMP_END

""" Module for EMA filter plugin

Generate Exponential Moving Average
The rate value (x) allows to include x% of current value
and (100-x)% of history
A datapoint called 'ema' is added to each reading being filtered
"""

import time
import copy
import logging

from foglamp.common import logger
import filter_ingest

__author__ = "Massimiliano Pinto"
__copyright__ = "Copyright (c) 2022 Dianomic Systems Inc."
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_LOGGER = logger.setup(__name__, level=logging.INFO)

PLUGIN_NAME = 'ema'

_DEFAULT_CONFIG = {
    'plugin': {
        'description': 'Exponential Moving Average filter plugin',
        'type': 'string',
        'default': PLUGIN_NAME,
        'readonly': 'true'
    },
    'enable': {
        'description': 'Enable ema plugin',
        'type': 'boolean',
        'default': 'false',
        'displayName': 'Enabled',
        'order': "3"
    },
    'rate': {
        'description': 'Rate value: include % of current value',
        'type': 'float',
        'default': '0.07',
        'displayName': 'Rate',
        'order': "2"
    },
    'datapoint': {
        'description': 'Datapoint name for calculated ema value',
        'type': 'string',
        'default': PLUGIN_NAME,
        'displayName': 'EMA datapoint',
        'order': "1"
    }
}


def compute_ema(handle, reading):
    """ Compute EMA

    Args:
        A reading data
    """
    rate = float(handle['rate']['value'])
    for attribute in list(reading):
        if not handle['latest']:
            handle['latest'] = reading[attribute]
        handle['latest'] = reading[attribute] * rate + handle['latest'] * (1 - rate)
        reading[handle['datapoint']['value']] = handle['latest']


def plugin_info():
    """ Returns information about the plugin
    Args:
    Returns:
        dict: plugin information
    Raises:
    """
    return {
        'name': 'ema',
        'version': '2.0.0',
        'mode': "none",
        'type': 'filter',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG
    }


def plugin_init(config, ingest_ref, callback):
    """ Initialise the plugin
    Args:
        config: JSON configuration document for the Filter plugin configuration category
        ingest_ref: filter ingest reference
        callback:   filter callback
    Returns:
        data: JSON object to be used in future calls to the plugin
    Raises:
    """
    _config = copy.deepcopy(config)
    _config['ingestRef'] = ingest_ref
    _config['callback'] = callback
    _config['latest'] = None
    _config['shutdownInProgress'] = False
    return _config


def plugin_reconfigure(handle, new_config):
    """ Reconfigures the plugin

    Args:
        handle: handle returned by the plugin initialisation call
        new_config: JSON object representing the new configuration category for the category
    Returns:
        new_handle: new handle to be used in the future calls
    """
    _LOGGER.info("Old config for ema plugin {} \n new config {}".format(handle, new_config))

    new_handle = copy.deepcopy(new_config)
    new_handle['shutdownInProgress'] = False
    new_handle['latest'] = None
    new_handle['ingestRef'] = handle['ingestRef']
    new_handle['callback'] = handle['callback']
    return new_handle


def plugin_shutdown(handle):
    """ Shutdowns the plugin doing required cleanup.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
        plugin shutdown
    """
    handle['shutdownInProgress'] = True
    time.sleep(1)
    handle['callback'] = None
    handle['ingestRef'] = None
    handle['latest'] = None

    _LOGGER.info('{} filter plugin shutdown.'.format(PLUGIN_NAME))


def plugin_ingest(handle, data):
    """ Modify readings data and pass it onward

    Args:
        handle: handle returned by the plugin initialisation call
        data: readings data
    """
    if handle['shutdownInProgress']:
        return

    if handle['enable']['value'] == 'false':
        # Filter not enabled, just pass data onwards
        filter_ingest.filter_ingest_callback(handle['callback'], handle['ingestRef'], data)
        return

    # Filter is enabled: compute EMA for each reading
    for elem in data:
        compute_ema(handle, elem['readings'])

    # Pass data onwards
    filter_ingest.filter_ingest_callback(handle['callback'], handle['ingestRef'], data)

    _LOGGER.debug("{} filter_ingest done.".format(PLUGIN_NAME))
