#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
cytoflow.views.stats_1d
-----------------------
'''

from traits.api import provides, Constant
import matplotlib.pyplot as plt

import numpy as np

import cytoflow.utility as util
from .i_view import IView
from .base_views import Base1DStatisticsView

@provides(IView)
class Stats1DView(Base1DStatisticsView):
    """
    Plot a statistic.  The value of the statistic will be plotted on the
    Y axis; a numeric conditioning variable must be chosen for the X axis.
    Every variable in the statistic must be specified as either the `variable`
    or one of the plot facets.
    
    Attributes
    ----------
    variable_scale : {'linear', 'log', 'logicle'}
        The scale applied to the variable (on the X axis)
        
    Examples
    --------
    
    .. plot::
        :context: close-figs
        
        Make a little data set.
    
        >>> import cytoflow as flow
        >>> import_op = flow.ImportOp()
        >>> import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
        ...                              conditions = {'Dox' : 10.0}),
        ...                    flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
        ...                              conditions = {'Dox' : 1.0})]
        >>> import_op.conditions = {'Dox' : 'float'}
        >>> ex = import_op.apply()
    
    Create and a new statistic.
    
    .. plot::
        :context: close-figs
        
        >>> ch_op = flow.ChannelStatisticOp(name = 'MeanByDox',
        ...                     channel = 'Y2-A',
        ...                     function = flow.geom_mean,
        ...                     by = ['Dox'])
        >>> ex2 = ch_op.apply(ex)
        
    View the new statistic
    
    .. plot::
        :context: close-figs
        
        >>> flow.Stats1DView(variable = 'Dox',
        ...                  statistic = ('MeanByDox', 'geom_mean'),
        ...                  xscale = 'log',
        ...                  yscale = 'log').plot(ex2)
    """
    
    # traits   
    id = Constant("edu.mit.synbio.cytoflow.view.stats1d")
    friendly_id = Constant("1D Statistics View")
    
    REMOVED_ERROR = Constant("Statistics changed dramatically in 0.5; please see the documentation")
    by = util.Removed(err_string = REMOVED_ERROR)
    yfunction = util.Removed(err_string = REMOVED_ERROR)
    ychannel = util.Removed(err_string = REMOVED_ERROR)
    xvariable = util.Deprecated(new = "variable")
    xscale = util.Deprecated(new = 'variable_scale')
    
    variable_scale = util.ScaleEnum
    
    def enum_plots(self, experiment):
        """
        Returns an iterator over the possible plots that this View can
        produce.  The values returned can be passed to :meth:`plot`.
        """
                
        return super().enum_plots(experiment)
        
    
    def plot(self, experiment, plot_name = None, **kwargs):
        """Plot a chart of a variable's values against a statistic.
        
        Parameters
        ----------
        
        variable_lim : (float, float)
            The limits on the variable axis
        
        color : a matplotlib color
            The color to plot with.  Overridden if `huefacet` is not `None`
            
        linewidth : float
            The width of the line, in points
            
        linestyle : ['solid' | 'dashed', 'dashdot', 'dotted' | (offset, on-off-dash-seq) | '-' | '--' | '-.' | ':' | 'None' | ' ' | '']
            
        marker : a matplotlib marker style
            See http://matplotlib.org/api/markers_api.html#module-matplotlib.markers
            
        markersize : int
            The marker size in points
            
        markerfacecolor : a matplotlib color
            The color to make the markers.  Overridden (?) if `huefacet` is not `None`
            
        alpha : the alpha blending value, from 0.0 (transparent) to 1.0 (opaque)
        
        Notes
        -----
                
        Other `kwargs` are passed to `matplotlib.pyplot.plot <https://matplotlib.org/devdocs/api/_as_gen/matplotlib.pyplot.plot.html>`_
        
        """
        
        if self.variable not in experiment.conditions:
            raise util.CytoflowError('variable',
                                     "Variable {} not in the experiment"
                                     .format(self.variable))
        
        if not util.is_numeric(experiment[self.variable]):
            raise util.CytoflowError('variable',
                                     "Variable {} must be numeric"
                                     .format(self.variable))
        
        variable_scale = util.scale_factory(self.variable_scale, 
                                            experiment, 
                                            condition = self.variable)
        
        super().plot(experiment, 
                     plot_name, 
                     variable_scale = variable_scale,
                     **kwargs)

    def _grid_plot(self, experiment, grid, **kwargs):

        data = grid.data
        data_scale = kwargs.pop('scale')
        variable_scale = kwargs.pop('variable_scale')

        stat = experiment.statistics[self.statistic]
        stat_name = stat.name
        if self.error_statistic[0]:
            err_stat = experiment.statistics[self.error_statistic]
            err_stat_name = err_stat.name
        else:
            err_stat = None
        
        variable_lim = kwargs.pop("variable_lim", None)
        if variable_lim is None:
            variable_lim = (variable_scale.clip(data[self.variable].min() * 0.9),
                            variable_scale.clip(data[self.variable].max() * 1.1))
                      
        lim = kwargs.pop("lim", None)
        if lim is None:
            lim = (data_scale.clip(data[stat_name].min() * 0.9),
                   data_scale.clip(data[stat_name].max() * 1.1))
            
            if self.error_statistic[0]:
                try: 
                    lim = (data_scale.clip(min([x[0] for x in data[err_stat_name]]) * 0.9),
                           data_scale.clip(max([x[1] for x in data[err_stat_name]]) * 1.1))
                except (TypeError, IndexError):
                    lim = (data_scale.clip((data[stat_name].min() - data[err_stat_name].min()) * 0.9), 
                           data_scale.clip((data[stat_name].max() + data[err_stat_name].max()) * 1.1))


        orientation = kwargs.pop('orientation', 'vertical')
        if orientation == 'vertical':
            # plot the error bars first so the axis labels don't get overwritten
            if err_stat is not None:
                grid.map(_v_error_bars, self.variable, stat_name, err_stat_name)
            
            grid.map(plt.plot, self.variable, stat_name, **kwargs)
            
            return dict(xscale = variable_scale,
                        xlim = variable_lim,
                        yscale = data_scale, 
                        ylim = lim)
        else:
            # plot the error bars first so the axis labels don't get overwritten
            if err_stat is not None:
                grid.map(_h_error_bars, stat_name, self.variable, err_stat_name)
            
            grid.map(plt.plot, stat_name, self.variable, **kwargs)
            
            return dict(yscale = variable_scale,
                        ylim = variable_lim,
                        xscale = data_scale, 
                        xlim = lim)

                
def _v_error_bars(x, y, yerr, ax = None, color = None, **kwargs):
    
    kwargs.pop('markersize', None)
    kwargs.pop('markersize', None)
    
    if isinstance(yerr.iloc[0], tuple):
        lo = [ye[0] for ye in yerr]
        hi = [ye[1] for ye in yerr]
    else:
        lo = [y.iloc[i] - ye for i, ye in yerr.reset_index(drop = True).items()]
        hi = [y.iloc[i] + ye for i, ye in yerr.reset_index(drop = True).items()]

    plt.vlines(x, lo, hi, color = color, **kwargs)
    
def _h_error_bars(x, y, xerr, ax = None, color = None, **kwargs):
    
    kwargs.pop('markersize', None)
    kwargs.pop('markersize', None)
    
    if isinstance(xerr.iloc[0], tuple):
        lo = [xe[0] for xe in xerr]
        hi = [xe[1] for xe in xerr]
    else:
        lo = [x.iloc[i] - xe for i, xe in xerr.reset_index(drop = True).items()]
        hi = [x.iloc[i] + xe for i, xe in xerr.reset_index(drop = True).items()]

    plt.hlines(y, lo, hi, color = color, **kwargs)
    
util.expand_class_attributes(Stats1DView)
util.expand_method_parameters(Stats1DView, Stats1DView.plot)
    

if __name__ == '__main__':
    import cytoflow as flow
    
    tube1 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                      conditions = {"Dox" : 10.0})
    
    tube2 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                      conditions = {"Dox" : 1.0})                      

    ex = flow.ImportOp(conditions = {"Dox" : "float"}, tubes = [tube1, tube2])
    
    thresh = flow.ThresholdOp()
    thresh.name = "Y2-A+"
    thresh.channel = 'Y2-A'
    thresh.threshold = 2005.0

    ex2 = thresh.apply(ex)
    
    s = flow.Stats1DView()
    s.by = "Dox"
    s.ychannel = "Y2-A"
    s.yfunction = np.mean
    s.huefacet = "Y2-A+"
    
    plt.ioff()
    s.plot(ex2)
    plt.show()
