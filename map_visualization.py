#!/usr/bin/env python3
"""
Puerto Rico Property Dashboard - Interactive Map Visualization Module
--------------------------------------------------------------------
This module provides UI components for the interactive map visualization tab
with support for 3D, 2D, and heatmap visualizations.
"""

from dash import html, dcc, Input, Output, State, callback, ALL, MATCH
import plotly.express as px
import plotly.graph_objects as go
import traceback
import pandas as pd
import numpy as np

# Import dashboard styles
from dashboard_styles import styles

# Import map data processor
from map_data_processor import prepare_map_data, create_hover_template, calculate_map_statistics

def generate_kepler_map_tab(df):
    """
    Generate content for the interactive map visualization tab
    
    Args:
        df: Pandas DataFrame containing property data
        
    Returns:
        Dash HTML component containing the map visualization
    """
    try:
        # Initial content container
        content = html.Div([
            html.H2("Interactive Property Map Visualization")
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
        
        # Add map statistics
        map_stats = create_map_stats(map_data)
        content.children.append(map_stats)
        
        # Add visualization controls
        viz_controls = create_viz_controls()
        content.children.append(viz_controls)
        
        # Create a default map visualization
        fig = create_map_visualization(
            map_data,
            height_attr='SALESAMT',
            color_attr='SALESAMT',
            view_mode='3d',
            point_size=5,
            opacity=0.7,
            heatmap_intensity=5
        )
        
        # Create a container for the visualization
        map_component = html.Div([
            html.H3("Property Map"),
            html.Div([
                dcc.Graph(
                    id={'type': 'property-map', 'index': 0},
                    figure=fig,
                    config={
                        'scrollZoom': True,
                        'displayModeBar': True,
                        'modeBarButtonsToAdd': ['resetCameraDefault3d'],
                        'responsive': True
                    },
                    style={'height': '700px', 'width': '100%'}
                )
            ], style={'height': '700px', 'width': '100%'})
        ], style={**styles['chart-container'], 'height': 'auto', 'minHeight': '750px'})
        content.children.append(map_component)
        
        # Add navigation instructions
        navigation_div = create_navigation_instructions()
        content.children.append(navigation_div)
        
        return content
    
    except Exception as e:
        print(f"Error in generate_kepler_map_tab: {e}")
        traceback.print_exc()
        return html.Div([
            html.H4("Error generating map tab:"),
            html.Pre(str(e)),
            html.Hr(),
            html.Pre(traceback.format_exc())
        ])

def create_viz_controls():
    """Create visualization control panel"""
    return html.Div([
        html.H3("Visualization Controls"),
        
        html.Div([
            html.Div([
                html.Label("View Mode:"),
                dcc.RadioItems(
                    id={'type': 'view-mode', 'index': 0},
                    options=[
                        {'label': '3D View', 'value': '3d'},
                        {'label': '2D Map', 'value': '2d'},
                        {'label': 'Heatmap', 'value': 'heatmap'}
                    ],
                    value='3d',
                    labelStyle={'marginRight': '15px'},
                    style={'marginBottom': '10px'}
                )
            ], style={'marginBottom': '15px'}),
            
            html.Div([
                html.Label("Color By:"),
                dcc.Dropdown(
                    id={'type': 'color-attribute', 'index': 0},
                    options=[
                        {'label': 'Sale Price', 'value': 'SALESAMT'},
                        {'label': 'Price per Sq Ft', 'value': 'price_per_sqft'},
                        {'label': 'Municipality', 'value': 'MUNICIPIO'}
                    ],
                    value='SALESAMT',
                    clearable=False
                )
            ], style={'marginBottom': '15px', 'width': '100%'}),
            
            html.Div([
                html.Label("Height (Z-axis):"),
                dcc.Dropdown(
                    id={'type': 'height-attribute', 'index': 0},
                    options=[
                        {'label': 'Sale Price', 'value': 'SALESAMT'},
                        {'label': 'Price per Sq Ft', 'value': 'price_per_sqft'}
                    ],
                    value='SALESAMT',
                    clearable=False
                )
            ], style={'marginBottom': '15px', 'width': '100%'})
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        
        html.Div([
            html.Div([
                html.Label("Point Size:"),
                dcc.Slider(
                    id={'type': 'point-size', 'index': 0},
                    min=2,
                    max=10,
                    step=1,
                    value=5,
                    marks={i: str(i) for i in range(2, 11, 2)},
                )
            ], style={'marginBottom': '15px'}),
            
            html.Div([
                html.Label("Point Opacity:"),
                dcc.Slider(
                    id={'type': 'point-opacity', 'index': 0},
                    min=0.1,
                    max=1.0,
                    step=0.1,
                    value=0.7,
                    marks={i/10: str(i/10) for i in range(1, 11, 2)},
                )
            ], style={'marginBottom': '15px'}),
            
            html.Div([
                html.Label("Heatmap Intensity:"),
                dcc.Slider(
                    id={'type': 'heatmap-intensity', 'index': 0},
                    min=1,
                    max=10,
                    step=1,
                    value=5,
                    marks={i: str(i) for i in range(1, 11, 2)},
                )
            ], style={'marginBottom': '15px'})
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'})
    ], style={'marginBottom': '20px', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px'})

def create_navigation_instructions():
    """Create navigation instructions panel"""
    return html.Div([
        html.H3("Navigation Instructions"),
        html.Div([
            html.Div([
                html.H4("Basic Controls:"),
                html.Ul([
                    html.Li("Rotate View (3D): Click and drag"),
                    html.Li("Pan: Right-click and drag"),
                    html.Li("Zoom: Scroll wheel"),
                    html.Li("Reset View: Double-click or use 'Reset Camera' button")
                ])
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            
            html.Div([
                html.H4("Tips:"),
                html.Ul([
                    html.Li("Toggle between view modes to see different perspectives"),
                    html.Li("Adjust point size and opacity for clearer visualization"),
                    html.Li("In heatmap mode, adjust intensity to highlight density patterns"),
                    html.Li("Click on points to see detailed property information")
                ])
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ])
    ], style={'marginTop': '20px', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px'})

def create_map_stats(map_df):
    """Create statistics cards for the map data"""
    # Get statistics
    stats = calculate_map_statistics(map_df)
    
    # Create the stats cards
    return html.Div([
        html.Div([
            html.H3("Map Data Overview"),
            html.P(f"Total properties: {stats.get('total_properties', 0)}"),
            html.P(f"Valid sales: {stats.get('sales_count', 'N/A')}"),
            html.P(f"Price range: ${stats.get('min_price', 0):,.2f} to ${stats.get('max_price', 0):,.2f}")
        ], style=styles['summary-card']),
        
        html.Div([
            html.H3("Location Information"),
            html.P(f"Top municipality: {stats.get('top_municipality', 'Unknown')} "
                   f"({stats.get('top_municipality_count', 0)} properties)"),
            html.P(f"Total municipalities: {stats.get('municipalities_count', 'N/A')}")
        ], style=styles['summary-card']),
        
        html.Div([
            html.H3("Price Information"),
            html.P(f"Average price: ${stats.get('avg_price', 0):,.2f}"),
            html.P(f"Average price/sqft: ${stats.get('avg_price_sqft', 0):,.2f}"),
            html.P(f"Properties with price/sqft: {stats.get('price_sqft_count', 0)}")
        ], style=styles['summary-card'])
    ], style=styles['card-container'])

def create_map_visualization(map_data, height_attr='SALESAMT', color_attr='SALESAMT', 
                            view_mode='3d', point_size=5, opacity=0.7, heatmap_intensity=5):
    """
    Create visualization of property data
    
    Args:
        map_data: DataFrame with prepared map data
        height_attr: Column to use for height in 3D visualization
        color_attr: Column to use for coloring points
        view_mode: Visualization mode ('3d', '2d', or 'heatmap')
        point_size: Size of points in scatter plots
        opacity: Opacity of points (0.1 to 1.0)
        heatmap_intensity: Intensity value for heatmap view (1-10)
        
    Returns:
        Plotly figure object with visualization
    """
    try:
        # Safety check for empty data
        if map_data is None or len(map_data) == 0:
            return create_error_figure("No valid data for visualization")
        
        # Create hover template and customdata
        hovertemplate, customdata = create_hover_template(map_data)
        
        # Handle different visualization modes
        if view_mode == 'heatmap':
            # Create density heatmap with intensity control
            try:
                # Dynamic bin calculation based on intensity
                base_bins = 50
                max_bins = 150
                intensity_factor = heatmap_intensity / 10  # Scale 1-10 to 0.1-1.0
                num_bins = int(base_bins + (max_bins - base_bins) * intensity_factor)
                
                # Create density heatmap
                fig = px.density_heatmap(
                    map_data,
                    x='INSIDE_X',
                    y='INSIDE_Y',
                    title='Property Density Heatmap',
                    labels={
                        'INSIDE_X': 'Longitude',
                        'INSIDE_Y': 'Latitude'
                    },
                    nbinsx=num_bins,
                    nbinsy=num_bins,
                    color_continuous_scale='Viridis',
                    # Higher intensity = more contrast
                    z_range=[0, 20 - heatmap_intensity]
                )
                
                # Add property points as scatter on top for reference
                fig.add_trace(
                    go.Scatter(
                        x=map_data['INSIDE_X'],
                        y=map_data['INSIDE_Y'],
                        mode='markers',
                        marker=dict(
                            size=point_size/2,
                            color='white',
                            opacity=opacity/2
                        ),
                        hoverinfo='skip',
                        showlegend=False
                    )
                )
                
                fig.update_layout(
                    margin=dict(l=0, r=0, b=0, t=30),
                    height=700
                )
                
                return fig
            except Exception as e:
                print(f"Error creating heatmap, falling back to contour: {e}")
                # Fallback to contour plot if heatmap fails
                fig = px.density_contour(
                    map_data,
                    x='INSIDE_X',
                    y='INSIDE_Y',
                    title='Property Density Contour',
                    labels={
                        'INSIDE_X': 'Longitude',
                        'INSIDE_Y': 'Latitude'
                    }
                )
                fig.update_traces(contours_coloring="fill", contours_showlabels=True)
                return fig
            
        elif view_mode == '2d':
            # Create 2D scatter plot
            if color_attr == 'MUNICIPIO':
                # Use categorical coloring
                fig = px.scatter(
                    map_data,
                    x='INSIDE_X',
                    y='INSIDE_Y',
                    color=color_attr,
                    title='Property Map',
                    labels={
                        'INSIDE_X': 'Longitude',
                        'INSIDE_Y': 'Latitude'
                    },
                    height=700
                )
                
                # Update marker size and opacity (done separately to ensure proper functioning)
                fig.update_traces(
                    marker=dict(size=point_size, opacity=opacity),
                    hovertemplate=hovertemplate,
                    customdata=customdata
                )
                
            else:
                # Use continuous color scale for numeric values
                fig = px.scatter(
                    map_data,
                    x='INSIDE_X',
                    y='INSIDE_Y',
                    color=color_attr,
                    color_continuous_scale='Viridis',
                    title='Property Map',
                    labels={
                        'INSIDE_X': 'Longitude',
                        'INSIDE_Y': 'Latitude'
                    },
                    height=700
                )
                
                # Update marker size and opacity separately
                fig.update_traces(
                    marker=dict(size=point_size, opacity=opacity),
                    hovertemplate=hovertemplate,
                    customdata=customdata
                )
            
            # Make sure layout properly configured
            fig.update_layout(
                margin=dict(l=0, r=0, b=0, t=30),
                height=700
            )
            
            return fig
        
        else:  # 3D View
            # Determine Z values for height
            if height_attr == 'price_per_sqft' and 'price_per_sqft' in map_data.columns:
                # Use price per sqft for height
                z_values = map_data['price_per_sqft'].fillna(0).values
                
                # Scale height for better visualization
                x_range = map_data['INSIDE_X'].max() - map_data['INSIDE_X'].min()
                y_range = map_data['INSIDE_Y'].max() - map_data['INSIDE_Y'].min()
                
                # Use log scale for better visualization of price differences
                max_val = z_values.max() if z_values.max() > 0 else 1
                z_values = np.log1p(z_values) * 0.15 * min(x_range, y_range) / np.log1p(max_val)
                
                z_title = 'Price per Sq Ft'
            elif height_attr == 'SALESAMT' and 'SALESAMT' in map_data.columns:
                # Special handling for sales amount to show price levels effectively
                z_values = map_data['SALESAMT'].fillna(0).values
                
                # Scale height for better visualization 
                x_range = map_data['INSIDE_X'].max() - map_data['INSIDE_X'].min()
                y_range = map_data['INSIDE_Y'].max() - map_data['INSIDE_Y'].min()
                
                # Use log scale for better visualization
                max_val = z_values.max() if z_values.max() > 0 else 1
                z_values = np.log1p(z_values) * 0.15 * min(x_range, y_range) / np.log1p(max_val)
                
                z_title = 'Sale Price'
            elif height_attr in map_data.columns and pd.api.types.is_numeric_dtype(map_data[height_attr]):
                # Handle other numeric columns
                z_values = map_data[height_attr].fillna(0).values
                # Scale to a reasonable height
                x_range = map_data['INSIDE_X'].max() - map_data['INSIDE_X'].min()
                y_range = map_data['INSIDE_Y'].max() - map_data['INSIDE_Y'].min()
                scale_factor = 0.15 * min(x_range, y_range) / (z_values.max() if z_values.max() > 0 else 1)
                z_values = z_values * scale_factor
                z_title = f'{height_attr}'
            else:
                # Default to small constant if no height attribute is valid
                z_values = np.ones(len(map_data)) * 0.001
                z_title = ''
            
            # Create 3D scatter with more efficient WebGL settings
            if color_attr == 'MUNICIPIO':
                # Use categorical coloring
                colors = map_data[color_attr].astype('category').cat.codes
                colorscale = px.colors.qualitative.Plotly
                color_discrete_map = {
                    cat: colorscale[i % len(colorscale)] 
                    for i, cat in enumerate(map_data[color_attr].unique())
                }
                
                # Create 3D scatter using Scatter3d
                fig = go.Figure()
                
                # Add a trace for each category for proper legend
                for cat in map_data[color_attr].unique():
                    cat_data = map_data[map_data[color_attr] == cat]
                    if len(cat_data) > 0:
                        # Get indices where this category appears
                        cat_indices = map_data[color_attr] == cat
                        cat_z = z_values[cat_indices]
                        cat_custom = customdata[cat_indices]
                        
                        fig.add_trace(go.Scatter3d(
                            x=cat_data['INSIDE_X'],
                            y=cat_data['INSIDE_Y'],
                            z=cat_z,
                            mode='markers',
                            marker=dict(
                                size=point_size,
                                color=color_discrete_map[cat],
                                opacity=opacity,
                                line=dict(width=0)
                            ),
                            name=str(cat),
                            hovertemplate=hovertemplate,
                            customdata=cat_custom
                        ))
            else:
                # Use continuous coloring for numeric values
                color_values = map_data[color_attr] if color_attr in map_data.columns else z_values
                color_title = color_attr if color_attr in map_data.columns else height_attr
                
                fig = go.Figure(data=[go.Scatter3d(
                    x=map_data['INSIDE_X'],
                    y=map_data['INSIDE_Y'],
                    z=z_values,
                    mode='markers',
                    marker=dict(
                        size=point_size,
                        color=color_values,
                        colorscale='Viridis',
                        opacity=opacity,
                        line=dict(width=0),
                        colorbar=dict(title=color_title)
                    ),
                    hovertemplate=hovertemplate,
                    customdata=customdata
                )])
            
            # Set better layout for 3D visualization
            fig.update_layout(
                title='3D Property Visualization',
                titlefont=dict(size=16),
                showlegend=False if color_attr not in ['MUNICIPIO'] else True,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                scene=dict(
                    aspectmode='data',
                    xaxis=dict(title='Longitude'),
                    yaxis=dict(title='Latitude'),
                    zaxis=dict(title=z_title, showticklabels=False),
                    camera=dict(
                        eye=dict(x=1.5, y=-1.5, z=0.5),
                        up=dict(x=0, y=0, z=1)
                    )
                ),
                height=700,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                )
            )
            
            return fig
    
    except Exception as e:
        print(f"Error creating visualization: {e}")
        traceback.print_exc()
        return create_error_figure(f"Error: {str(e)}")

def create_error_figure(error_message):
    """Create a simple error figure with a message"""
    fig = go.Figure()
    fig.add_annotation(
        text=error_message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=20, color="red")
    )
    
    fig.update_layout(
        title='Error in Visualization',
        height=700
    )
    
    return fig

def register_callbacks(app):
    """
    Register callbacks for the map tab
    This function should be called after the app is created
    """
    @app.callback(
        Output({'type': 'property-map', 'index': MATCH}, 'figure'),
        [Input({'type': 'height-attribute', 'index': MATCH}, 'value'),
         Input({'type': 'color-attribute', 'index': MATCH}, 'value'),
         Input({'type': 'view-mode', 'index': MATCH}, 'value'),
         Input({'type': 'point-size', 'index': MATCH}, 'value'),
         Input({'type': 'point-opacity', 'index': MATCH}, 'value'),
         Input({'type': 'heatmap-intensity', 'index': MATCH}, 'value')],
        [State({'type': 'map-data-store', 'index': MATCH}, 'children')]
    )
    def update_visualization(height_attr, color_attr, view_mode, 
                            point_size, opacity, heatmap_intensity, map_data_json):
        """Update the visualization based on user selections"""
        if not map_data_json:
            return create_error_figure("No data available for visualization")
        
        try:
            # Convert the JSON data back to DataFrame
            map_data = pd.read_json(map_data_json, orient='split')
            
            # Create updated visualization
            return create_map_visualization(
                map_data,
                height_attr=height_attr,
                color_attr=color_attr,
                view_mode=view_mode,
                point_size=point_size,
                opacity=opacity,
                heatmap_intensity=heatmap_intensity
            )
            
        except Exception as e:
            print(f"Error updating visualization: {e}")
            traceback.print_exc()
            return create_error_figure(f"Error updating visualization: {str(e)}")