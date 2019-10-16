================================
FogLAMP EMA Python filter plugin
================================

The plugin generates an exponential moving average datapoint by including a rate of current value and a rate of history values.

Runtime configuration
---------------------

The filter supports the following configuration items:

enable
  A switch to control if the filter should take effect or not

rate
  The percentage value for including current value and 100 - percentage of the history

datapoint
  the datapoint name to add with EMA value


Note: the EMA datapoint is added to each reading data passed to the filter.

