#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import wx
import sys
import time
import PySAM
import config
import logging
import wx.grid
import analysis
import uiconfig
import screeninfo
import decorators
import pandas as pd
import agent_mutation
import financial_functions
import psycopg2.extras as pgx
import diffusion_functions_elec
import data_functions as datfunc
import utility_functions as utilfunc
import input_data_functions as iFuncs

from wx.html2 import WebView
from io import StringIO
from uiconfig import db_tables
from settings import (ModelSettings, ScenarioSettings)
from uiutils import (Container, WxDataFrame, DataVisualizer, ScenariosTree,
    LoggerPanel, __components_spacing__, __prepare_data__)



#==============================================================================
# raise  numpy and pandas warnings as exceptions
#==============================================================================
pd.set_option('mode.chained_assignment', None)
#==============================================================================


logger = utilfunc.get_logger()
class DGenUI(wx.Frame):
    """
    This class represents the graphical user interface (GUI) for the open source version
    of the dGen model. The GUI lets the user interact (set-up scenarios and run)
    with dGen through menus and buttons instead of using excel sheets to define inputs.
    """
    
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title)
        self.SetBackgroundColour((40, 45, 48))
        self.project_state = "Initial"
        self.current_scenario = None
        self.existing_scenario = 0
        self.scenarios = []
        self.engine = None
        self.schemas = ['time', 'date']
        self.sectors = []
        self.scenario_index = None
        self.InitUI()
    
        
    def InitUI(self):
        """
        Initializer method for the graphical user interface
        """
        file_path = os.path.dirname(__file__)
        
        # Size the GUI display
        screen = screeninfo.get_monitors()
        if self.project_state == "Initial":
            self.full_width = screen[0].width
            self.full_height = screen[0].height
            self.w = int(0.86*screen[0].width)
            self.h = int(0.8*screen[0].height)
        self.SetSize((self.w, self.h))
        
        # Add a ToolBar
        self.toolbar = self.CreateToolBar()
        # Status Bar
        self.statusbar = self.CreateStatusBar()
        
        self.toolbar.SetToolPacking(10)
        
        # Add a tool for adding a new scenario 
        add_scenario = self.toolbar.AddTool(
            toolId=wx.ID_ADD, label="+scenario", bitmap=wx.ArtProvider.GetBitmap(wx.ART_NEW), 
            bmpDisabled=wx.NullBitmap, shortHelp='New Scenario', longHelp='Click here to start a new scenario')
        self.Bind(wx.EVT_TOOL, self.new_scenario, add_scenario)
        
        # Add a tool to save current scenario
        save_scenario = self.toolbar.AddTool(
            toolId=wx.ID_SAVE, label="", bitmap=wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE), 
            shortHelp='Save Scenario')
        self.Bind(wx.EVT_TOOL, self.update_save_current_scenario, save_scenario)
        
        # Add a tool to close the GUI
        delete_scenario = self.toolbar.AddTool(
            toolId=wx.ID_CLOSE_ALL, label="", bitmap=wx.ArtProvider.GetBitmap(wx.ART_QUIT),
            shortHelp='Delete Scenario')
        self.Bind(wx.EVT_TOOL, self.delete_scenario, delete_scenario)
        
        # Add a tool to look at scenarios in descending order of creation
        bkwrd = self.toolbar.AddTool(
            toolId=wx.ID_BACKWARD, label="", bitmap=wx.ArtProvider.GetBitmap(wx.ART_GO_BACK),
            shortHelp='See Previous Scenario')
        self.Bind(wx.EVT_TOOL, self.look_scenario_backward, bkwrd)
        
        # Add a tool to look at scenarios in ascending order of creation
        fwrd = self.toolbar.AddTool(
            toolId=wx.ID_FORWARD, label="", bitmap=wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD),
            shortHelp='See Following Scenario')
        self.Bind(wx.EVT_TOOL, self.look_scenario_ahead, fwrd)
        
        # Add a tool to run saved scenarios
        run = self.toolbar.AddTool(
            toolId=wx.ID_EXECUTE, label="", bitmap=wx.Bitmap(os.path.join(file_path, "bitmaps", "play-16.png")), 
            shortHelp='Run Scenarios')
        self.Bind(wx.EVT_TOOL, self.run_dgen_model, run)
        
        # Add a help tool
        help_ = self.toolbar.AddTool(
            toolId=wx.ID_HELP, label="", bitmap=wx.ArtProvider.GetBitmap(wx.ART_HELP_PAGE),
            shortHelp='Online Documentation')
        help_web = "https://github.com/NREL/dgen/"
        self.Bind(wx.EVT_TOOL, lambda x: wx.LaunchDefaultBrowser(help_web), help_)
        
        # Add a visualization tool for outputs
        viz_out = self.toolbar.AddTool(
            toolId=wx.ID_VIEW_DETAILS, label="", bitmap=wx.Bitmap(os.path.join(file_path, "bitmaps", "export.png")),
            shortHelp='Export Outputs Visuals')
        self.Bind(wx.EVT_TOOL, self.visualize_outputs, viz_out)
        
        self.toolbar.SetBackgroundColour(wx.Colour(128,128,0))
        self.toolbar.Realize()
        
        # Create a container to show the Scenarios
        self.scenarios_tree_panel = Container(self, bgcolor=(255, 255, 255))
        self.scenarios_tree_panel.place(self, 0, 0.5, 19, 95, self.full_height, self.toolbar, self.statusbar)
        self.scenarios_tree_visual = ScenariosTree(self.scenarios_tree_panel, self.scenarios)
        self.scenarios_tree_visual.SetSize(self.scenarios_tree_panel.Size[0], self.scenarios_tree_panel.Size[1])
        
        # Create a container to set titles
        self.scenario_title_panel = Container(self, (192, 192, 192))
        self.scenario_title_display(self.scenario_title_panel, 19.0, 0.5, 12, 3)
        
        self.value_title_panel = Container(self, (192, 192, 192))
        self.value_title_display(self.value_title_panel, 31.5, 0.5, 25, 3)
        
        # Create a container for scenario option labels
        self.scen_panel = Container(self, bgcolor=(192, 192, 192))
        self.scenario_options_display(self.scen_panel, 15.0, 5, 12, 70)
        self.scen_panel.Bind(wx.EVT_LEFT_DOWN, self.scenario_input_info)
        
        # Create a container to show choices
        self.choices_panel = Container(self, bgcolor=(192, 192, 192))
        self.choices_display(self.choices_panel, 35, 11, 18, 70)
        
        # Create a border line between 
        self.console_top_border = Container(self, bgcolor=(152, 89, 247))
        self.console_top_border.place(self, 15, 74.5, 36, 0.2, self.full_height)
        
        # Create Container for progress bars
        self.scenario_progress_panel = Container(self, bgcolor=(128, 255, 0))
        self.scenario_progress_panel.place(self, 15, 74.8, 36, 12, self.full_height, self.toolbar, self.statusbar)
        
        self.scenarios_progress_panel = Container(self, bgcolor=(128, 255, 0))
        self.scenarios_progress_panel.place(self, 15, 87, 36, 13, self.full_height, self.toolbar, self.statusbar)
        
        # Add border to the left of visuals
        self.borderLeft = Container(self, bgcolor=(152, 89, 247))
        self.borderLeft.place(self, 53.5, 11, 0.5, 85, self.toolbar, self.statusbar)
        
        # Viewing options
        self.view_file_panel = Container(self, (152, 89, 247))
        self.view_file_display(self.view_file_panel, 57.0, 0.0, 43.0, 4)
        self.view_choice = wx.RadioBox(self.view_file_panel, label='View:', choices=['Figure', 'Data Summary'])
        self.view_choice.SetFont(wx.Font(10, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_SLANT, wx.FONTWEIGHT_LIGHT))
        self.view_choice.Bind(wx.EVT_RADIOBOX, self.view_option_tracker)
        
        # Splitter Window for Visualization
        self.splitter_container = Container(self, bgcolor=(128, 255, 0))
        self.splitter_container.place(self, 57.5, 7, 42.0, 90.0,self.full_height, self.toolbar, self.statusbar)
        
        self.visual_console = wx.SplitterWindow(self.splitter_container, size=self.splitter_container.Size)
        self.visual_console.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.sash_pos_changed)
        #self.visual_console.SetSashGravity(0.5)
        
        self.data_window = wx.Panel(self.visual_console)
        self.console_window = wx.Panel(self.visual_console)
        
        self.visual_console.SplitHorizontally(self.data_window, self.console_window)
        
        # Panel for the figure
        self.view_panel = Container(self.data_window, bgcolor=(64, 64, 64))
        self.view_panel.place(self.data_window, 0, 0, 100.0, 100.0)
        
        # Console
        self.console = Container(self.console_window)
        self.console.place(self.console_window, 0, 0, 100, 100)
        self.logger = LoggerPanel(self.console)
        
        # Add a menu to choose what to show
        self.view_menu_choice.Bind(wx.EVT_COMBOBOX, self.view_option_tracker)
        
        # Add the resize ability
        self.Bind(wx.EVT_SIZE, self.on_resize)
        
        self.Bind(wx.EVT_COMBOBOX, self.market_region)
        
        self.data_window.Bind(wx.EVT_SIZE, self.on_resize_splitter)
        self.console_window.Bind(wx.EVT_SIZE, self.on_resize_splitter)
        
        
        # Place the GUI on the center of the screen
        self.Center() 
        
        # Change project state
        self.project_state = "Running"
        
        
    def run_dgen_model(self, event):
        
        if not self.scenarios:
            wx.MessageBox("Cannot run model without specified scenarios", "RuntimeError", wx.OK)
        else:
            self.main()
            
        
    def on_resize(self, event):
        self.w, self.h = self.GetSize()
        self.SetSize((self.w, self.h))
        
        self.scenarios_tree_panel.place(self, 0.5, 0.5, 18, 99, self.full_height, self.toolbar, self.statusbar)
        self.scenarios_tree_visual.SetSize(self.scenarios_tree_panel.Size[0], self.scenarios_tree_panel.Size[1])
        self.scenario_title_display(self.scenario_title_panel, 19.0, 0.5, 17, 3)
        self.value_title_display(self.value_title_panel, 36.5, 0.5, 20, 3)
        self.view_file_display(self.view_file_panel, 57.0, 0.0, 43.0, 6)
        
        self.scenario_options_display(self.scen_panel, 19.0, 4, 17, 70)
        self.choices_display(self.choices_panel, 36.5, 4, 20, 70)
        self.console_top_border.place(self, 19, 74.5, 38, 0.4, self.full_height, self.toolbar, self.statusbar)
        self.scenario_progress_panel.place(self, 19, 75.0, 38, 12, self.full_height, self.toolbar, self.statusbar)
        self.scenarios_progress_panel.place(self, 19, 87.5, 38, 12, self.full_height, self.toolbar, self.statusbar)
        
        self.borderLeft.place(self, 57.0, 5, 0.2, 95, self.full_height, self.toolbar, self.statusbar)
        
        self.splitter_container.place(self, 57.5, 7, 42.0, 92.0, self.full_height, self.toolbar, self.statusbar)
        self.visual_console.SetSize(self.splitter_container.Size)
        self.view_panel.place(self.data_window, 0, 0, 100, 100)
        self.console.place(self.console_window, 0, 0, 100, 100)
     
    def on_resize_splitter(self, event):
        self.view_panel.place(self.data_window, 0, 0, 100, 100)
        self.console.place(self.console_window, 0, 0, 100, 100)
    
     
    def scenario_title_display(self, parent, relx, rely, relwidth, relheight):
        """ Controller function for the scenario options label/title window """
        parent.place(self, relx, rely, relwidth, relheight, self.full_height, self.toolbar, self.statusbar)
        x, y = parent.Size
        title_font = wx.Font(12, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_HEAVY)
        if self.project_state == 'Initial':
            exec('self.' + "lbl1" +' = wx.StaticText(parent, label= "Scenario Options:", pos=(5, y//3))')
            exec('self.' + "lbl1" + '.SetFont(title_font)')
        else:
            exec('self.' + "lbl1" + '.SetPosition((5, y//3))')
        
        
    
    def value_title_display(self, parent, relx, rely, relwidth, relheight):
        """ Display the title for the Values label"""
        parent.place(self, relx, rely, relwidth, relheight, self.full_height, self.toolbar, self.statusbar)
        x, y = parent.Size
        title_font = wx.Font(12, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_HEAVY)
        if self.project_state == 'Initial':
            exec('self.' + "lbl2" + ' = wx.StaticText(parent, label="Value:", pos=(5, y//3))')
            exec('self.' + "lbl2" + '.SetFont(title_font)')
        else:
            exec('self.' + "lbl2" + '.SetPosition((5, y//3))')
            
    
    
    def view_file_display(self, parent, relx, rely, relwidth, relheight):
        """ Controller function for which input variable to view """
        parent.place(self, relx, rely, relwidth, relheight, self.full_height, self.toolbar, self.statusbar)
        x, y = parent.Size
        options = ['Load Growth', 'Wholesale Electricity Price', 'PV Price', 
                   'Storage Cost', 'PV Storage Cost']
        title_font = wx.Font(12, wx.FONTFAMILY_SCRIPT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        if self.project_state == 'Initial':
            self.view_menu_choice = wx.ComboBox(parent, value="None", choices=options)
            self.view_menu_choice.SetFont(title_font)
            xs, ys = self.view_menu_choice.Size
            self.view_menu_choice.SetPosition((x - xs - 10, (y - ys)//2))
        else:
            xs, ys = self.view_menu_choice.Size
            self.view_menu_choice.SetPosition((x - xs - 10, (y - ys)//2))
         
        
    def scenario_options_display(self, parent, relx, rely, relwidth, relheight):
        """ Controller funtion for scenario options and info icons """
        parent.DestroyChildren()
        parent.place(self, relx, rely, relwidth, relheight, self.full_height, self.toolbar, self.statusbar)
        x, y = parent.Size
        # Create labels for scenario options
        lbl_font = wx.Font(10, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        labels = uiconfig.scenario_names
        options = uiconfig.scenario_options
        # Evaluate the spacer
        spacer = __components_spacing__(len(labels), parent)
        
        file_path = os.path.dirname(__file__)
        bitmap = os.path.join(file_path, "bitmaps", "icons8-info-16.png")
        # Put the labels for scenario options
        for i, lbl in enumerate(labels):
            exec('self.' + "label" + '_' + str(i) +' = wx.StaticText(parent, label= lbl + ":", pos = (5, spacer//3 + spacer*i), style=0, name="statictext")')
            exec('self.' + "label" + '_' + str(i)  +'.SetFont(lbl_font)')
            exec('self.' + "label" + '_' + str(i)  +'.SetForegroundColour((0,0,0))')
            exec('self.info_' + options[i] + '= wx.StaticBitmap(parent, bitmap = wx.Bitmap(' + "bitmap" + '), pos=(x-20, spacer//3 + spacer*i - 6))')
            
        
    def choices_display(self, parent, relx, rely, relwidth, relheight):
        """ Controller for scenario variable """
        parent.DestroyChildren()
        parent.place(self, relx, rely, relwidth, relheight, self.full_height, self.toolbar, self.statusbar)
        xs, ys = parent.Size
       
        font = wx.Font(10, wx.FONTFAMILY_SCRIPT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        # buttons
        butns = uiconfig.scenario_options 
        # Evaluate the spacer
        spacer = __components_spacing__(len(butns), parent)
        for i, choice in enumerate(butns):
            if choice not in ['scenario_name', 'random_generator_seed', 'agent_file']:
                exec('self.' + "choice"+ '_' + choice + '= wx.ComboBox(parent, value=uiconfig.default[choice], choices=uiconfig.hash_table[choice])')   
                exec('self.' + "choice" + '_' + choice  +'.SetFont(font)')
                exec('xs_, ys_ = self.' + "choice" + '_' + choice + '.Size')
                exec('self.' + "choice" + '_' + choice + '.SetPosition((int(xs/20), spacer//2 + spacer*i - ys_//2))') 
            else:
                exec('self.' + "choice"+ '_' + choice + '= wx.TextCtrl(parent, value=uiconfig.default[choice], size=(xs - int(xs/10), 20))')   
                exec('self.' + "choice" + '_' + choice  +'.SetFont(font)')
                exec('xs_, ys_ = self.' + "choice" + '_' + choice + '.Size')
                exec('self.' + "choice" + '_' + choice + '.SetPosition((int(xs/20), spacer//2 + spacer*i - ys_//2))')
            exec('self.' + "choice" + '_' + choice + '.SetSize((xs - int(xs/10), ys_ - 5))')
        
        
    
    def market_region(self, event):
        """ Specify market, hence modify agent file name """
        # This function will need updating or deprecating, because agent file names 
        # can be anything and that flexibility currently is not supported
        market_type = self.choice_markets.GetValue()
        region = self.choice_region_to_analyze.GetValue()
        if market_type != "None" and region != "None":
            if market_type == 'Only Residential' and region in uiconfig.regions.keys():
                self.choice_agent_file.SetValue("agent_df_base_res_" + uiconfig.regions[region] + '_revised')
            elif market_type == "Only Commercial" and region in uiconfig.regions.keys():
                self.choice_agent_file.SetValue("agent_df_base_com_" + uiconfig.regions[region] + '_revised')
        
    
        
    def view_option_tracker(self, event):
        """ Listener for which input to visualize """
        str_ = self.view_menu_choice.GetStringSelection()
        if str_ != "":
            analysis_end_year = int(self.choice_analysis_end_year.GetValue())
            market_val = self.choice_markets.GetValue()
            market = 'Residential'
            if market_val == "Only Commercial":
                market = 'Commercial'
            
            path_, file, scenario_option = self.view_selection_hashmap()[str_]
            path = os.path.join(path_, file)
            
            dataframe = pd.read_csv(path + '.csv')
            state = self.choice_region_to_analyze.GetValue()
            if state == 'None':
                data = __prepare_data__(dataframe, analysis_end_year, market, scenario_option, None)
            else:
                state_abbr = uiconfig.regions[state].upper()
                data = __prepare_data__(dataframe, analysis_end_year, market, scenario_option, state_abbr)
            
            self.view_panel.DestroyChildren()
            view_selector = self.view_choice.GetItemLabel(self.view_choice.GetSelection())
            if view_selector == "Figure":
                DataVisualizer(self.view_panel, data, scenario_option, market)
            elif view_selector == "Data Summary":
                WxDataFrame(self.view_panel, data)
        
           
           
    def scenario_input_info(self, event):
        """ Listener for information bitmaps clicking """
        x, y = event.GetPosition()
        bitmap_names = uiconfig.scenario_options
        descriptions = uiconfig.descriptions
        names = uiconfig.scenario_names
        bitmaps = []
        for name in bitmap_names:
            exec('bitmaps.append(self.info_' + name +')') 
        for i, bitmap in enumerate(bitmaps):
            result = self.description_mapper(bitmap, bitmap_names[i], x, y, descriptions)
            if result != None:
                wx.MessageBox(result, names[i], wx.OK | wx.ICON_INFORMATION)
                break
        return None
        
        
    
    def description_mapper(self, bitmap, bitmap_name, x, y, descriptions):
        """ Map information bitmaps to corresponding property descriptions """
        bx, by = bitmap.Position # bitmap position
        # Evaluate center position of bitmap
        bxc = bx + 12 
        byc = by + 12
        result = None
        # Evaluate if the x and y are within a 10 pixel radius
        if abs(bxc - x) <= 10 and abs(byc - y) <= 10:
            result = descriptions[bitmap_name]
        return result
        
    
    def scenario_tree_display(self):
        """ Show the scerios in a tree """
        self.scenarios_tree_panel.DestroyChildren()
        parent = self.scenarios_tree_panel
        x, y = parent.Size
        self.scenarios_tree_visual = ScenariosTree(self.scenarios_tree_panel, self.scenarios)
        self.scenarios_tree_visual.SetSize(x, y)
        
        
    def reset_input_scenario(self):
        """ Reset the input fields """
        for scen_op in uiconfig.scenario_options:
            if scen_op not in ['scenario_name', 'random_generator_seed']:
                exec('self.choice_' + scen_op + '.SetValue("None")')
            elif scen_op == 'scenario_name':
                exec('self.choice_' + scen_op + '.SetValue("reference")')
            elif scen_op == 'random_generator_seed':
                exec('self.choice_' + scen_op + '.SetValue("1")')
        
        
    def new_scenario(self, event):
        """ Create new scenario """
        self.current_scenario = {}
        if not self.scenarios:
            pass
        else:
            self.scenario_index = len(self.scenarios)
            self.existing_scenario = 0
            self.reset_input_scenario()
                
                
    def update_save_current_scenario(self, event):
        """ Capture inputs from the GUI """
        res = {}
        for scen_op in uiconfig.scenario_options:
            exec('res[scen_op] = self.choice_' + scen_op +'.GetValue()')
        
        if 'None' in list(res.values()):
            msg = "Incomplete input scenario cannot be saved! Fill in missing parameters."
            wx.MessageBox(msg, "Warning!", wx.OK)
        else:
            self.current_scenario = res
            if self.existing_scenario == 0:
                self.existing_scenario = 1
                if not self.scenarios:
                    self.scenarios.append(res)
                    self.scenario_index = 0
                else:
                    self.scenarios.append(res)
                    self.scenario_index = len(self.scenarios) - 1
            elif self.existing_scenario == 1:
                self.scenarios[self.scenario_index] = res
            self.scenario_tree_display()  
      
    
    def delete_scenario(self, event):
        """ Delete a selected scenario """
        if not self.scenarios:
            msg = "There are no scenarios to delete."
            wx.MessageBox(msg, "Warning!", wx.OK | wx.ICON_WARNING)
        else:
            self.scenarios.pop(self.scenario_index)
            self.scenario_tree_display()
            if len(self.scenarios) != 0:
                if self.scenario_index == 0:
                    self.scenario_index = len(self.scenarios) - 1
                else:
                    self.scenario_index -= 1
                scenario = self.scenarios[self.scenario_index]
                # View the selected scenario
                for key, value in scenario.items():
                    exec('self.choice_' + key + '.SetValue(value)')
            else:
                self.reset_input_scenario()
                
            
    
    def look_scenario_ahead(self, event):
        """ View the scenario ahead """
        if not self.scenarios:
            msg = "There are no scenarios to view."
            wx.MessageBox(msg, "Warning!", wx.OK | wx.ICON_WARNING)
            
        if self.scenario_index == len(self.scenarios) - 1:
            msg = "There are no more scenarios to view in this direction."
            wx.MessageBox(msg, "Warning!", wx.OK | wx.ICON_WARNING)
        else:
            self.existing_scenario = 1
            scenario = self.scenarios[self.scenario_index + 1]
            self.scenario_index += 1
            # View the selected scenario
            for key, value in scenario.items():
                exec('self.choice_' + key + '.SetValue(value)')
            
        
    def look_scenario_backward(self, event):
        """ View the scenario backward """
        if not self.scenarios:
            msg = 'There are no scenarios to view.'
            wx.MessageBox(msg, 'Warning!', wx.OK | wx.ICON_WARNING)
            
        if self.scenario_index == 0:
            msg = "There are no more scenarios to view in this direction."
            wx.MessageBox(msg, "Warning!", wx.OK | wx.ICON_WARNING)
        else:
            self.existing_scenario = 1
            scenario = self.scenarios[self.scenario_index - 1]
            self.scenario_index -= 1
            # View the selected scenario
            for key, value in scenario.items():
                exec('self.choice_' + key + '.SetValue(value)')
                
    def visualize_outputs(self, event):
        if not self.schemas:
            msg = "There are no results yet to be shown! Run the model to get some results first."
            wx.MessageBox(msg, "Warning!", wx.OK | wx.ICON_WARNING)
        else:
            dialog = wx.TopLevelWindow(self, size=(400, 300), title='Visualize Outputs')
            identifiers = {}
            for schema in self.schemas:
                identifiers[schema.split('_')[-1]] = schema
            choice = wx.CheckListBox(dialog, choices=list(identifiers.keys()), name="Scenario Names")
            dialog.Show()
          
          
    def scenario_to_csv(self, input_scenario, output_dir):
        """ Save the scenario inputs in a csv """
        x = input_scenario
        df = pd.DataFrame(dict(zip([i for i in x.keys()],[[j] for j in x.values()])))
        df.to_csv(os.path.join(output_dir, input_scenario['scenario_name'], 'input_data',  'scenario_inputs.csv'))
        
    
    def view_selection_hashmap(self):
        res = {
            'Load Growth':(
                uiconfig.load_growth_path, 
                self.choice_load_growth_scenario.GetValue(),
                'load_growth_scenario'
                ),
            'Retail Electricity Price Escalation':(
                uiconfig.re_price_esc_path,
                self.choice_retail_electricity_price_escalation_scenario.GetValue(),
                'retail_electricity_price_escalation'
                ),
            'Wholesale Electricity Price':(
                uiconfig.wh_price_esc_path, 
                self.choice_wholesale_electricity_price_scenario.GetValue(), 
                'wholesale_electricity_price'
                ),
            'PV Price':(
                uiconfig.pv_price_scenarios_path,
                self.choice_pv_price_scenario.GetValue(),
                'pv_price'
                ),
            'PV Technical Performance':(
                uiconfig.pv_technical_performance_path,
                self.choice_pv_technical_performance_scenario.GetValue(),
                'pv_technical_performance'
                ),
            'Storage Cost':(
                uiconfig.storage_cost_scenarios_path,
                self.choice_storage_cost_scenario.GetValue(), 
                'storage_cost'
                ),
            'Storage Technical Performance':(
                uiconfig.storage_tech_performance_scenarios_path,
                self.choice_storage_technical_performance_scenario.GetValue(),
                'storage_technical_performance'
                ),
            'PV Storage Cost':(
                uiconfig.pv_storage_cost_scenarios_path, 
                self.choice_pv_storage_cost_scenario.GetValue(), 
                'pv_storage_cost'
                ),
            'Financing':(
                uiconfig.financing_scenarios_path,
                self.choice_financing_scenario.GetValue(),
                'financing'
                ),
            'Depreciation':(
                uiconfig.depreciation_scenarios_path, 
                self.choice_depreciation_scenario.GetValue(),
                'depreciation'
                ),
            'Value of Resiliency':(
                uiconfig.value_of_res_scenarios_path, 
                self.choice_value_of_resiliency_scenario.GetValue(), 
                'value_of_resiliency'
                ),
            'Carbon intensity':(
                uiconfig.carbon_intensity_scenarios_path, 
                self.choice_carbon_intensity_scenario.GetValue(),
                'carbon_intensity')
            }
        return res
        
        
    def init_model_settings(self):
        """initialize Model Settings object (this controls settings that apply to all scenarios to be executed)"""
        # initialize Model Settings object (this controls settings that apply to
        # all scenarios to be executed)
        model_settings = ModelSettings()

        # add the config to model settings; set model starting time, output directory based on run time, etc.
        model_settings.add_config(config)
        model_settings.set('model_init', utilfunc.get_epoch_time())
        model_settings.set('cdate', utilfunc.get_formatted_time())
        model_settings.set('out_dir', datfunc.make_output_directory_path(model_settings.cdate))
        model_settings.set('input_data_dir', '{}/input_data'.format(os.path.dirname(os.getcwd())))
        model_settings.set('input_agent_dir', '{}/input_agents'.format(os.path.dirname(os.getcwd())))
        model_settings.set('input_scenarios', self.scenarios)
        # validate all model settings
        model_settings.validate()

        return model_settings
    
    
    def init_scenario_settings(self, scenario_file, index, model_settings, con, cur):
        """load scenario specific data and configure output settings"""
        scenario_settings = ScenarioSettings()
        scenario_settings.set('input_scenario', scenario_file)

        logger.info("-------------Preparing Database-------------")
        # =========================================================================
        # DEFINE SCENARIO SETTINGS
        # =========================================================================
        try:
            # create an empty schema from diffusion_template
            new_schema = datfunc.create_output_schema(model_settings.pg_conn_string, model_settings.role, model_settings.cdate, model_settings.input_scenarios, index, source_schema = 'diffusion_template', include_data = False)
            
        except Exception as e:
            raise Exception('\tCreation of output schema failed with the following error: {}'.format(e))
        
        # set the schema
        scenario_settings.set('schema', new_schema)

        # load Input Scenario to the new schema
        try:
           # excel_functions.load_scenario(scenario_settings.input_scenario, scenario_settings.schema, con, cur)
            self.scenario_to_postgres(con, cur, scenario_settings.schema, scenario_file)
        except Exception as e:
            raise Exception('\tLoading failed with the following error: {}'.format(e))

        # read in high level scenario settings
        scenario_settings.set('techs', datfunc.get_technologies(con, scenario_settings.schema))

        # read in settings whether to use pre-generated agent file ('User Defined'- provide pkl file name) or generate new agents
        scenario_settings.set('agent_file_status', datfunc.get_agent_file_scenario(con, scenario_settings.schema))

        # Set scenario output dir

        # set tech_mode
        scenario_settings.set_tech_mode()
        scenario_settings.set('sectors', datfunc.get_sectors(cur, scenario_settings.schema))
        scenario_settings.add_scenario_options(datfunc.get_scenario_options(cur, scenario_settings.schema, model_settings.pg_params))
        scenario_settings.set('model_years', datfunc.create_model_years(model_settings.start_year, scenario_settings.end_year))
        scenario_settings.set('state_to_model', datfunc.get_state_to_model(con, scenario_settings.schema))
        # validate scenario settings
        scenario_settings.validate()

        return scenario_settings
        
        
    @decorators.fn_timer(logger=logger, tab_level=1, prefix='')   
    def scenario_to_postgres(self, connection, cursor, schema, scenario):
        logger.info('Loading Scenario')
        
        main_scen_opts = [['User Defined'] for i in range(19)]
        main_scen_opts[0][0] = scenario['scenario_name']
        main_scen_opts[1][0] = scenario['technology']
        main_scen_opts[2][0] = 'Use pre-generated Agents'
        main_scen_opts[3][0] = scenario['region_to_analyze']
        main_scen_opts[4][0] = scenario['markets']
        main_scen_opts[5][0] = int(scenario['analysis_end_year'])
        main_scen_opts[6][0] = 'AEO2019 Reference'
        main_scen_opts[18][0] = int(scenario['random_generator_seed'])
        
        main_scen_cols = [str(i) for i in range(19)]
        
        main_scen_df = pd.DataFrame(dict(zip(main_scen_cols, main_scen_opts)))
        
        dict_0 = {'input_main':main_scen_df}
        
        scenario['load_growth_scenario'] = 'AEO2019 Reference'
        dict_0.update(self.dict_to_dfs(scenario))
        
        # Load Mappings
        mappings = pd.read_csv('table_range_lkup.csv')
        # only run the mappings that are marked to run
        mappings = mappings[mappings.run == True]
        for tablekey, dataframe in dict_0.items():
            try:
                table = db_tables[tablekey]
                if table in mappings.table.values:
                    self.df_to_postgres(connection, cursor, schema, table, dataframe)
            except:
                pass
            

    @staticmethod
    def df_to_postgres(connection, cursor, schema, table, dataframe, index = False, header = False, overwrite = True):
        """
        Copty contents of the dataframe into a postgres database

        """
        s = StringIO()
        try:
            dataframe.to_csv(s, sep = ',', index = index, header = header)
        except:
            dataframe.to_csv(s, index = index, header = header)  
        s.seek(0)
        
        connection.commit()           
        if overwrite == True:
            sql = 'DELETE FROM {}.{};'.format(schema, table)
            cursor.execute(sql)
            connection.commit()

        sql = '{}.{}'.format(schema, table)
        cursor.copy_from(s, sql, sep = ',', null = '')
        connection.commit()    
        
        # release the string io object
        s.close()      
        
        
    @staticmethod    
    def dict_to_dfs(dict):
        """
        Convert dictionary of key-val pair to key-dataframe(val) pair
        """
        dfs = {}
        for key, val in dict.items():
            dfs[key] = pd.DataFrame([val])
        return dfs    

    
    def main(self, mode = None, resume_year = None, endyear = None, ReEDS_inputs = None):
        """
        Compute the economic adoption of distributed generation resources on an agent-level basis.
        Model output is saved to a `/runs` file within the dGen directory as well as in the "agent_outputs"
        table within the new schema created upon each model run.
        """
    
        try:
            # =====================================================================
            # SET UP THE MODEL TO RUN
            # =====================================================================
    
            # initialize Model Settings object
            # (this controls settings that apply to all scenarios to be executed)
            model_settings = self.init_model_settings()
            
            # make output directory
            os.makedirs(model_settings.out_dir)
            # create the logger
            logger = utilfunc.get_logger(os.path.join(model_settings.out_dir, 'dg_model.log'))
    
            # connect to Postgres and configure connection
            con, cur = utilfunc.make_con(model_settings.pg_conn_string, model_settings.role)
            engine = utilfunc.make_engine(model_settings.pg_engine_string)
            self.engine = engine
            
            # register access to hstore in postgres
            pgx.register_hstore(con)  
    
            logger.info("Connected to Postgres with the following params:\n{}".format(model_settings.pg_params_log))
            owner = model_settings.role
    
            # =====================================================================
            # LOOP OVER SCENARIOS
            # =====================================================================
            
            # variables used to track outputs
            scenario_names = []
            dup_n = 1
            out_subfolders = {'wind': [], 'solar': []}
            for i, scenario_file in enumerate(model_settings.input_scenarios):
            
                logger.info('============================================')
                logger.info('============================================')
                logger.info("Running Scenario {i} of {n}".format(i=i + 1,n=len(model_settings.input_scenarios)))
                
                # initialize ScenarioSettings object
                # (this controls settings that apply only to this specific scenario)
                scenario_settings = self.init_scenario_settings(scenario_file, i, model_settings, con, cur)
                scenario_settings.input_data_dir = model_settings.input_data_dir
                self.schemas.append(scenario_settings.schema)
                self.sectors.append(scenario_settings.sectors)
                
                # summarize high level secenario settings
                datfunc.summarize_scenario(scenario_settings, model_settings)
    
                # create output folder for this scenario
                input_scenario = scenario_settings.input_scenario
                scen_name = scenario_settings.scen_name
                out_dir = model_settings.out_dir
        
                (out_scen_path, scenario_names, dup_n) = datfunc.create_scenario_results_folder(input_scenario, scen_name,
                                                                 scenario_names, out_dir, dup_n)
                                                                 
                # create folder for input data csvs for this scenario
                scenario_settings.dir_to_write_input_data = out_scen_path + '/input_data'
                scenario_settings.scen_output_dir = out_scen_path
                os.makedirs(scenario_settings.dir_to_write_input_data)
                
                                                                 
                # save the input scenario
                self.scenario_to_csv(scenario_file, out_dir)
                
                # get other datasets needed for the model run
                logger.info('Getting various scenario parameters')
    
                schema = scenario_settings.schema
                max_market_share = datfunc.get_max_market_share(con, schema)
                load_growth_scenario = scenario_settings.load_growth.lower()
                inflation_rate = datfunc.get_annual_inflation(con, scenario_settings.schema)
                bass_params = datfunc.get_bass_params(con, scenario_settings.schema)
    
                # get settings whether to use pre-generated agent file ('User Defined'- provide pkl file name) or generate new agents
                agent_file_status = scenario_settings.agent_file_status
    
                #==========================================================================================================
                # CREATE AGENTS
                #==========================================================================================================
                logger.info("--------------Creating Agents---------------")
                
                if scenario_settings.techs in [['wind'], ['solar']]:
    
                    # =========================================================
                    # Initialize agents
                    # =========================================================   
                               
                    solar_agents = iFuncs.import_agent_file(scenario_settings, con, cur, engine, model_settings, agent_file_status, input_name='agent_file')   
    
                    # Get set of columns that define agent's immutable attributes
                    cols_base = list(solar_agents.df.columns)
    
                #==============================================================================
                # TECHNOLOGY DEPLOYMENT
                #==============================================================================
    
                if scenario_settings.techs == ['solar']:
                    # get incentives and itc inputs
                    state_incentives = datfunc.get_state_incentives(con)
                    itc_options = datfunc.get_itc_incentives(con, scenario_settings.schema)
                    nem_state_capacity_limits = datfunc.get_nem_state(con, scenario_settings.schema)
                    nem_state_and_sector_attributes = datfunc.get_nem_state_by_sector(con, scenario_settings.schema)
                    nem_utility_and_sector_attributes = datfunc.get_nem_utility_by_sector(con, scenario_settings.schema)
                    nem_selected_scenario = datfunc.get_selected_scenario(con, scenario_settings.schema)
                    rate_switch_table = agent_mutation.elec.get_rate_switch_table(con)
    
                    #==========================================================================================================
                    # INGEST SCENARIO ENVIRONMENTAL VARIABLES
                    #==========================================================================================================
                    deprec_sch = iFuncs.import_table( scenario_settings, con, engine, owner, input_name ='depreciation_schedules', csv_import_function=iFuncs.deprec_schedule)
                    carbon_intensities = iFuncs.import_table( scenario_settings, con, engine,owner, input_name='carbon_intensities', csv_import_function=iFuncs.melt_year('grid_carbon_intensity_tco2_per_kwh'))
                    wholesale_elec_prices = iFuncs.import_table( scenario_settings, con, engine, owner, input_name='wholesale_electricity_prices', csv_import_function=iFuncs.process_wholesale_elec_prices)
                    pv_tech_traj = iFuncs.import_table( scenario_settings, con, engine, owner,input_name='pv_tech_performance', csv_import_function=iFuncs.stacked_sectors)
                    elec_price_change_traj = iFuncs.import_table( scenario_settings, con, engine, owner,input_name='elec_prices', csv_import_function=iFuncs.process_elec_price_trajectories)
                    load_growth = iFuncs.import_table( scenario_settings, con, engine, owner,input_name='load_growth', csv_import_function=iFuncs.stacked_sectors)
                    pv_price_traj = iFuncs.import_table( scenario_settings, con, engine, owner,input_name='pv_prices', csv_import_function=iFuncs.stacked_sectors)
                    batt_price_traj = iFuncs.import_table( scenario_settings, con, engine,owner, input_name='batt_prices', csv_import_function=iFuncs.stacked_sectors)
                    pv_plus_batt_price_traj = iFuncs.import_table( scenario_settings, con, engine,owner, input_name='pv_plus_batt_prices', csv_import_function=iFuncs.stacked_sectors)
                    financing_terms = iFuncs.import_table( scenario_settings, con, engine, owner,input_name='financing_terms', csv_import_function=iFuncs.stacked_sectors)
                    batt_tech_traj = iFuncs.import_table( scenario_settings, con, engine, owner,input_name='batt_tech_performance', csv_import_function=iFuncs.stacked_sectors)
                    value_of_resiliency = iFuncs.import_table( scenario_settings, con, engine,owner, input_name='value_of_resiliency', csv_import_function=None)
    
                    #==========================================================================================================
                    # Calculate Tariff Components from ReEDS data
                    #==========================================================================================================
                    for i, year in enumerate(scenario_settings.model_years):
    
                        logger.info('\tWorking on {}'.format(year))
    
                        # determine any non-base-year columns and drop them
                        cols = list(solar_agents.df.columns)
                        cols_to_drop = [x for x in cols if x not in cols_base]
                        solar_agents.df.drop(cols_to_drop, axis=1, inplace=True)
    
                        # copy the core agent object and set their year
                        solar_agents.df['year'] = year
    
                        # is it the first model year?
                        is_first_year = year == model_settings.start_year
    
                        # get and apply load growth
                        solar_agents.on_frame(agent_mutation.elec.apply_load_growth, (load_growth))
    
                        # Update net metering and incentive expiration
                        cf_during_peak_demand = pd.read_csv('cf_during_peak_demand.csv') # Apply NEM on generation basis, i.e. solar capacity factor during peak demand
                        peak_demand_mw = pd.read_csv('peak_demand_mw.csv')
                        if is_first_year:
                            last_year_installed_capacity = agent_mutation.elec.get_state_starting_capacities(con, schema)
    
                        state_capacity_by_year = agent_mutation.elec.calc_state_capacity_by_year(con, schema, load_growth, peak_demand_mw, is_first_year, year,solar_agents,last_year_installed_capacity)
                        
                        #Apply net metering parameters
                        net_metering_state_df, net_metering_utility_df = agent_mutation.elec.get_nem_settings(nem_state_capacity_limits, nem_state_and_sector_attributes, nem_utility_and_sector_attributes, nem_selected_scenario, year, state_capacity_by_year, cf_during_peak_demand)
                        
                        # update NEM sunset year to reflect actual expiration
                        if is_first_year == False:
                            nem_state_capacity_limits.loc[nem_state_capacity_limits.state_abbr.isin(net_metering_state_df.state_abbr.loc[net_metering_state_last_year_df.pv_pctload_limit.notnull() & net_metering_state_df.pv_pctload_limit.isnull()]),'sunset_year'] = year
                        net_metering_state_last_year_df = net_metering_state_df
                        
                        solar_agents.on_frame(agent_mutation.elec.apply_export_tariff_params, [net_metering_state_df, net_metering_utility_df])
    
                        # Apply each agent's electricity price change and assumption about increases
                        solar_agents.on_frame(agent_mutation.elec.apply_elec_price_multiplier_and_escalator, [year, elec_price_change_traj])
    
                        # Apply technology performance
                        solar_agents.on_frame(agent_mutation.elec.apply_batt_tech_performance, (batt_tech_traj))
                        solar_agents.on_frame(agent_mutation.elec.apply_pv_tech_performance, pv_tech_traj)
    
                        # Apply technology prices
                        solar_agents.on_frame(agent_mutation.elec.apply_pv_prices, pv_price_traj)
                        solar_agents.on_frame(agent_mutation.elec.apply_batt_prices, [batt_price_traj, batt_tech_traj, year])
                        solar_agents.on_frame(agent_mutation.elec.apply_pv_plus_batt_prices, [pv_plus_batt_price_traj, batt_tech_traj, year])
    
                        # Apply value of resiliency
                        solar_agents.on_frame(agent_mutation.elec.apply_value_of_resiliency, value_of_resiliency)
    
                        # Apply depreciation schedule
                        solar_agents.on_frame(agent_mutation.elec.apply_depreciation_schedule, deprec_sch)
    
                        # Apply carbon intensities
                        solar_agents.on_frame(agent_mutation.elec.apply_carbon_intensities, carbon_intensities)
    
                        # Apply wholesale electricity prices
                        solar_agents.on_frame(agent_mutation.elec.apply_wholesale_elec_prices, wholesale_elec_prices)
    
                        # Apply host-owned financial parameters
                        solar_agents.on_frame(agent_mutation.elec.apply_financial_params, [financing_terms, itc_options, inflation_rate])
    
                        if 'ix' not in os.name: 
                            cores = None
                        else:
                            cores = model_settings.local_cores
    
                        # Apply state incentives
                        solar_agents.on_frame(agent_mutation.elec.apply_state_incentives, [state_incentives, year, model_settings.start_year, state_capacity_by_year])
                        
                        # Calculate System Financial Performance
                        solar_agents.chunk_on_row(financial_functions.calc_system_size_and_performance, sectors=scenario_settings.sectors,  cores=cores, rate_switch_table=rate_switch_table)
    
                        # Calculate the financial performance of the S+S systems
                        #solar_agents.on_frame(financial_functions.calc_financial_performance)
    
                        # Calculate Maximum Market Share
                        solar_agents.on_frame(financial_functions.calc_max_market_share, max_market_share)
    
                        # determine "developable" population
                        solar_agents.on_frame(agent_mutation.elec.calculate_developable_customers_and_load)
    
                        # Apply market_last_year
                        if is_first_year == True:
                            state_starting_capacities_df = agent_mutation.elec.get_state_starting_capacities(con, schema)
                            solar_agents.on_frame(agent_mutation.elec.estimate_initial_market_shares, state_starting_capacities_df)
                            market_last_year_df = None
                        else:
                            solar_agents.on_frame(agent_mutation.elec.apply_market_last_year, market_last_year_df)
    
                        # Calculate diffusion based on economics and bass diffusion
                        solar_agents.df, market_last_year_df = diffusion_functions_elec.calc_diffusion_solar(solar_agents.df, is_first_year, bass_params, year)
    
                        # Estimate total generation
                        solar_agents.on_frame(agent_mutation.elec.estimate_total_generation)
    
                        # Aggregate results
                        scenario_settings.output_batt_dispatch_profiles = True
    
                        last_year_installed_capacity = solar_agents.df[['state_abbr','system_kw_cum','batt_kw_cum','batt_kwh_cum','year']].copy()
                        last_year_installed_capacity = last_year_installed_capacity.loc[last_year_installed_capacity['year'] == year]
                        last_year_installed_capacity = last_year_installed_capacity.groupby('state_abbr')[['system_kw_cum','batt_kw_cum','batt_kwh_cum']].sum().reset_index()
    
                        #==========================================================================================================
                        # WRITE AGENT DF AS PICKLES FOR POST-PROCESSING
                        #==========================================================================================================
                        write_annual_agents = True
                        drop_fields = ['index', 'reeds_reg', 'customers_in_bin_initial', 'load_kwh_per_customer_in_bin_initial',
                                       'load_kwh_in_bin_initial', 'sector', 'roof_adjustment', 'load_kwh_in_bin', 'naep',
                                       'first_year_elec_bill_savings_frac', 'metric', 'developable_load_kwh_in_bin', 'initial_number_of_adopters', 'initial_pv_kw', 
                                       'initial_market_share', 'initial_market_value', 'market_value_last_year', 'teq_yr1', 'mms_fix_zeros', 'ratio', 
                                       'teq2', 'f', 'new_adopt_fraction', 'bass_market_share', 'diffusion_market_share', 'new_market_value', 'market_value', 'total_gen_twh',
                                       'consumption_hourly', 'solar_cf_profile', 'tariff_dict', 'deprec_sch', 'batt_dispatch_profile',
                                       'cash_flow', 'cbi', 'ibi', 'pbi', 'cash_incentives', 'state_incentives', 'export_tariff_results']
                        drop_fields = [x for x in drop_fields if x in solar_agents.df.columns]
                        df_write = solar_agents.df.drop(drop_fields, axis=1)
    
                        if write_annual_agents==True:
                            df_write.to_pickle(out_scen_path + '/agent_df_{}.pkl'.format(year))
    
                        # Write Outputs to the database
                        if i == 0:
                            write_mode = 'replace'
                        else:
                            write_mode = 'append'
                        iFuncs.df_to_psql(df_write, engine, schema, owner,'agent_outputs', if_exists=write_mode, append_transformations=True)
    
                        del df_write
    
                elif scenario_settings.techs == ['wind']:
                    logger.error('Wind not yet supported')
                    break
                
                #==============================================================================
                #    Outputs & Visualization
                #==============================================================================
                logger.info("---------Saving Model Results---------")
                out_subfolders = datfunc.create_tech_subfolders(out_scen_path, scenario_settings.techs, out_subfolders)
                
    
            #####################################################################
            # drop the new scenario_settings.schema
            engine.dispose()
            con.close()
            datfunc.drop_output_schema(model_settings.pg_conn_string, scenario_settings.schema, model_settings.delete_output_schema)
            #####################################################################
            
            logger.info("-------------Model Run Complete-------------")
            time_to_complete = time.time() - model_settings.model_init
            logger.info('Completed in: {} seconds'.format(round(time_to_complete, 1)))
    
        except Exception as e:
            # close the connection (need to do this before dropping schema or query will hang)
            if 'engine' in locals():
                engine.dispose()
            if 'con' in locals():
                con.close()
            if 'logger' in locals():
                logger.error(e.__str__(), exc_info = True)
            if 'scenario_settings' in locals() and scenario_settings.schema is not None:
                # drop the output schema
                datfunc.drop_output_schema(model_settings.pg_conn_string, scenario_settings.schema, model_settings.delete_output_schema)
            if 'logger' not in locals():
                raise
    
        finally:
            if 'con' in locals():
                con.close()
            if 'scenario_settings' in locals() and scenario_settings.schema is not None:
                # drop the output schema
                datfunc.drop_output_schema(model_settings.pg_conn_string, scenario_settings.schema, model_settings.delete_output_schema)
            if 'logger' in locals():
                utilfunc.shutdown_log(logger)
                utilfunc.code_profiler(model_settings.out_dir)
                
                
                
                
def __main__():
    app = wx.App()
    app_ = DGenUI(None, 'NREL dGen Model')
    app_.Show()
    app.MainLoop()
    
    
    
    
if __name__=='__main__':
    
    __main__()
    




