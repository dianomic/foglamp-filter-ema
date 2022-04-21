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
__copyright__ = "Copyright (c) 2022 Dianomic Systems"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_LOGGER = logger.setup(__name__, level = logging.WARN)

_DEFAULT_CONFIG = {
    'plugin': {
        'description': 'Exponential Moving Average filter plugin',
        'type': 'string',
        'default': 'ema',
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
        'default': 'ema',
        'displayName': 'EMA datapoint',
        'order': "1"
    }
}


def compute_ema(handle, reading):
    """ Compute EMA

    Args:
        A reading data
    """
    for attribute in list(reading):
        if not handle['latest']:
            handle['latest'] = reading[attribute]
        handle['latest'] = reading[attribute] * handle['rate'] + handle['latest'] * (1 - handle['rate'])
        reading[handle['datapoint']] = handle['latest']


def plugin_info():
    """ Returns information about the plugin
    Args:
    Returns:
        dict: plugin information
    Raises:
    """
    return {
        'name': 'ema',
        'version': '1.9.2',
        'mode': "none",
        'type': 'filter',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG
    }


def plugin_init(config, ingest_ref, callback):
    """ Initialise the plugin
    Args:
        config: JSON configuration document for the Filter plugin configuration category
        ingest_ref:
        callback:
    Returns:
        data: JSON object to be used in future calls to the plugin
    Raises:
    """
    _config = copy.deepcopy(config)

    _config['ingest_ref'] = ingest_ref
    _config['callback'] = callback
    _config['latest'] = None

    _config['rate'] = float(config['rate']['value'])
    _config['datapoint'] = config['datapoint']['value']
    _config['shutdown_in_progress'] = False

    _LOGGER.debug("plugin_init for filter EMA called")

    return _config


def plugin_reconfigure(handle, new_config):
    """ Reconfigures the plugin

    Args:
        handle: handle returned by the plugin initialisation call
        new_config: JSON object representing the new configuration category for the category
    Returns:
        new_handle: new handle to be used in the future calls
    """
    handle['rate'] = float(new_config['rate']['value'])
    handle['datapoint'] = new_config['datapoint']['value']
    _LOGGER.debug("Old config for ema plugin {} \n new config {}".format(handle, new_config))

    new_handle = copy.deepcopy(new_config)
    new_handle['rate'] = float(config['rate']['value'])
    new_handle['datapoint'] = config['datapoint']['value']
    new_handle['shutdown_in_progress'] = False
    new_handle['latest'] = None
    new_handle['ingest_ref'] = ingest_ref
    new_handle['callback'] = callback

    return new_handle


def plugin_shutdown(handle):
    """ Shutdowns the plugin doing required cleanup.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
        plugin shutdown
    """
    handle['shutdown_in_progress'] = True
    time.sleep(1)
    handle['callback'] = None
    handle['ingest_ref'] = None
    handle['latest'] = None

    _LOGGER.info('filter ema plugin shutdown.')


def plugin_ingest(handle, data):
    """ Modify readings data and pass it onward

    Args:
        handle: handle returned by the plugin initialisation call
        data: readings data
    """
    if handle['shutdown_in_progress']:
        return

    if handle['enable']['value'] == 'false':
        # Filter not enabled, just pass data onwards
        filter_ingest.filter_ingest_callback(handle['callback'],
                                             handle['ingest_ref'],
                                             data)
        return

    # Filter is enabled: compute EMA for each reading
    for elem in data:
        compute_ema(handle, elem['readings'])

    # Pass data onwards
    filter_ingest.filter_ingest_callback(handle['callback'],
                                         handle['ingest_ref'],
                                         data)

    _LOGGER.debug("ema filter_ingest done")
