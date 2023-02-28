#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import numpy as np


# get the path of the current file
model_path = os.path.dirname(os.path.abspath(__file__))

#==============================================================================
# Technologies
#============================================================================== 
techs = ['Solar + Storage']


#==============================================================================
# Region to analyze
#============================================================================== 
regions = {'PJM':'pjm', 
           'MISO':'miso',
           'ERCOT':'ercot',
           'CAISO':'caiso',
           'NYISO':'nyiso',
           'NEISO':'neiso',
           'SPP':'spp',
           'United States':'us',
           'Alabama':'al',
           'Arizona':'az',
           'Arkansas':'ar',
           'California':'ca',
           'Colorado':'co',
           'Connecticut':'ct',
           'Delaware':'de',
           'District of Columbia':'dc',
           'Florida':'fl',
           'Georgia':'ga',
           'Idaho':'id', 
           'Illinois':'il',
           'Indiana':'in', 
           'Iowa':'ia', 
           'Kansas':'ks',
           'Kentucky':'ky',
           'Louisiana':'la',
           'Maine':'me', 
           'Maryland':'md',
           'Massachusetts':'ma',
           'Michigan':'mi', 
           'Minnesota':'mn',
           'Mississipi':'ms', 
           'Missouri':'mo', 
           'Montana':'mt', 
           'Nebraska':'ne',
           'Nevada':'nv', 
           'New Hampshire':'nh',
           'New Jersey':'nj',
           'New Mexico':'nm', 
           'New York':'ny', 
           'North Carolina':'nc', 
           'North Dakota':'nd',
           'Ohio':'oh', 
           'Oklahoma':'ok', 
           'Oregon':'or',
           'Pennsylvania':'pa',
           'Rhode Island':'ri', 
           'South Carolina':'sc',
           'South Dakota':'sd', 
           'Tennessee':'tn',
           'Texas':'tx',
           'Utah':'ut', 
           'Vermont':'vt',
           'Virginia':'va',
           'Washington':'wa',
           'West Virginia':'wv', 
           'Winsconsin':'wi',
           'Wyoming':'wy'}


#==============================================================================
# Markets
#============================================================================== 
markets = ['Only Residential', 'Only Commercial']


#==============================================================================
# Analysis end year
#============================================================================== 
analysis_end_year = np.arange(2014, 2051, 2)


#==============================================================================
# Load Growth
#==============================================================================
load_growth_path = os.path.join(model_path[:-7], 'input_data', 'load_growth')
load_growth = list(map(lambda s: s[:-4] if s[-3:] == 'csv' else None, os.listdir(load_growth_path)))
try:
    load_growth.remove(None)
except:
    pass

#==============================================================================
# Retail electricity price escalation scenario
#============================================================================== 
re_price_esc_path = os.path.join(model_path[:-7], 'input_data', 'elec_prices')
re_price_esc = list(map(lambda s: s[:-4] if s[-3:] == 'csv' else None, os.listdir(re_price_esc_path)))
try:
    re_price_esc.remove(None)
except:
    pass


#==============================================================================
# Wholesale electricity price escalation scenario
#============================================================================== 
wh_price_esc_path = os.path.join(model_path[:-7], 'input_data', 'wholesale_electricity_prices')
wh_price_esc = list(map(lambda s: s[:-4] if s[-3:] == 'csv' else None, os.listdir(wh_price_esc_path)))
try:
    wh_price_esc.remove(None)
except:
    pass


#==============================================================================
# PV price scenario
#============================================================================== 
pv_price_scenarios_path = os.path.join(model_path[:-7], 'input_data', 'pv_prices')
pv_price_scenarios = list(map(lambda s: s[:-4] if s[-3:] == 'csv' else None, os.listdir(pv_price_scenarios_path)))
try:
    pv_price_scenarios.remove(None)
except:
    pass


#==============================================================================
# PV technical performance
#============================================================================== 
pv_technical_performance_path = os.path.join(model_path[:-7], 'input_data', 'pv_tech_performance')
pv_technical_performance = list(map(lambda s: s[:-4] if s[-3:] == 'csv' else None, os.listdir(pv_technical_performance_path)))
try:
    pv_technical_performance.remove(None)
except:
    pass


#==============================================================================
# Storage cost scenario
#============================================================================== 
storage_cost_scenarios_path = os.path.join(model_path[:-7], 'input_data', 'batt_prices')
storage_cost_scenarios = list(map(lambda s: s[:-4] if s[-3:] == 'csv' else None, os.listdir(storage_cost_scenarios_path)))
try:
    storage_cost_scenarios.remove(None)
