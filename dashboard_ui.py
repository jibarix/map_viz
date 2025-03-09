#!/usr/bin/env python3
"""
Puerto Rico Property Dashboard - UI Components (Modular Version)
----------------------------------------------
This file contains UI components, styles, and layout for the dashboard.
"""

from dash import dcc, html, Input, Output, State
import traceback

# Import styles
from dashboard_styles import styles

# Import data processing functions
from dashboard_data import parse_contents

# Import tab modules
from dashboard_summary import generate_summary_tab
from dashboard_price_trends import generate_price_trends_tab
from dashboard_property_values import generate_property_values_tab
from dashboard_spatial import generate_spatial_tab
from dashboard_distance import generate_distance_tab
from dashboard_area_analysis import generate_area_analysis_tab
from dashboard_ownership_network import generate_ownership_network_tab
from dashboard_kepler_map import generate_kepler_map_tab

def init_dashboard_ui(app):
    """Initialize the dashboard with layout and callbacks"""
    
    # Define the layout
    app.layout = html.Div([
        html.Div([
            html.H1("Puerto Rico Property Analysis Dashboard", style=styles['title']),
            html.P("Upload a CSV file from the PR Property Search Tool to analyze property data."),
            
            # File upload component
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select a CSV File')
                ]),
                style=styles['upload'],
                multiple=False
            ),
            
            # Display when file is uploaded
            html.Div(id='output-data-upload'),
            
            # Tabs for different analyses
            dcc.Tabs(id='tabs', value='summary', children=[
                dcc.Tab(label='Summary', value='summary'),
                dcc.Tab(label='Interactive Map', value='kepler-map'),
                dcc.Tab(label='Price Trends', value='price-trends'),
                dcc.Tab(label='Property Values', value='property-values'),
                dcc.Tab(label='Area Analysis', value='area-analysis'),
                dcc.Tab(label='Spatial Analysis', value='spatial'),
                dcc.Tab(label='Price vs. Distance', value='distance'),
                dcc.Tab(label='Ownership Network', value='ownership-network'),
            ]),
            
            # Div to hold the tab content
            html.Div(id='tab-content', style=styles['tab-content']),
            
            # Footer
            html.Footer([
                html.P("Puerto Rico Property Analysis Dashboard"),
                html.P("Data sourced from PR Property Search Tool")
            ], style=styles['footer'])
            
        ], style=styles['container'])
    ])
    
    # Register callbacks
    @app.callback(
        [Output('output-data-upload', 'children'),
         Output('tab-content', 'children')],
        [Input('upload-data', 'contents'),
         Input('tabs', 'value')],
        [State('upload-data', 'filename')]
    )
    def update_output(contents, tab_value, filename):
        """Update the dashboard based on uploaded file and selected tab"""
        # Initialize tab_content to an empty div
        tab_content = html.Div()
        
        # Handle file upload
        if contents is None:
            return html.Div("No file uploaded yet."), html.Div(
                html.P("Please upload a CSV file to begin analysis."),
                style=styles['info-message']
            )
        
        try:
            # Parse the file
            df, message = parse_contents(contents, filename)
            
            # Display error if file couldn't be parsed
            if df is None:
                return html.Div(
                    html.P(message, style=styles['error-message'])
                ), html.Div()
            
            # Display successful upload message
            file_info = html.Div([
                html.Div(
                    html.P(message),
                    style=styles['success-message']
                )
            ])
            
            # Generate content based on selected tab
            if tab_value == 'summary':
                tab_content = generate_summary_tab(df)
            elif tab_value == 'price-trends':
                tab_content = generate_price_trends_tab(df)
            elif tab_value == 'property-values':
                tab_content = generate_property_values_tab(df)
            elif tab_value == 'area-analysis':
                tab_content = generate_area_analysis_tab(df)
            elif tab_value == 'spatial':
                tab_content = generate_spatial_tab(df)
            elif tab_value == 'distance':
                tab_content = generate_distance_tab(df)
            elif tab_value == 'ownership-network':
                tab_content = generate_ownership_network_tab(df)
            elif tab_value == 'kepler-map':
                tab_content = generate_kepler_map_tab(df)
        
        except Exception as e:
            print(f"Error in update_output callback: {e}")
            traceback.print_exc()
            
            file_info = html.Div([
                html.Div(
                    html.P("Error processing file"),
                    style=styles['error-message']
                )
            ])
            
            tab_content = html.Div([
                html.H4(f"Error processing data for {tab_value} tab:"),
                html.Pre(str(e)),
                html.Hr(),
                html.Pre(traceback.format_exc())
            ])
        
        return file_info, tab_content