#!/usr/bin/env python3
"""
Puerto Rico Property Dashboard - 3D Map Visualization Tab
--------------------------------------------------------
This module contains UI components for an interactive 3D map visualization
similar to Kepler.gl's perspective view using Plotly's 3D capabilities.
"""

from dash import html, dcc, Input, Output, State, callback, ALL, MATCH
import dash
import plotly.express as px
import plotly.graph_objects as go
import traceback
import pandas as pd
import numpy as np

# Import dashboard styles
from dashboard_styles import styles

def generate_kepler_map_tab(df):
    """
    Generate content for the 3D map visualization tab
    
    Args:
        df: Pandas DataFrame containing property data
        
    Returns:
        Dash HTML component containing the 3D map visualization
    """
    try:
        # Initial content container
        content = html.Div([
            html.H2("3D Property Map Visualization")
        ])
        
        # Check if we have coordinate data
        if 'INSIDE_X' not in df.columns or 'INSIDE_Y' not in df.columns:
            content.children.append(html.Div(
                html.P("Coordinate data (INSIDE_X, INSIDE_Y) is missing for map visualization."),
                style=styles['error-message']
            ))
            return content
        
        # Count records with valid coordinates
        valid_coord_count = df.dropna(subset=['INSIDE_X', 'INSIDE_Y']).shape[0]
        if valid_coord_count == 0:
            content.children.append(html.Div(
                html.P("No valid coordinate data found. All coordinates are missing or invalid."),
                style=styles['error-message']
            ))
            return content
        
        # Add info about available data
        content.children.append(html.Div(
            html.P(f"Found {valid_coord_count} properties with valid coordinates."),
            style=styles['info-message']
        ))
        
        # Prepare data for map
        map_data = prepare_map_data(df)
        if map_data is None:
            content.children.append(html.Div(
                html.P("Error preparing map data."),
                style=styles['error-message']
            ))
            return content
        
        # Store map data in a hidden div
        content.children.append(
            html.Div(
                id={'type': 'map-data-store', 'index': 0},
                style={'display': 'none'},
                children=map_data.to_json(date_format='iso', orient='split')
            )
        )
        
        # Add visualization controls
        viz_controls = html.Div([
            html.H3("3D Visualization Controls"),
            html.Div([
                html.Label("Height (Z-axis):"),
                dcc.Dropdown(
                    id={'type': 'height-attribute', 'index': 0},
                    options=[
                        {'label': 'Sale Price', 'value': 'SALESAMT'},
                        {'label': 'Total Value', 'value': 'TOTALVAL'},
                        {'label': 'Land Value', 'value': 'LAND'},
                        {'label': 'Structure Value', 'value': 'STRUCTURE'},
                        {'label': 'Flat (2D)', 'value': 'flat'}
                    ],
                    value='SALESAMT'
                )
            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '3%'}),
            
            html.Div([
                html.Label("Color By:"),
                dcc.Dropdown(
                    id={'type': 'color-attribute', 'index': 0},
                    options=[
                        {'label': 'Sale Price', 'value': 'SALESAMT'},
                        {'label': 'Total Value', 'value': 'TOTALVAL'},
                        {'label': 'Land Value', 'value': 'LAND'},
                        {'label': 'Structure Value', 'value': 'STRUCTURE'},
                        {'label': 'Property Type', 'value': 'TIPO'},
                        {'label': 'Municipality', 'value': 'MUNICIPIO'}
                    ],
                    value='TOTALVAL'
                )
            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '3%'}),
            
            html.Div([
                html.Label("View Mode:"),
                dcc.RadioItems(
                    id={'type': 'view-mode', 'index': 0},
                    options=[
                        {'label': '3D Perspective', 'value': '3d'},
                        {'label': 'Top-Down Map', 'value': '2d'},
                        {'label': 'Density Heatmap', 'value': 'heatmap'}
                    ],
                    value='3d',
                    labelStyle={'display': 'block', 'marginBottom': '5px'}
                )
            ], style={'width': '30%', 'display': 'inline-block'})
        ], style={'marginBottom': '20px', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px'})
        
        # Create a default 3D visualization
        fig3d = create_3d_visualization(map_data)
        
        # Create a container for the visualization
        map_component = html.Div([
            html.H3("Interactive 3D Property Map"),
            html.Div([
                dcc.Graph(
                    id={'type': 'property-3d-map', 'index': 0},
                    figure=fig3d,
                    config={
                        'scrollZoom': True,
                        'displayModeBar': True,
                        'modeBarButtonsToAdd': ['resetCameraDefault3d'],
                        'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                        'willReadFrequently': True  # Fix for Canvas2D warning
                    },
                    style={'height': '700px'}
                )
            ])
        ], style=styles['chart-container'])
        
        # Add map statistics
        map_stats = create_map_stats(map_data)
        
        # Add 3D navigation instructions
        navigation_div = html.Div([
            html.H3("3D Navigation Instructions"),
            html.Div([
                html.Div([
                    html.H4("Basic Controls:"),
                    html.Ul([
                        html.Li("Rotate View: Click and drag with mouse"),
                        html.Li("Pan: Right-click and drag"),
                        html.Li("Zoom: Scroll wheel or pinch gesture"),
                        html.Li("Reset View: Double-click or use the 'Reset Camera' button")
                    ])
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                
                html.Div([
                    html.H4("Advanced Tips:"),
                    html.Ul([
                        html.Li("Hold Shift while dragging for more precise rotation"),
                        html.Li("Click on a point to see its details"),
                        html.Li("Use the view selector to switch between 3D, 2D, and heatmap views"),
                        html.Li("Try different height and color attributes to explore patterns")
                    ])
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'})
            ])
        ], style={'marginTop': '20px', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px'})
        
        # Combine everything
        content.children.extend([
            map_stats,
            viz_controls,
            map_component,
            navigation_div
        ])
        
        return content
    
    except Exception as e:
        print(f"Error in generate_kepler_map_tab: {e}")
        traceback.print_exc()
        return html.Div([
            html.H4("Error generating 3D map tab:"),
            html.Pre(str(e)),
            html.Hr(),
            html.Pre(traceback.format_exc())
        ])

def prepare_map_data(df):
    """
    Prepare data for map visualization
    
    Args:
        df: Input DataFrame with property data
        
    Returns:
        DataFrame with cleaned data ready for map visualization
    """
    try:
        # Create a copy to avoid modifying the original
        map_df = df.copy()
        
        # Filter to records with valid coordinates
        map_df = map_df.dropna(subset=['INSIDE_X', 'INSIDE_Y'])
        
        # Remove any records with 0 coordinates (likely invalid)
        map_df = map_df[(map_df['INSIDE_X'] != 0) & (map_df['INSIDE_Y'] != 0)]
        
        # Keep only essential columns for the map
        keep_cols = ['INSIDE_X', 'INSIDE_Y', 'CATASTRO', 'MUNICIPIO', 'TIPO', 'CABIDA', 
                     'SALESAMT', 'TOTALVAL', 'LAND', 'STRUCTURE', 'SALESDTTM_FORMATTED']
        
        map_df = map_df[[col for col in keep_cols if col in map_df.columns]]
        
        # Calculate additional fields for visualization
        if 'SALESAMT' in map_df.columns:
            # Normalize sales amount for visualization
            max_sales = map_df['SALESAMT'].max()
            if max_sales > 0:
                map_df['salesamt_norm'] = map_df['SALESAMT'] / max_sales
        
        if 'TOTALVAL' in map_df.columns:
            # Normalize total value for visualization
            max_val = map_df['TOTALVAL'].max()
            if max_val > 0:
                map_df['totalval_norm'] = map_df['TOTALVAL'] / max_val
        
        return map_df
    
    except Exception as e:
        print(f"Error preparing map data: {e}")
        return None

def create_3d_visualization(map_data, height_attr='SALESAMT', color_attr='TOTALVAL', view_mode='3d'):
    """
    Create a 3D visualization of property data
    
    Args:
        map_data: DataFrame with prepared map data
        height_attr: Column to use for height in 3D visualization
        color_attr: Column to use for coloring points
        view_mode: Visualization mode ('3d', '2d', or 'heatmap')
        
    Returns:
        Plotly figure object with visualization
    """
    try:
        # Determine Z values (height) for 3D visualization
        if height_attr == 'flat' or view_mode == '2d':
            # Use constant height for 2D view
            z_values = np.zeros(len(map_data))
            z_title = ''
        elif height_attr in map_data.columns and map_data[height_attr].sum() > 0:
            z_values = map_data[height_attr]
            z_title = f'{height_attr} ($)'
        else:
            # If no numeric value, use constant height
            z_values = np.ones(len(map_data))
            z_title = 'Count'
            
        # Get color values
        if color_attr in map_data.columns:
            color_values = map_data[color_attr]
            colorbar_title = f'{color_attr}'
            if color_attr in ['SALESAMT', 'TOTALVAL', 'LAND', 'STRUCTURE']:
                colorbar_title += ' ($)'
        else:
            color_values = z_values
            colorbar_title = z_title
            
        # Create hover text
        hover_texts = []
        for idx, row in map_data.iterrows():
            text_parts = []
            
            if 'CATASTRO' in row and pd.notnull(row['CATASTRO']):
                text_parts.append(f"ID: {row['CATASTRO']}")
                
            if 'TIPO' in row and pd.notnull(row['TIPO']):
                text_parts.append(f"Type: {row['TIPO']}")
                
            if 'MUNICIPIO' in row and pd.notnull(row['MUNICIPIO']):
                text_parts.append(f"Municipality: {row['MUNICIPIO']}")
                
            if 'SALESAMT' in row and pd.notnull(row['SALESAMT']):
                text_parts.append(f"Sale Price: ${row['SALESAMT']:,.2f}")
                
            if 'TOTALVAL' in row and pd.notnull(row['TOTALVAL']):
                text_parts.append(f"Total Value: ${row['TOTALVAL']:,.2f}")
                
            hover_texts.append("<br>".join(text_parts))
        
        # Create the appropriate visualization based on view mode
        if view_mode == 'heatmap':
            # Create a 2D heatmap/density map
            fig = px.density_heatmap(
                map_data,
                x='INSIDE_X',
                y='INSIDE_Y',
                title='Property Density Heatmap',
                labels={
                    'INSIDE_X': 'Longitude',
                    'INSIDE_Y': 'Latitude'
                }
            )
            
            fig.update_layout(
                margin=dict(l=0, r=0, b=0, t=30),
                height=700
            )
            
            return fig
            
        elif view_mode == '2d':
            # Create a 2D scatter plot
            if color_attr in ['TIPO', 'MUNICIPIO']:
                # Use categorical coloring
                fig = px.scatter(
                    map_data,
                    x='INSIDE_X',
                    y='INSIDE_Y',
                    color=color_attr,
                    title='2D Property Map',
                    labels={
                        'INSIDE_X': 'Longitude',
                        'INSIDE_Y': 'Latitude',
                        color_attr: color_attr
                    },
                    hover_data={col: True for col in map_data.columns if col not in ['INSIDE_X', 'INSIDE_Y']}
                )
            else:
                # Use continuous coloring
                fig = px.scatter(
                    map_data,
                    x='INSIDE_X',
                    y='INSIDE_Y',
                    color=color_values,
                    title='2D Property Map',
                    labels={
                        'INSIDE_X': 'Longitude',
                        'INSIDE_Y': 'Latitude',
                        'color': colorbar_title
                    },
                    hover_data={col: True for col in map_data.columns if col not in ['INSIDE_X', 'INSIDE_Y']}
                )
            
            fig.update_layout(
                margin=dict(l=0, r=0, b=0, t=30),
                height=700
            )
            
            return fig
        
        else:
            # Create a 3D scatter plot
            if color_attr in ['TIPO', 'MUNICIPIO']:
                # Use categorical coloring for non-numeric variables
                fig = px.scatter_3d(
                    map_data,
                    x='INSIDE_X',
                    y='INSIDE_Y',
                    z=z_values,
                    color=color_attr,
                    title='3D Property Visualization',
                    labels={
                        'INSIDE_X': 'Longitude',
                        'INSIDE_Y': 'Latitude',
                        'z': z_title,
                        color_attr: color_attr
                    },
                    opacity=0.8
                )
            else:
                # Create the 3D scatter plot with numerical color scale
                fig = go.Figure(data=[go.Scatter3d(
                    x=map_data['INSIDE_X'],
                    y=map_data['INSIDE_Y'],
                    z=z_values,
                    mode='markers',
                    marker=dict(
                        size=5,
                        color=color_values,
                        colorscale='Viridis',
                        opacity=0.8,
                        colorbar=dict(title=colorbar_title),
                        symbol='circle',
                    ),
                    text=hover_texts,
                    hoverinfo='text'
                )])
                
                # Set the title
                fig.update_layout(title='3D Property Visualization')
            
            # Set up the layout for nice 3D visualization
            fig.update_layout(
                scene=dict(
                    aspectmode='data',  # Important for realistic visualization
                    xaxis=dict(title='Longitude'),
                    yaxis=dict(title='Latitude'),
                    zaxis=dict(title=z_title),
                    camera=dict(
                        # Set initial camera position for Kepler.gl-like perspective view
                        eye=dict(x=1.5, y=-1.5, z=1.0),
                        up=dict(x=0, y=0, z=1)
                    )
                ),
                margin=dict(l=0, r=0, b=0, t=30),
                height=700
            )
            
            return fig
    
    except Exception as e:
        print(f"Error creating visualization: {e}")
        # Return a simple fallback figure
        return go.Figure(data=[go.Scatter3d(
            x=[0],
            y=[0],
            z=[0],
            mode='markers',
            marker=dict(size=10, color='red')
        )]).update_layout(
            title='Error in Visualization',
            scene=dict(
                xaxis=dict(title='Longitude'),
                yaxis=dict(title='Latitude'),
                zaxis=dict(title='Error')
            )
        )

def create_map_stats(map_df):
    """Create statistics cards for the map data"""
    total_properties = len(map_df)
    
    # Sale price stats if available
    price_stats = {}
    if 'SALESAMT' in map_df.columns:
        valid_sales = map_df[map_df['SALESAMT'] > 1000]
        price_stats = {
            'sales_count': len(valid_sales),
            'avg_price': valid_sales['SALESAMT'].mean() if len(valid_sales) > 0 else 0,
            'max_price': valid_sales['SALESAMT'].max() if len(valid_sales) > 0 else 0,
            'min_price': valid_sales['SALESAMT'].min() if len(valid_sales) > 0 else 0
        }
    
    # Municipality counts if available
    municipality_stats = {}
    if 'MUNICIPIO' in map_df.columns:
        top_municipalities = map_df['MUNICIPIO'].value_counts().head(3)
        municipality_stats = {
            'top_municipality': top_municipalities.index[0] if len(top_municipalities) > 0 else "Unknown",
            'top_count': top_municipalities.iloc[0] if len(top_municipalities) > 0 else 0,
            'municipalities_count': map_df['MUNICIPIO'].nunique()
        }
    
    # Create the stats cards
    stats_div = html.Div([
        html.Div([
            html.H3("Map Data Overview"),
            html.P(f"Total properties: {total_properties}"),
            html.P(f"Valid sales: {price_stats.get('sales_count', 'N/A')}"),
            html.P(f"Price range: ${price_stats.get('min_price', 0):,.2f} to ${price_stats.get('max_price', 0):,.2f}")
        ], style=styles['summary-card']),
        
        html.Div([
            html.H3("Location Information"),
            html.P(f"Top municipality: {municipality_stats.get('top_municipality', 'Unknown')} "
                   f"({municipality_stats.get('top_count', 0)} properties)"),
            html.P(f"Total municipalities: {municipality_stats.get('municipalities_count', 'N/A')}")
        ], style=styles['summary-card']),
        
        html.Div([
            html.H3("Visualization Features"),
            html.P("3D View: Properties displayed in three dimensions"),
            html.P("Height: Represents sale price or property value"),
            html.P("Color: Indicates property value or type"),
            html.P("Hover: Shows detailed property information")
        ], style=styles['summary-card'])
    ], style=styles['card-container'])
    
    return stats_div

# Callback for updating the 3D visualization based on user selections
def register_callbacks(app):
    """
    Register callbacks for the Kepler map tab
    This function should be called after the app is created
    """
    @app.callback(
        Output({'type': 'property-3d-map', 'index': MATCH}, 'figure'),
        [Input({'type': 'height-attribute', 'index': MATCH}, 'value'),
         Input({'type': 'color-attribute', 'index': MATCH}, 'value'),
         Input({'type': 'view-mode', 'index': MATCH}, 'value')],
        [State({'type': 'map-data-store', 'index': MATCH}, 'children')]
    )
    def update_3d_visualization(height_attr, color_attr, view_mode, map_data_json):
        """Update the visualization based on user selections"""
        if not map_data_json:
            # Return an empty figure if no data
            return go.Figure().update_layout(
                title='No data available for visualization',
                height=700
            )
        
        try:
            # Convert the JSON data back to DataFrame
            map_data = pd.read_json(map_data_json, orient='split')
            
            # Create updated visualization
            return create_3d_visualization(map_data, height_attr, color_attr, view_mode)
            
        except Exception as e:
            print(f"Error updating visualization: {e}")
            traceback.print_exc()
            
            # Return error figure
            return go.Figure(data=[go.Scatter3d(
                x=[0],
                y=[0],
                z=[0],
                mode='markers',
                marker=dict(size=10, color='red')
            )]).update_layout(
                title=f'Error: {str(e)}',
                scene=dict(
                    xaxis=dict(title='Longitude'),
                    yaxis=dict(title='Latitude'),
                    zaxis=dict(title='Error')
                ),
                height=700
            )