except:
    pass


#==============================================================================
# Storage technical performance scenario
#============================================================================== 
storage_tech_performance_scenarios_path = os.path.join(model_path[:-7], 'input_data', 'batt_tech_performance')
storage_tech_performance_scenarios = list(map(lambda s: s[:-4] if s[-3:] == 'csv' else None, os.listdir(storage_tech_performance_scenarios_path)))
try:
    storage_tech_performance_scenarios.remove(None)
except:
    pass


#==============================================================================
# PV + Storage cost scenario
#============================================================================== 
pv_storage_cost_scenarios_path = os.path.join(model_path[:-7], 'input_data', 'pv_plus_batt_prices')
pv_storage_cost_scenarios = list(map(lambda s: s[:-4] if s[-3:] == 'csv' else None, os.listdir(pv_storage_cost_scenarios_path)))
try:
    pv_storage_cost_scenarios.remove(None)
except:
    pass


#==============================================================================
# Financing scenario
#============================================================================== 
financing_scenarios_path = os.path.join(model_path[:-7], 'input_data', 'financing_terms')
financing_scenarios = list(map(lambda s: s[:-4] if s[-3:] == 'csv' else None, os.listdir(financing_scenarios_path)))
try:
    financing_scenarios.remove(None)
except:
    pass


#==============================================================================
# Depreciation scenarios
#============================================================================== 
depreciation_scenarios_path = os.path.join(model_path[:-7], 'input_data', 'depreciation_schedules')
depreciation_scenarios = list(map(lambda s: s[:-4] if s[-3:] == 'csv' else None, os.listdir(depreciation_scenarios_path)))
try:
    depreciation_scenarios.remove(None)
except:
    pass


#==============================================================================
# Value of resiliency scenario
#============================================================================== 
value_of_res_scenarios_path = os.path.join(model_path[:-7], 'input_data', 'value_of_resiliency')
value_of_res_scenarios = list(map(lambda s: s[:-4] if s[-3:] == 'csv' else None, os.listdir(value_of_res_scenarios_path)))
try:
    value_of_res_scenarios.remove(None)
except:
    pass


#==============================================================================
# Carbon intensity scenario
#============================================================================== 
carbon_intensity_scenarios_path = os.path.join(model_path[:-7], 'input_data', 'carbon_intensities')
carbon_intensity_scenarios = list(map(lambda s: s[:-4] if s[-3:] == 'csv' else None, os.listdir(carbon_intensity_scenarios_path)))
try:
    carbon_intensity_scenarios.remove(None)
except:
    pass


#==============================================================================
# Random Seed Generator
#==============================================================================

random_seed_generator = 1

#==============================================================================
# Titles 
#==============================================================================

titles = ['Scenario Options', 'Value']

#==============================================================================
# Scenario Names
#==============================================================================

scenario_names = ['Scenario Name', 
                  'Technology', 
                  'Markets',
                  'Region to Analyze',
                  'Agent File',
                  'Analysis End Year',
                  'Load Growth Scenario', 
                  'Retail Electricity Price Escalation Scenario', 
                  'Wholesale Electricity Price Scenario',
                  'PV Price Scenario', 
                  'PV Technical Performance Scenario',
                  'Storage Cost Scenario', 
                  'Storage Technical Performance Scenario',
                  'PV + Storage Cost Scenario',
                  'Financing Scenario', 
                  'Depreciation Scenario', 
                  'Value of Resiliency Scenario',
                  'Carbon Intensity Scenario',
                  'Random Generator Seed']

#==============================================================================
# Scenario options
#==============================================================================

scenario_options = ['scenario_name',
                    'technology',
                    'markets',
                    'region_to_analyze',
                    'agent_file',
                    'analysis_end_year',
                    'load_growth_scenario',
                    'retail_electricity_price_escalation_scenario',
                    'wholesale_electricity_price_scenario',
                    'pv_price_scenario',
                    'pv_technical_performance_scenario',
                    'storage_cost_scenario',
                    'storage_technical_performance_scenario',
                    'pv_storage_cost_scenario',
                    'financing_scenario',
                    'depreciation_scenario',
                    'value_of_resiliency_scenario',
                    'carbon_intensity_scenario',
                    'random_generator_seed'
                    ]

#==============================================================================
# Database tables
#==============================================================================

