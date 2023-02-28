#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import markdown

from urllib.request import urlopen
from sqlalchemy import create_engine

import pandas as pd
import numpy as np

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def visualization_main(engine, schema, sector, id_):

    # --- Database ---

    # establish connection
    con = engine.connect()

    #############
    ### Plots ###
    #############

    # --- Configuration ---

    # set colors
    color1 = '#F05F3B'
    color2 = '#007872'

    # set labels
    labels = {
        "year": "Year",
        "average_payback": "Average Payback Period",
        "sector_abbr": "Sector",
        "res": "Residential",
        "com": "Commercial",
        "ind": "Industrial",
        "crb_model": "Building Type"
    }

    # set start year
    start_year = 2020

    # --- Title Markdown ---

    title_md = """<div class="jp-Cell-inputWrapper"><div class="jp-InputPrompt jp-InputArea-prompt">
    </div><div class="jp-RenderedHTMLCommon jp-RenderedMarkdown jp-MarkdownOutput " data-mime-type="text/markdown">
    <h1 id="Model-Run-Analysis">Model Run Analysis</h1><ol>
    </ol>
    </div>
    """

    title_html = markdown.markdown(title_md)

    # --- Diffusion Markdown ---

    diff_md = """<div class="jp-Cell-inputWrapper"><div class="jp-InputPrompt jp-InputArea-prompt">
    </div><div class="jp-RenderedHTMLCommon jp-RenderedMarkdown jp-MarkdownOutput " data-mime-type="text/markdown">
    <h2 id='diffusion'>Diffusion</h2><ol>
    </ol>
    <ul>
    <li>This section provides an overivew of total installed capacity and generation, adoption rates and market share, and the value of installed systems.</li>
    <li>Note that some graphs have different y-axis scales for ease of viewing.</li>
    </ul>
    </div>
    """

    diff_html = markdown.markdown(diff_md)

    # --- Data ---

    sql_total = '''
    SELECT year, sector_abbr,
    ROUND(SUM(system_kw_cum_last_year)/1e3) as cum_capacity_last_year,
    ROUND(SUM(system_kw_cum)/1e3) as cum_capacity_mw,
    ROUND(SUM((system_kw_cum - system_kw_cum_last_year)/1e3)) as annual_capacity_mw,
    ROUND(SUM(developable_agent_weight*developable_roof_sqft)) as sum_dev_roof_sqft,
    ROUND(SUM(new_adopters)) as new_adopters,
    ROUND(SUM(number_of_adopters)) as cum_adopters,
    ROUND(SUM(annual_energy_production_kwh)/1e3) as anual_generation_mwh,
    ROUND(SUM(npv)) as sum_npv,
    ROUND(AVG(payback_period)) as avg_payback,
    AVG(system_kw) as avg_system_size,
    ROUND(SUM(system_kw_cum*8760*capacity_factor)/1E3) AS Cum_annual_Gen_MW,
    (SUM(developable_agent_weight*load_kwh_per_customer_in_bin::numeric))/1E9 as load_twh,
    (SUM(system_kw_cum*8760*capacity_factor)/1E9) AS Cum_DPV_Gen_TWh,
    (SUM((system_kw_cum - system_kw_cum_last_year)*8760*capacity_factor)/1E9) as Ann_GEN_TWh,
    ROUND(avg(market_share)*100,3) as avg_market_share,
    ROUND(MAX(max_market_share)*100,3) as max_market_share
    FROM %s.agent_outputs
    WHERE year >= %s
    GROUP BY year, sector_abbr
    ORDER BY year
    ;'''%(schema, start_year)

    total = pd.read_sql(sql_total, con)

    sql_total_by_county = '''
    SELECT year, sector_abbr, county_id,
    ROUND(SUM(system_kw_cum_last_year)/1e3) as cum_capacity_last_year,
    ROUND(SUM(system_kw_cum)/1e3) as cum_capacity_mw,
    ROUND(SUM((system_kw_cum - system_kw_cum_last_year)/1e3)) as annual_capacity_mw,
    ROUND(SUM(developable_agent_weight*developable_roof_sqft)) as sum_dev_roof_sqft,
    ROUND(SUM(new_adopters)) as new_adopters,
    ROUND(SUM(number_of_adopters)) as cum_adopters,
    ROUND(SUM(annual_energy_production_kwh)/1e3) as anual_generation_mwh,
    ROUND(SUM(npv)) as sum_npv,
    ROUND(AVG(payback_period)) as avg_payback,
    AVG(system_kw) as avg_system_size,
    ROUND(SUM(system_kw_cum*8760*capacity_factor)/1E3) AS Cum_annual_Gen_MW,
    (SUM(developable_agent_weight*load_kwh_per_customer_in_bin::numeric))/1E9 as load_twh,
    (SUM(system_kw_cum*8760*capacity_factor)/1E9) AS Cum_DPV_Gen_TWh,
    (SUM((system_kw_cum - system_kw_cum_last_year)*8760*capacity_factor)/1E9) as Ann_GEN_TWh,
    ROUND(avg(market_share)*100,3) as avg_market_share,
    ROUND(MAX(max_market_share)*100,3) as max_market_share
    FROM %s.agent_outputs
    WHERE year >= %s
    GROUP BY year, sector_abbr, county_id
    ORDER BY year
    ;'''%(schema, start_year)

    total_by_county = pd.read_sql(sql_total_by_county, con)

    fips_sql = '''
    SELECT county_id, geoid as fips
    FROM diffusion_shared.cntys_ranked_rates_lkup_20200721;
    '''

    fips_lkup = pd.read_sql(fips_sql, con)

    # drop duplicates and unnecessary columns
    fips_lkup = fips_lkup.drop_duplicates(subset=['county_id'], keep='first')[['county_id', 'fips']]

    # merge FIPS code on county_id
    total_by_county = total_by_county.merge(fips_lkup, how='left', on='county_id')

    # rename column for FIPS code
    total_by_county.rename(columns={'geoid': 'fips'}, inplace=True)

    county_sql = '''
    SELECT county_id, county, state_abbr
    FROM %s.agent_outputs
    ;'''%(schema)

    county_lkup = pd.read_sql(county_sql, con)

    # drop duplicates and unnecessary columns
    county_lkup = county_lkup.drop_duplicates(subset=['county_id'], keep='first')[['county_id', 'county', 'state_abbr']]

    # merge county and state_abbr on county_id
    total_by_county = total_by_county.merge(county_lkup, how='left', on='county_id')

    # get end year
    years = total['year'].to_list()
    end_year = years[-1]

    # --- Installed Capacity ---

    # make subplots
    capacity = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=[sector, sector]
    )

    # adding trace for annual capacity
    capacity.add_trace(go.Bar(
        x=total['year'],
        y=total['annual_capacity_mw'],
        name="Annual",
        marker=dict(color=color1)
    ), row=1, col=1)

    # adding trace for cumulative capacity
    capacity.add_trace(go.Bar(
        x=total['year'],
        y=total['cum_capacity_mw'],
        name="Cumulative",
        marker=dict(color=color2)
    ), row=1, col=2)

    # update layout
    capacity.update_layout(
        title="Installed Capacity By Year",
        title_x = 0.5,
        xaxis_title="Year",
        xaxis2_title="Year",
        yaxis_title="Installed Capacity (MW)",
        xaxis=dict(
            showline=False,
            tickmode='array',
            tickvals=years
        ),
        barmode='stack'
    )

    # --- Net Present Value ---

    # make subplots
    value = make_subplots(
        rows=1,
        cols=1,
        subplot_titles=[sector],
        shared_xaxes=True,
        vertical_spacing=0.02
    )

    # adding trace for annual npv
    value.add_trace(go.Bar(
        x=total['year'],
        y=total['sum_npv'],
        name='Annual',
        marker=dict(color=color1)
    ), row=1, col=1)

    # calculating cumulative npv for commercial
    total['cum_npv'] = total['sum_npv'].cumsum()

    # adding trace for cumulative npv
    value.add_trace(go.Line(
        x=total['year'],
        y=total['cum_npv'],
        name='Cumulative',
        marker=dict(color=color2)
    ), row=1, col=1)

    # update layout
    value.update_layout(
        title="Value of Installed Capacity by Year",
        title_x=0.5,
        xaxis_title="Year",
        yaxis_title="Net Present Value ($)",
        xaxis=dict(
            tickmode='array',
            showgrid=False,
            tickvals=years
        ),
        xaxis2=dict(
            tickmode='array',
            showgrid=False,
            tickvals=years
        ),
        barmode='stack'
    )

    # --- Annual Generation ---

    # make subplots
    generation = make_subplots(
        rows=1,
        cols=1,
        subplot_titles=[sector],
        shared_xaxes=True,
        vertical_spacing=0.02
    )

    # add trace for annual generation
    generation.add_trace(go.Bar(
        x=total['year'],
        y=total['anual_generation_mwh'],
        marker=dict(color=color1)
    ), row=1, col=1)

    # update layout
    generation.update_layout(
        title="Annual Generation by Year",
        title_x=0.5,
        xaxis_title="Year",
        yaxis_title="Annual Generation (MWh)",
        xaxis=dict(
            tickmode='array',
            showgrid=False,
            tickvals=years
        ),
        xaxis2=dict(
            tickmode='array',
            showgrid=False,
            tickvals=years
        ),
        barmode='stack',
        showlegend=False
    )

    # --- Number of Adopters ---

    # make subplots
    adopters = make_subplots(
        rows=1,
        cols=1,
        subplot_titles=[sector]
    )

    # adding trace for annual adopters
    adopters.add_trace(go.Bar(
        x=total['year'],
        y=total['new_adopters'],
        name='Annual',
        marker=dict(color=color1)
    ), row=1, col=1)

    adopters.add_trace(go.Line(
        x=total['year'],
        y=total['cum_adopters'],
        name='Cumulative',
        marker=dict(color=color2)
    ), row=1, col=1)

    # update layout
    adopters.update_layout(
        title="Number of Adopters by Year",
        title_x=0.5,
        xaxis_title="Year",
        yaxis_title="Number of Adopters",
        xaxis=dict(
            tickmode='array',
            showgrid=False,
            tickvals=years
        ),
        barmode='stack'
    )

    # --- Market Share ---

    # make subplots
    market_share = make_subplots(
        rows=1,
        cols=1,
        subplot_titles=[sector],
        shared_yaxes=True,
        shared_xaxes=True,
        horizontal_spacing=0.05
    )

    # adding trace for average market share
    market_share.add_trace(go.Line(
        x=total['year'],
        y=total['avg_market_share'],
        mode='lines+markers',
        name='Market Share',
        marker=dict(color=color1)
    ), row=1, col=1)

    # adding trace for max market share
    market_share.add_trace(go.Scatter(
        x=total['year'],
        y=total['max_market_share'],
        mode='lines',
        line={'dash':'dash'},
        name='Max Market Share',
        marker=dict(color=color1)
    ), row=1, col=1)

    # update layout
    market_share.update_layout(
        title="Market Share by Year",
        title_x=0.5,
        xaxis_title="Year",
        yaxis_title="Market Share (%)",
        xaxis=dict(
            tickmode='array',
            showgrid=False,
            tickvals=years
        ),
        xaxis2=dict(
            tickmode='array',
            showgrid=False,
            tickvals=years
        ),
        barmode='stack'
    )

    # --- Adoption by County ---

    # load shapefile for U.S. counties using FIPS code
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        counties = json.load(response)

    # choropleth
    adoption_map = px.choropleth(
        total_by_county,
        geojson=counties,
        locations='fips',
        color='cum_adopters',
        scope='usa',
        custom_data=['county', 'state_abbr']
    )

    # update geography
    adoption_map.update_geos(
        fitbounds="locations"
    )

    # update traces
    adoption_map.update_traces(
        hovertemplate='<b>%{customdata[0]}, %{customdata[1]}</b><br>%{z:.0f}<extra></extra>'
    )

    # update layout
    adoption_map.update_layout(
        title_text=f"Cumulative {sector} Adopters by County for {end_year}",
        title_x=0.5,
        coloraxis_colorbar=dict(
            title_text='Adopters',
            thickness=15,
            len=.75
        )
    )

    # --- Economics Markdown ---

    econ_md = """<div class="jp-Cell-inputWrapper"><div class="jp-InputPrompt jp-InputArea-prompt">
    </div><div class="jp-RenderedHTMLCommon jp-RenderedMarkdown jp-MarkdownOutput " data-mime-type="text/markdown">
    <h2 id='economics'>Economics</h2><ol>
    </ol>
    <ul>
    <li>This section provides a breakdown of results by payback period, or the number of years it takes for the system to pay for itself.</li>
    <li>Note that payback period is capped at 30 years.</li>
    </ul>
    </div>
    """

    econ_html = markdown.markdown(econ_md)

    # --- Data ---

    sql_payback = '''
    SELECT year, sector_abbr, crb_model, payback_period
    FROM %s.agent_outputs
    WHERE year >= %s
    ;'''%(schema, start_year)

    payback = pd.read_sql(sql_payback, con)

    sql_payback_by_crb = '''
    SELECT year, sector_abbr, crb_model,
    avg(payback_period) as average_payback
    FROM %s.agent_outputs
    WHERE year >= %s
    GROUP BY year, sector_abbr, crb_model
    ORDER BY year ASC
    ;'''%(schema, start_year)

    payback_by_crb = pd.read_sql(sql_payback_by_crb, con)

    # --- Payback Period Distribution ---

    # box plot
    payback_distribution = px.box(
        payback,
        x='year',
        y='payback_period',
        color='sector_abbr',
        facet_col='sector_abbr',
        labels=labels
    )

    # update annotations
    payback_distribution.for_each_annotation(
        lambda a: a.update(
            text=labels[a.text.split("=")[-1]]
        )
    )

    # update traces
    # payback_distribution.for_each_trace(
    #     lambda t: t.update(
    #         name=labels[t.name],
    #         legendgroup=labels[t.name],
    #         hovertemplate=t.hovertemplate.replace(t.name, labels[t.name])
    #     )
    # )

    # update layout
    payback_distribution.update_layout(
        title="Payback Period Distribution by Year",
        title_x=0.5,
        yaxis_title="Payback Period (Years)",
        xaxis=dict(
            tickmode='array',
            showgrid=False,
            tickvals=years
        ),
        xaxis2=dict(
            tickmode='array',
            showgrid=False,
            tickvals=years
        )
    )

    # --- Average Payback Period by Building Type ---

    # line plot
    payback_building = px.line(
        payback_by_crb,
        x='year',
        y='average_payback',
        color='crb_model',
        line_group='crb_model',
        facet_col='sector_abbr',
        labels=labels
    )

    # update annotations
    payback_building.for_each_annotation(
        lambda a: a.update(
            text=labels[a.text.split("=")[-1]]
        )
    )

    # update traces
    # payback_building.for_each_trace(
    #     lambda t: t.update(
    #         name=labels[t.name],
    #         legendgroup=labels[t.name],
    #         hovertemplate=t.hovertemplate.replace(t.name, labels[t.name])
    #     )
    # )

    # update layout
    payback_building.update_layout(
        title="Average Payback Period by Building Type",
        title_x=0.5,
        xaxis_title="Year",
        yaxis_title="Average Payback Period (Years)",
        xaxis=dict(
            showline=False,
            tickmode='array',
            tickvals=years
        )
    )

    # --- Average Payback Period by Cumulative Annual Generation ---

    # make subplots
    payback_generation = make_subplots(
        rows=1,
        cols=1,
        subplot_titles=[sector]
    )

    # adding trace for cumulative annual generation
    payback_generation.add_trace(go.Line(
        x = total['cum_annual_gen_mw'],
        y = total['avg_payback'],
        marker=dict(color=color1),
        showlegend=False
    ), row=1, col=1)

    # update layout
    payback_generation.update_layout(
        title=f"Average Payback Period by Cumulative Annual Generation for {end_year}",
        title_x=0.5,
        yaxis_title="Average Payback Period (Years)",
        xaxis_title="Cumulative Annual Generation (MW)"
    )

    # --- Average Payback Period by County ---

    # choropleth
    payback_map = px.choropleth(
        total_by_county,
        geojson=counties,
        locations='fips',
        color='avg_payback',
        scope='usa',
        custom_data=['county', 'state_abbr']
    )

    # update geography
    payback_map.update_geos(
        fitbounds="locations"
    )

    # update traces
    payback_map.update_traces(
        hovertemplate='<b>%{customdata[0]}, %{customdata[1]}</b><br>%{z:.0f}<extra></extra>'
    )

    # update layout
    payback_map.update_layout(
        title_text=f"Average {sector} Payback Period by County",
        title_x=0.5,
        coloraxis_colorbar=dict(
            title_text='Years',
            thickness=15,
            len=.75
        )
    )

    ############
    ### HTML ###
    ############

    # write all figures and markdown text to single HTML document
    with open('visualize_results_'+str(id_)+'.html', 'w') as f:

        f.write(title_html)

        f.write(diff_html)
        f.write(capacity.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write(value.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write(generation.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write(adopters.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write(market_share.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write(adoption_map.to_html(full_html=False, include_plotlyjs='cdn'))

        f.write(econ_html)
        f.write(payback_distribution.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write(payback_building.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write(payback_generation.to_html(full_html=False, include_plotlyjs='cdn'))
        f.write(payback_map.to_html(full_html=False, include_plotlyjs='cdn'))

    # --- Database ---

    # close connection
    con.close()