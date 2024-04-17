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
__copyright__ = "Copyright (c) 2019 Dianomic Systems"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_LOGGER = logger.setup(__name__, level = logging.WARN)

# Filter specific objects
the_callback = None
the_ingest_ref = None

# latest ema value
latest = None
# rate value
rate = None
# datapoint name
datapoint = None
# plugin shutdown indicator
shutdown_in_progress = False

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


def compute_ema(reading):
    """ Compute EMA

    Args:
        A reading data
    """
    global rate, latest, datapoint
    for attribute in list(reading):
        if not latest:
            latest = reading[attribute]
        latest = reading[attribute] * rate + latest * (1 - rate)
        reading[datapoint] = latest


def plugin_info():
    """ Returns information about the plugin
    Args:
    Returns:
        dict: plugin information
    Raises:
    """
    return {
        'name': 'ema',
        'version': '2.4.0',
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
    data = copy.deepcopy(config)

    global the_callback, the_ingest_ref, rate, datapoint

    the_callback = callback
    the_ingest_ref = ingest_ref
    rate = float(config['rate']['value'])
    datapoint = config['datapoint']['value']

    _LOGGER.debug("plugin_init for filter EMA called")

    return data


def plugin_reconfigure(handle, new_config):
    """ Reconfigures the plugin

    Args:
        handle: handle returned by the plugin initialisation call
        new_config: JSON object representing the new configuration category for the category
    Returns:
        new_handle: new handle to be used in the future calls
    """
    global rate, datapoint
    rate = float(new_config['rate']['value'])
    datapoint = new_config['datapoint']['value']
    _LOGGER.debug("Old config for ema plugin {} \n new config {}".format(handle, new_config))
    new_handle = copy.deepcopy(new_config)

    return new_handle


def plugin_shutdown(handle):
    """ Shutdowns the plugin doing required cleanup.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
        plugin shutdown
    """
    global shutdown_in_progress, the_callback, the_ingest_ref, rate, latest, datapoint
    shutdown_in_progress = True
    time.sleep(1)
    the_callback = None
    the_ingest_ref = None
    rate = None
    latest = None
    datapoint = None

    _LOGGER.info('filter ema plugin shutdown.')


def plugin_ingest(handle, data):
    """ Modify readings data and pass it onward

    Args:
        handle: handle returned by the plugin initialisation call
        data: readings data
    """
    global shutdown_in_progress, the_callback, the_ingest_ref
    if shutdown_in_progress:
        return

    if handle['enable']['value'] == 'false':
        # Filter not enabled, just pass data onwards
        filter_ingest.filter_ingest_callback(the_callback, the_ingest_ref, data)
        return

    # Filter is enabled: compute EMA for each reading
    for elem in data:
        compute_ema(elem['readings'])

    # Pass data onwards
    filter_ingest.filter_ingest_callback(the_callback, the_ingest_ref, data)

    _LOGGER.debug("ema filter_ingest done")
