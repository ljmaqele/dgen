#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module contains utility functions and classes used to build the user interface
architecture and controls. 
"""

import wx
import logging
import logging.config
import requests
import numpy as np
import pandas as pd
import matplotlib as mpl
mpl.use('WXAgg')
import seaborn as sns
import utility_functions as utilfunc
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from wx.richtext import RichTextCtrl
from wx.html import HtmlWindow
from wx.html2 import WebView
from bs4 import BeautifulSoup

logger = utilfunc.get_logger()

class Container(wx.Panel):
    
    """
    This class represents a rectangular panel/window which can be placed into a
    parent frame for complex layouts 
    """
    
    def __init__(self, parent, bgcolor=None):
        wx.Panel.__init__(self, parent)
        if bgcolor != None:
            self.SetBackgroundColour(bgcolor)
            
            
    def place(self, parent, relx, rely, relwidth, relheight, screenheight=None, taskbar=None, statusbar=None):
        """
        This function places a container frame at a specified position onto a parent
        wx Panel

        Parameters
        ----------
        parent : wx.Frame
            Parent frame to put the window onto.
        relx : float
            A real number in the range [0, 100] specifying the relative postion of top left corner.
        rely : float
            A real number in the range [0, 100] specifying the relative postion of top left corner.
        relwidth : float
            A real number in the range [0, 100] specifying the relative width.
        relheight : float
            A real number in the range [0, 100] specifying the relative height.

        Returns
        -------
        None.

        """
        if relx > 100 or relx < 0:
            raise ValueError('Invalid value: {}, relx must be in the range [0,100]'.format(relx))
            
        if rely > 100 or rely < 0:
            raise ValueError('Invalid value: {}, rely must be in the range [0,100]'.format(rely))
            
        if relwidth > 100 or relwidth < 0:
            raise ValueError('Invalid value: {}, relwidth must be in the range [0,100]'.format(relwidth))
        
        if relheight > 100 or relheight < 0:
            raise ValueError('Invalid value: {}, relheight must be in the range [0,100]'.format(relheight))
            
        if relx + relwidth > 100:
            raise ValueError('Invalid value: {}, bottom right corner x out of bounds, must be < 100'.format(relx + relwidth))
            
        if rely + relheight > 100:
            raise ValueError('Invalid value: {}, bottom right corner y out of bounds, must be < 100'.format(rely + relheight))
        
        pixel_y = parent.Size[1]
        if taskbar != None:
            if parent.Size[1] + 42 == screenheight:
                pixel_y = pixel_y - taskbar.Size[1]
            else:
                pixel_y = pixel_y - taskbar.Size[1] - 24
        if statusbar != None:
            pixel_y = pixel_y - statusbar.Size[1]
        parent_size = parent.Size
        x_anchor = __relx__(relx/100, parent_size[0])
        y_anchor = __rely__(rely/100, pixel_y)
        width = __relwidth__(relwidth/100, parent_size[0])
        height = __relheight__(relheight/100, pixel_y)
        self.SetPosition((x_anchor, y_anchor))
        self.SetSize((width, height))



class WxDataFrame(wx.grid.Grid):
    
    """
    This class represents a table that takes data from a pandas dataframe
    """
    
    def __init__(self, parent, dataframe):
        wx.grid.Grid.__init__(self, parent)
        self.data = tuple(tuple(row) for row in dataframe.to_numpy())
        self.rowLabels = tuple(list(dataframe.index))
        self.colLabels = tuple(list(dataframe.columns))
        self.parent = parent
        self.SetSize(self.parent.Size)
        self.parent.Bind(wx.EVT_SIZE, self.on_resize)
        self.setup()
        
        
    def setup(self):
        x, y = len(self.data), len(self.data[0])
        self.CreateGrid(x, y)
        for idx, rowLabel in enumerate(self.rowLabels):
            self.SetRowLabelValue(idx, str(rowLabel))
            
        for idy, colLabel in enumerate(self.colLabels):
            self.SetColLabelValue(idy, str(colLabel))
            
        for i in range(x):
            for j in range(y):
                self.SetCellValue(i, j, str(self.data[i][j]))
                
    
    def on_resize(self, event):
        self.SetSize(self.parent.Size)



class DataVisualizer(wx.Panel):
    """
    
    """
    def __init__(self, parent, data, scenario_option, market):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.data = data
        self.scenario_option = scenario_option
        self.market = market
        self.SetBackgroundColour((0,0,0))
        self.InitVisualizer()
        self.parent.Bind(wx.EVT_SIZE, self.size)
        #self.master_plot()
        
    def InitVisualizer(self):
        self.fig = mpl.figure.Figure()
        self.ax = self.fig.add_subplot()
        self.canvas = FigureCanvas(self, -1, self.fig)
        self.dpi = self.fig.get_dpi()
        # size
        self.x, self.y = self.parent.Size
        self.SetSize((self.x, self.y))
        self.canvas.SetSize((self.x, self.y))
        self.fig.set_size_inches((self.x)/self.dpi, (self.y)/self.dpi)
        
        #self.size()
        #self.draw()
        self.master_plot()
        #self.Bind(wx.EVT_SIZE, self.size)
        
        
    def size(self, event):
        #print("DPI: ", dpi)
        self.x, self.y = self.parent.Size
        self.SetSize((self.x, self.y))
        self.canvas.SetSize((self.x, self.y))
        self.fig.set_size_inches((self.x)/self.dpi, (self.y)/self.dpi)
        self.draw()
        self.master_plot()
        self.fig.set_tight_layout(True)
        
    def resize(self, event):
        
        self._resizeflag = True
        
    def draw(self): pass
        
        
    def master_plot(self):
        
        if self.scenario_option == 'load_growth_scenario':
            self.plot_load_growth(self.data, self.market)
            
        elif self.scenario_option == 'retail_electricity_price_escalation':
            self.plot_elec_price_esc(self.data, self.market)
            
        elif self.scenario_option == 'wholesale_electricity_price':
            self.plot_wholesale_price_esc(self.data, self.market)
            
        elif self.scenario_option == 'pv_price':
            self.plot_pv_price(self.data, self.market)
            
        elif self.scenario_option == 'pv_technical_performance':
            self.plot_pv_technical_performance(self.data, self.market)
            
        elif self.scenario_option == 'storage_cost':
            self.plot_storage_cost(self.data, self.market)
            
        elif self.scenario_option == 'storage_technical_performance':
            self.plot_storage_technical_performance(self.data, self.market)
            
        elif self.scenario_option == 'pv_storage_cost':
            self.plot_pv_storage_cost(self.data, self.market)
               
        # sizer = wx.BoxSizer(wx.VERTICAL)
        # sizer.Add(self.canvas, 1, wx.EXPAND | wx.ALL)
        # self.SetSizer(sizer)
        # self.Fit()


    def plot_load_growth(self, data, market):
        
        """
        Visualize Load Growth Scenario
        """
        
        endstr = {"Residential":"res", "Commercial":"com", "Industry":"ind"}
        sns.lineplot(x='year', y='load_growth_' + endstr[market], hue='census_division_abbr', data=data, ax=self.ax)
        h, l = self.ax.get_legend_handles_labels()
        self.ax.legend(h, l, loc='lower center', bbox_to_anchor=(1.1, 0.25), title='Census Div')
        self.ax.set_ylabel('Load Growth', fontweight="bold", fontsize=12)
        self.ax.set_xlabel('Year', fontweight="bold", fontsize=12)
        
        
    def plot_elec_price_esc(self, data, market):
        
        """
        Visualize Electricity Price Escalation
        """
        
        endstr = {"Residential":"res", "Commercial":"com", "Industry":"ind"}
        
        sns.lineplot(x='year', y='elec_price_' + endstr[market], hue='ba', data=data, ax=self.ax, legend=False)
        self.ax.set_ylabel('Electricity Price Escalation', fontweight="bold", fontsize=12)
        self.ax.set_xlabel('Year', fontweight="bold", fontsize=12)
        
    
        
    def plot_wholesale_price_esc(self, data, market):
        
        """
        Visualize Wholesale Price Escalation
        """
        sns.lineplot(x='year', y='price', hue='ba', data=data, ax=self.ax, legend=False)
        self.ax.set_ylabel('Wholesale Price Escalation', fontweight="bold", fontsize=12)
        self.ax.set_xlabel('Year', fontweight="bold", fontsize=12)
        
        
    def plot_pv_price(self, data, market):
        
        endstr = {"Residential":"res", "Commercial":"com", "Industry":"ind"}
        
        data.plot(x='year', y='system_capex_per_kw_' + endstr[market], ax=self.ax, label='Capital', legend=False, color='b')
        ax2 = self.ax.twinx()
        data.plot(x='year', y='system_om_per_kw_' + endstr[market], ax=ax2, label='O&M', legend=False, color='r')
        data.plot(x='year', y='system_variable_om_per_kw_' + endstr[market], label='Variable o&M', ax=ax2, legend=False, color='k')
        self.ax.figure.legend()
        self.ax.set_ylabel('PV Capital Cost [$/kW] ', fontweight="bold", fontsize=12)
        self.ax.set_xlabel('Year', fontweight="bold", fontsize=12)
        ax2.set_ylabel('PV OM Cost [$/kW]', fontweight="bold", fontsize=12)
        
        
    def plot_pv_technical_performance(self, data, market):
        
        endstr = {"Residential":"res", "Commercial":"com", "Industry":"ind"}
        
        data.plot(x='year', y='pv_kw_per_sqft_' + endstr[market], ax=self.ax, label='PV kW', legend=False, color='b')
        ax2 = self.ax.twinx()
        data.plot(x='year', y='pv_degradation_factor_' + endstr[market], ax=ax2, label='PV Degradation', legend=False, color='r')
        self.ax.figure.legend()
        self.ax.set_ylabel('PV Size [kW/sqft]', fontweight="bold", fontsize=12)
        self.ax.set_xlabel('Year', fontweight="bold", fontsize=12)
        ax2.set_ylabel('Degradation factor', fontweight="bold", fontsize=12)
        
        
    def plot_storage_cost(self, data, market):
        
        endstr = {"Residential":"res", "Commercial":"nonres", "Industry":"nonres"}
        
        data.plot(x='year', y='batt_capex_per_kwh_'+endstr[market], ax=self.ax, label='capex kwh', legend=False, color='b', ls=':')
        data.plot(x='year', y='batt_capex_per_kw_'+endstr[market], ax=self.ax, label='capex kw', legend=False, color='b', ls='--')
        ax2 = self.ax.twinx()
        data.plot(x='year', y='batt_om_per_kwh_'+endstr[market], ax=ax2, label='om kwh', legend=False, color='r', ls=':')
        data.plot(x='year', y='batt_om_per_kw_'+endstr[market], ax=ax2, label='om kw', legend=False, color='r', ls='--')
        data.plot(x='year', y='batt_replace_frac_kwh', ax=ax2, label='replace kwh', legend=False, color='k', ls=':')
        data.plot(x='year', y='batt_replace_frac_kw', ax=ax2, label='replace kw', legend=False, color='k', ls='--')
        self.ax.figure.legend(ncol=3, loc=9)
        self.ax.set_ylabel('Capex [$]', fontweight="bold", fontsize=12)
        self.ax.set_xlabel('Year', fontweight="bold", fontsize=12)
        ax2.set_ylabel('O&M [$] / Replace Fraction', fontweight="bold", fontsize=12)
        
        
    def plot_storage_technical_performance(self, data,  market):
        
        endstr = {"Residential":"res", "Commercial":"com", "Industry":"ind"}
        
        data.plot(x='year', y='batt_eff_' + endstr[market], ax=self.ax, label='Efficiency', legend=False, color='b')
        ax2 = self.ax.twinx()
        data.plot(x='year', y='batt_lifetime_yrs_' + endstr[market], ax=ax2, label='Life', legend=False, color='r')
        self.ax.figure.legend()
        self.ax.set_ylabel('Efficiecy', fontweight="bold", fontsize=12)
        self.ax.set_xlabel('Year', fontweight="bold", fontsize=12)
        ax2.set_ylabel('Lifetime', fontweight="bold", fontsize=12)
        ax2.set_ylim(0)
        
        
    def plot_pv_storage_cost(self, data, market):
        
        endstr = {"Residential":"res", "Commercial":"nonres", "Industry":"nonres"}
        
        data.plot(x='year', y='system_capex_per_kw_'+endstr[market], ax=self.ax, label='sys capex kw', legend=False, color='b', ls='--')
        data.plot(x='year', y='batt_capex_per_kwh_'+endstr[market], ax=self.ax, label='batt capex kwh', legend=False, color='k', ls=':')
        data.plot(x='year', y='batt_capex_per_kw_'+endstr[market], ax=self.ax, label='batt capex kw', legend=False, color='k', ls='--')
        ax2 = self.ax.twinx()
        data.plot(x='year', y='batt_om_per_kwh_'+endstr[market], ax=ax2, label='batt om kwh', legend=False, color='g', ls=':')
        data.plot(x='year', y='batt_om_per_kw_'+endstr[market], ax=ax2, label='batt om kw', legend=False, color='g', ls='--')
        data.plot(x='year', y='batt_replace_frac_kwh', ax=ax2, label='batt replace kwh', legend=False, color='k', ls='-')
        data.plot(x='year', y='batt_replace_frac_kw', ax=ax2, label='batt replace kw', legend=False, color='k', ls='-.')
        self.ax.figure.legend(ncol=3, loc=9)
        self.ax.set_ylabel('Capex [$]', fontweight="bold", fontsize=12)
        self.ax.set_xlabel('Year', fontweight="bold", fontsize=12)
        ax2.set_ylabel('O&M [$] / Replace Fraction', fontweight="bold", fontsize=12)


        

class ScenariosTree(wx.TreeCtrl):
    
    
    def __init__(self, parent, scenarios):
        wx.TreeCtrl.__init__(self, parent)#, style=wx.TR_EDIT_LABELS)
        self.root = self.AddRoot("Scenarios")
        self.SetItemTextColour(self.root, wx.Colour(123, 123, 123))
        self.SetItemBold(self.root)
        self.SetItemTextColour(self.root, (255, 128, 0))
        self.add_scenario_items(scenarios)
        self.SetFont(wx.Font(10, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        
    def add_scenario_items(self, scenarios):
        if not scenarios:
            pass
        
        else:
            for idx, scen in enumerate(scenarios):
                names = list(scen)
                S = Scenario(**scen)
                item_top = self.AppendItem(self.root, S.scenario_name)
                for name in names:
                    if name != 'scenario_name':
                        item = self.AppendItem(item_top, __smartify_str__(name))
                        exec('self.AppendItem(item, S.' +name+')')
                
        
        
class LogHandler(logging.StreamHandler):
    
    def __init__(self, text_control):
        logging.StreamHandler.__init__(self)
        self.text_control = text_control

    
    def emit(self, record):
        msg = self.format(record)
        self.text_control.BeginTextColour(wx.Colour(255, 255, 255))
        self.text_control.WriteText(msg + '\n')
        self.text_control.EndTextColour()
        self.text_control.MoveEnd()
        pos = self.text_control.GetInsertionPoint()
        self.text_control.ShowPosition(pos)
        wx.Yield()
        self.flush()
        
        
        
class Logger(wx.LogTextCtrl):
    
    def __init__(self, parent):
        wx.LogTextCtrl.__init__(self, parent)
        
        
class LoggerPanel(wx.Panel):
    
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.SetSize(parent.Size)
        self.logtxt = RichTextCtrl(self, style = wx.TE_MULTILINE | wx.TE_READONLY)
        self.logtxt.SetBackgroundColour(wx.Colour(64, 64, 64))
        font1 = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Consolas')
        self.logtxt.SetFont(font1)
        self.logtxt.SetSize(self.Size)
        handler = LogHandler(self.logtxt)
        logger.addHandler(handler)
        FORMAT = "%(asctime)s %(levelname)s %(message)s"
        handler.setFormatter(logging.Formatter(FORMAT))
        logger.setLevel(logging.DEBUG)
        self.parent.Bind(wx.EVT_SIZE, self.on_resize)
        
    def on_resize(self, event):
        self.SetSize(self.parent.Size)
        self.logtxt.SetSize(self.parent.Size)
    
        
        
class WebScrapper(object):
    
    def __init__(self, 
                 url="https://github.com/NREL/dgen/wiki/Input-Sheet-Documentation",
                 ):
        
        self.url = None
        self.content = None
        self.__config__(url)
        
    def set(self, attr, value):
        
        self.__setattr__(attr, value)
        self.validate_property(attr)
        
    def get(self, attr):
        
        return self.__getattribute__(attr)
    
    def __config__(self, url):
        
        self.set('url', url)
        
    def validate_property(self, property_name):
        
        if property_name == 'url':
            try:
                page = requests.get(self.url)
                self.content = BeautifulSoup(page.content, "html.parser")
            except TypeError as e:
                raise TypeError("Invalid {0}: {1}".format(property_name, e))

    
    
class Scenario(object):
    
    def __init__(
            self, 
            scenario_name,
            technology,
            markets,
            region_to_analyze,
            agent_file,
            analysis_end_year,
            load_growth_scenario,
            retail_electricity_price_escalation_scenario,
            wholesale_electricity_price_scenario,
            pv_price_scenario,
            pv_technical_performance_scenario,
            storage_cost_scenario,
            storage_technical_performance_scenario,
            pv_storage_cost_scenario,
            financing_scenario,
            depreciation_scenario,
            value_of_resiliency_scenario,
            carbon_intensity_scenario,
            random_generator_seed,
            ):
        self.scenario_name = scenario_name
        self.technology = technology
        self.markets = markets
        self.region_to_analyze = region_to_analyze
        self.agent_file = agent_file
        self.analysis_end_year = analysis_end_year
        self.load_growth_scenario = load_growth_scenario
        self.retail_electricity_price_escalation_scenario = retail_electricity_price_escalation_scenario
        self.wholesale_electricity_price_scenario = wholesale_electricity_price_scenario
        self.pv_price_scenario = pv_price_scenario
        self.pv_technical_performance_scenario = pv_technical_performance_scenario
        self.storage_cost_scenario = pv_storage_cost_scenario
        self.storage_technical_performance_scenario = storage_technical_performance_scenario
        self.pv_storage_cost_scenario = pv_storage_cost_scenario
        self.financing_scenario = financing_scenario
        self.depreciation_scenario = depreciation_scenario
        self.value_of_resiliency_scenario = value_of_resiliency_scenario
        self.carbon_intensity_scenario = carbon_intensity_scenario
        self.random_generator_seed = random_generator_seed

    
def __prepare_data__(raw_data, analysis_end_year, market, data_class, state_abbr=None):
    
    endstr = {"Residential":"res", "Commercial":"nonres", "Industry":"nonres"}
    if data_class == 'load_growth_scenario':
        data = raw_data[raw_data.year <= analysis_end_year]
        columns = ['year', 'load_growth_'+endstr[market], 'census_division_abbr']
        return data.filter(items=columns)
        
    elif data_class == 'retail_electricity_price_escalation':
        data = raw_data[raw_data.year <= analysis_end_year]
        columns = ['year', 'elec_price_'+endstr[market], 'ba']
        return data.filter(items=columns)
        
    elif data_class == 'wholesale_electricity_price':
        years = [int(y) for y in list(raw_data.columns)[1:]]
        prices = raw_data.to_numpy()[:, 1:].flatten()
        actual_years = np.tile(years, len(prices)//len(years))
        ba = np.repeat(raw_data.ba.values, len(years))
        data = pd.DataFrame({'ba':ba, 'year':actual_years, 'price':prices})
        return data[data.year <= analysis_end_year]
        
    elif data_class == 'pv_price':
        data = raw_data[raw_data.year <= analysis_end_year]
        columns = ['year', 'system_capex_per_kw_'+endstr[market], 'system_om_per_kw_'+endstr[market],]
        columns += ['system_variable_om_per_kw_'+endstr[market]]
        return data.filter(items=columns)
        
    elif data_class == 'pv_technical_performance':
        data = raw_data[raw_data.year <= analysis_end_year]
        columns = ['year', 'pv_kw_per_sqft_'+endstr[market], 'pv_degradation_factor_'+endstr[market]]
        return data.filter(items=columns)
        
    elif data_class == 'storage_cost':
        data = raw_data[raw_data.year <= analysis_end_year]
        columns = ['year', 'batt_capex_per_kwh_'+endstr[market], 'batt_capex_per_kw_'+endstr[market]]
        columns += ['batt_om_per_kwh_'+endstr[market], 'batt_om_per_kw_'+endstr[market]]
        columns += ['batt_replace_frac_kwh'+endstr[market], 'batt_replace_frac_kwh'+endstr[market]]
        return data.filter(items=columns)
    
    elif data_class == 'storage_technical_performance':
        data = raw_data[raw_data.year <= analysis_end_year]
        columns = ['year', 'batt_eff_'+endstr[market], 'batt_lifetime_yrs_'+endstr[market]]
        return data.filter(items=columns)
        
    elif data_class == 'pv_storage_cost':
        data = raw_data[raw_data.year <= analysis_end_year]
        columns = ['year', 'system_capex_per_kw_'+endstr[market], 'batt_capex_per_kwh_'+endstr[market]]
        columns += ['batt_capex_per_kw_'+endstr[market], 'batt_om_per_kw_'+endstr[market]]
        columns += ['batt_replace_frac_kwh', 'batt_replace_frac_kw']
        return data.filter(items=columns)
        
    elif data_class == 'financing':
        data = raw_data[raw_data.year <= analysis_end_year]
        columns = ['year', 'economic_lifetime_yrs', 'long_term_yrs_'+endstr[market]]
        columns += ['loan_interest_rate_'+endstr[market], 'down_payment_fraction_'+endstr[market]]
        columns += ['real_discount_rate_'+endstr[market], 'tax_rate_'+endstr[market]]
        return data.filter(items=columns)
        
    elif data_class == 'depreciation':
        data = raw_data[raw_data.year <= analysis_end_year]
        return data[data.sector_abbr == endstr[market]]
        
    elif data_class == 'value_of_resiliency':
        data = raw_data[raw_data.sector_abbr == endstr[market]]
        return data[data.state_abbr == state_abbr]
    
    elif data_class == 'carbon_intensity':
        data = raw_data[raw_data.state_abbr == state_abbr]
        years = [int(r) for r in list(data.columns)[1:]]
        cinten = data.to_numpy()[0, 1:]
        return pd.Dataframe({'year':years, 'carbon_intensity':cinten})
        
    else:
        raise Exception("")
        

        
def __relx__(relx_, width):
    """
    Evaluate the top left x position of a widget

    Parameters
    ----------
    relx_ : 'float'
        A real number in the range [0, 1] specifying the relative postion of top left corner.
    width : 'int'
        The width of the parent window/panel.

    Returns
    -------
    'int'
        Absolute x position of the top left corner.

    """
    return int(relx_*width)

def __rely__(rely_, height):
    """
    Evaluate the top left y position of a widget

    Parameters
    ----------
    rely_ : 'float'
        A real number in the range [0, 1] specifying the relative postion of top left corner.
    width : 'int'
        The height of the parent window/panel.

    Returns
    -------
    'int'
        Absolute y position of the top left corner.

    """
    return int(rely_*height)



def __relwidth__(rel_width, width):
    """
    Evaluate the width from the top left x position of a widget

    Parameters
    ----------
    relx_width : 'float'
        A real number in the range [0, 1] specifying the relative width.
    width : 'int'
        The width of the parent window/panel.

    Returns
    -------
    'int'
        Absolute x length.

    """
    return int(rel_width*width)



def __relheight__(rel_height, height):
    """
    Evaluate the height/depth left y position of a widget

    Parameters
    ----------
    relx_ : 'float'
        A real number in the range [0, 1] specifying the relative height.
    width : 'int'
        The width of the parent window/panel.

    Returns
    -------
    'int'
        Absolute y length.

    """
    return int(rel_height*height)



def __components_spacing__(num_comps, parent, direction = 'Vertical'):
    """
    Evaluate equal space measurement for each component on a Frame 

    Parameters
    ----------
    num_comps : int
        Number of components to be placed/spaced.
    parent : wx.Frame/wx.Panel
        A parent Frame or Panel onto which the components are to be placed.
    direction : String, optional
        Direction across the parent Panel in which the components are to be placed. The default is 'Vertical'.

    Returns
    -------
    spacer : int
        The measurement of space for each component.

    """
    x_span, y_span = parent.Size
    if direction == 'Vertical':
        spacer = int(y_span/(num_comps))
    elif direction == 'Horizontal':
        spacer = int(x_span/(num_comps))
    return spacer


def __smartify_str__(string):
    
    s = string.replace('_', ' ')
    return s
        

def __reverse_smartify_str__(string):
    
    s = string.replace(' ', '_')
    return s
        