db_tables = {
    'input_main':'input_main_scenario_options',
    'agent_file':'input_agent_file_user_defined',
    'storage_cost_scenario':'input_batt_prices_user_defined',
    'storage_technical_performance_scenario':'input_batt_tech_performance_user_defined',
    'carbon_intensity_scenario':'input_carbon_intensities_user_defined',
    'depreciation_scenario':'input_depreciation_schedules_user_defined',
    'retail_electricity_price_escalation_scenario':'input_elec_prices_user_defined',
    'financing_scenario':'input_financing_terms_user_defined',
    'load_growth_scenario':'input_load_growth_user_defined',
    'pv_storage_cost_scenario':'input_pv_plus_batt_prices_user_defined',
    'pv_price_scenario':'input_pv_prices_user_defined',
    'pv_technical_performance_scenario':'input_pv_tech_performance_user_defined',
    'value_of_resiliency_scenario':'input_value_of_resiliency_user_defined',
    'wholesale_electricity_price_scenario':'input_wholesale_electricity_prices_user_defined'
    }

#==============================================================================
# Hash map of default scenario inputs
#==============================================================================
# Define default scenario
default = {
    'scenario_name':'reference', 
    'technology':'Solar + Storage',
    'markets':'Only Residential',
    'region_to_analyze':'Delaware',
    'agent_file':'agent_df_base_res_de_revised', 
    'analysis_end_year':'2016',
    'load_growth_scenario':'Experimental_load_growth', 
    'retail_electricity_price_escalation_scenario':'ATB19_Low_RE_Cost_retail',
    'wholesale_electricity_price_scenario':'ATB19_Mid_Case_wholesale',
    'pv_price_scenario':'pv_price_atb19_mid',
    'pv_technical_performance_scenario':'pv_tech_performance_defaultFY19',
    'storage_cost_scenario':'batt_prices_FY20_mid',
    'storage_technical_performance_scenario':'batt_tech_performance_SunLamp17',
    'pv_storage_cost_scenario':'pv_plus_batt_prices_FY20_mid',
    'financing_scenario':'financing_atb_FY19',
    'depreciation_scenario':'deprec_sch_FY19',
    'value_of_resiliency_scenario':'vor_FY20_mid',
    'carbon_intensity_scenario':'carbon_intensities_FY19',
    'random_generator_seed':'1'
    }

#==============================================================================
# hash table linking scenario options to their respective choices
#==============================================================================
hash_table = {
    'technology':techs,
    'markets':markets,
    'region_to_analyze':list(regions.keys()),
    'analysis_end_year':[str(i) for i in analysis_end_year],
    'load_growth_scenario':load_growth,
    'retail_electricity_price_escalation_scenario':re_price_esc,
    'wholesale_electricity_price_scenario':wh_price_esc,
    'pv_price_scenario':pv_price_scenarios,
    'pv_technical_performance_scenario':pv_technical_performance,
    'storage_cost_scenario':storage_cost_scenarios,
    'storage_technical_performance_scenario':storage_tech_performance_scenarios,
    'pv_storage_cost_scenario':pv_storage_cost_scenarios,
    'financing_scenario':financing_scenarios,
    'depreciation_scenario':depreciation_scenarios,
    'value_of_resiliency_scenario':value_of_res_scenarios,
    'carbon_intensity_scenario':carbon_intensity_scenarios
    }


#==============================================================================
# Scenario options descriptions
#==============================================================================

descriptions = {
    'scenario_name':'Unique name that identifies the scenario from others. It is the user decision. The default value is reference.',
        
    'technology':'Energy generation/conversion technology options to include in the scenario.',
        
    'markets':'The type of target markets to consider in the scenario. Options include commercial and residential markets.',
        
    'region_to_analyze':'The administrative division name to consider in the scenario. Currently, the supported administrative divisions are the indepemdent states of the United States, the US inland power bloc regions and the United States as a country.',
        
    'agent_file':'A user defined name which matches that of a representative agent file. This is decided in the background based on choices for region to analyze and the type of market to analyze.',
        
    'analysis_end_year':'An even year between 2014 and 2050 for which to terminate running the scenario analysis.',
        
    'load_growth_scenario':'Projections of future energy demand from the Annual Enegy Outlook.',
    
    'retail_electricity_price_escalation_scenario':"TBD",
    
    'wholesale_electricity_price_scenario':"TBD",
    
    'pv_price_scenario':"TBD",
    
    'pv_technical_performance_scenario':"TBD",
    
    'storage_cost_scenario':"TBD",
    
    'storage_technical_performance_scenario':"TBD",
    
    'pv_storage_cost_scenario':"TBD",
    
    'financing_scenario':"TBD",
    
    'depreciation_scenario':"TBD",
    
    'value_of_resiliency_scenario':"TBD",
    
    'carbon_intensity_scenario':"TBD",
    
    'random_generator_seed':"TBD",
        
    }