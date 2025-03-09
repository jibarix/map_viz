#!/usr/bin/env python3
"""
Puerto Rico Property Dashboard - 3D Map Visualization Tab (Improved Version)
---------------------------------------------------------------------------
This module contains UI components for an interactive 3D map visualization
with improved 3D functionality and density controls.
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
        
        # Add visualization controls - Improved for better 3D functionality
        viz_controls = html.Div([
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
                            {'label': 'Municipality', 'value': 'MUNICIPIO'},
                            {'label': 'Property Type', 'value': 'TIPO'}
                        ],
                        value='SALESAMT',
                        clearable=False
                    )
                ], style={'marginBottom': '15px', 'width': '100%'}),
                
                # Using only properties with consistent Z-axis values
                html.Div([
                    html.Label("Height (Z-axis):"),
                    dcc.Dropdown(
                        id={'type': 'height-attribute', 'index': 0},
                        options=[
                            {'label': 'Sale Price', 'value': 'SALESAMT'},
                            {'label': 'Flat (No Height)', 'value': 'flat'}
                        ],
                        value='flat',
                        clearable=False
                    )
                ], style={'marginBottom': '15px', 'width': '100%'})
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            
            # Added density controls
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
                    html.Label("Heatmap Radius (for heatmap view):"),
                    dcc.Slider(
                        id={'type': 'heatmap-radius', 'index': 0},
                        min=5,
                        max=30,
                        step=5,
                        value=15,
                        marks={i: str(i) for i in range(5, 31, 5)},
                    )
                ], style={'marginBottom': '15px'})
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ], style={'marginBottom': '20px', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px'})
        
        # Create a default map visualization
        fig = create_map_visualization(
            map_data,
            height_attr='flat',
            color_attr='SALESAMT',
            view_mode='3d',
            point_size=5,
            opacity=0.7,
            heatmap_radius=15
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
        
        # Add map statistics
        map_stats = create_map_stats(map_data)
        
        # Add navigation instructions
        navigation_div = html.Div([
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
                        html.Li("For best 3D performance, use 'Flat' for height"),
                        html.Li("Toggle between view modes to see different perspectives"),
                        html.Li("Adjust point size and opacity for clearer visualization"),
                        html.Li("Click on points to see detailed property information")
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
            html.H4("Error generating map tab:"),
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
                     'SALESAMT', 'TOTALVAL', 'SALESDTTM_FORMATTED']
        
        map_df = map_df[[col for col in keep_cols if col in map_df.columns]]
        
        # Add calculated fields for better visualization
        # Normalize sales amount for better visualization
        if 'SALESAMT' in map_df.columns:
            map_df['SALESAMT'] = pd.to_numeric(map_df['SALESAMT'], errors='coerce')
            max_sales = map_df['SALESAMT'].max()
            if max_sales > 0:
                map_df['salesamt_norm'] = map_df['SALESAMT'] / max_sales
                # Fill NaN values with 0
                map_df['salesamt_norm'] = map_df['salesamt_norm'].fillna(0)
        
        # Remove any null values which could cause WebGL rendering issues
        map_df = map_df.fillna({
            'INSIDE_X': map_df['INSIDE_X'].mean(),
            'INSIDE_Y': map_df['INSIDE_Y'].mean(),
            'SALESAMT': 0
        })
        
        # If dataset is too large, sample it to prevent browser performance issues
        if len(map_df) > 2000:
            print(f"Dataset contains {len(map_df)} points, sampling to 2000 for performance")
            map_df = map_df.sample(2000, random_state=42)
            
        return map_df
    
    except Exception as e:
        print(f"Error preparing map data: {e}")
        traceback.print_exc()
        return None

def create_map_visualization(map_data, height_attr='flat', color_attr='SALESAMT', 
                            view_mode='3d', point_size=5, opacity=0.7, heatmap_radius=15):
    """
    Create visualization of property data
    
    Args:
        map_data: DataFrame with prepared map data
        height_attr: Column to use for height in 3D visualization
        color_attr: Column to use for coloring points
        view_mode: Visualization mode ('3d', '2d', or 'heatmap')
        point_size: Size of points in scatter plots
        opacity: Opacity of points (0.1 to 1.0)
        heatmap_radius: Radius for heatmap view
        
    Returns:
        Plotly figure object with visualization
    """
    try:
        # Safety check for empty data
        if map_data is None or len(map_data) == 0:
            return create_error_figure("No valid data for visualization")
            
        # Create hover text information
        hover_data = {}
        for col in map_data.columns:
            if col in ['INSIDE_X', 'INSIDE_Y', 'salesamt_norm']:
                continue
            if col == 'SALESAMT':
                hover_data[col] = ':$,.2f'
            elif col == 'TOTALVAL':
                hover_data[col] = ':$,.2f'
            else:
                hover_data[col] = True
        
        # Handle different visualization modes
        if view_mode == 'heatmap':
            # Create density heatmap
            try:
                fig = px.density_heatmap(
                    map_data,
                    x='INSIDE_X',
                    y='INSIDE_Y',
                    title='Property Density Heatmap',
                    labels={
                        'INSIDE_X': 'Longitude',
                        'INSIDE_Y': 'Latitude'
                    },
                    nbinsx=100,
                    nbinsy=100,
                )
                
                # Add property points as scatter on top of heatmap for reference
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
            # Create 2D scatter plot with more efficient settings
            if color_attr in ['TIPO', 'MUNICIPIO']:
                # Use categorical coloring for non-numeric values
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
                    hover_data=hover_data,
                    opacity=opacity,
                )
                
                # Update marker size 
                fig.update_traces(marker=dict(size=point_size))
                
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
                    hover_data=hover_data,
                    opacity=opacity,
                )
                
                # Update marker size
                fig.update_traces(marker=dict(size=point_size))
            
            fig.update_layout(
                margin=dict(l=0, r=0, b=0, t=30),
                height=700
            )
            
            return fig
        
        else:  # 3D View
            # Determine Z values for height
            if height_attr == 'flat':
                # Use a small constant for flat view but not zero (for better visibility)
                z_values = np.ones(len(map_data)) * 0.01
                z_title = ''
            elif height_attr in map_data.columns and pd.api.types.is_numeric_dtype(map_data[height_attr]):
                # Normalize height values to a reasonable range for better visualization
                z_values = map_data[height_attr].fillna(0).values
                # Scale to a reasonable height (max 20% of the X/Y range)
                x_range = map_data['INSIDE_X'].max() - map_data['INSIDE_X'].min()
                y_range = map_data['INSIDE_Y'].max() - map_data['INSIDE_Y'].min()
                scale_factor = 0.2 * min(x_range, y_range) / (z_values.max() if z_values.max() > 0 else 1)
                z_values = z_values * scale_factor
                z_title = f'{height_attr}'
            else:
                # Default to flat if the specified column isn't suitable
                z_values = np.ones(len(map_data)) * 0.01
                z_title = ''
            
            # Create 3D scatter with more efficient WebGL settings
            if color_attr in ['TIPO', 'MUNICIPIO']:
                # Use categorical coloring
                colors = map_data[color_attr].astype('category').cat.codes
                colorscale = px.colors.qualitative.Plotly
                color_discrete_map = {
                    cat: colorscale[i % len(colorscale)] 
                    for i, cat in enumerate(map_data[color_attr].unique())
                }
                
                # Create more efficient 3D scatter using Scatter3d
                fig = go.Figure()
                
                # Add a trace for each category for proper legend
                for cat in map_data[color_attr].unique():
                    cat_data = map_data[map_data[color_attr] == cat]
                    if len(cat_data) > 0:
                        cat_z = z_values[map_data[color_attr] == cat]
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
                            hovertemplate=create_hover_template(cat_data)
                        ))
            else:
                # Use continuous coloring for numeric values
                fig = go.Figure(data=[go.Scatter3d(
                    x=map_data['INSIDE_X'],
                    y=map_data['INSIDE_Y'],
                    z=z_values,
                    mode='markers',
                    marker=dict(
                        size=point_size,
                        color=map_data[color_attr] if color_attr in map_data.columns else z_values,
                        colorscale='Viridis',
                        opacity=opacity,
                        line=dict(width=0),
                        colorbar=dict(title=color_attr)
                    ),
                    hovertemplate=create_hover_template(map_data)
                )])
            
            # Set better layout for 3D visualization
            fig.update_layout(
                title='3D Property Visualization',
                scene=dict(
                    aspectmode='data',
                    xaxis=dict(title='Longitude'),
                    yaxis=dict(title='Latitude'),
                    zaxis=dict(title=z_title, showticklabels=False),
                    camera=dict(
                        eye=dict(x=1.5, y=-1.5, z=0.5),  # Lower z for better angle
                        up=dict(x=0, y=0, z=1)
                    )
                ),
                margin=dict(l=0, r=0, b=0, t=30),
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

def create_hover_template(df):
    """Create a nice hover template based on available columns"""
    parts = []
    
    # Add property ID if available
    if 'CATASTRO' in df.columns:
        parts.append("ID: %{customdata[0]}")
    
    # Add property type if available
    if 'TIPO' in df.columns:
        parts.append("Type: %{customdata[1]}")
    
    # Add municipality if available
    if 'MUNICIPIO' in df.columns:
        parts.append("Municipality: %{customdata[2]}")
    
    # Add price information if available
    if 'SALESAMT' in df.columns:
        parts.append("Sale Price: $%{customdata[3]:,.2f}")
    
    # Add coordinates
    parts.append("<br>Longitude: %{x:.6f}")
    parts.append("Latitude: %{y:.6f}")
    
    # Add extra info
    parts.append("<extra></extra>")
    
    # Build customdata array for the template
    custom_cols = []
    if 'CATASTRO' in df.columns:
        custom_cols.append(df['CATASTRO'])
    if 'TIPO' in df.columns:
        custom_cols.append(df['TIPO'])
    if 'MUNICIPIO' in df.columns:
        custom_cols.append(df['MUNICIPIO'])
    if 'SALESAMT' in df.columns:
        custom_cols.append(df['SALESAMT'])
    
    # If we have customdata columns, add them to the figure
    if custom_cols:
        customdata = np.column_stack(custom_cols)
    else:
        # Default empty customdata
        customdata = np.zeros((len(df), 1))
    
    return "<br>".join(parts), customdata

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
            html.H3("Visualization Tips"),
            html.P("For best performance in 3D view, use 'Flat' height setting"),
            html.P("Adjust point size and opacity for clearer visualization"),
            html.P("Try different view modes to explore the data in different ways")
        ], style=styles['summary-card'])
    ], style=styles['card-container'])
    
    return stats_div

# Callbacks for updating the visualization based on user selections
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
         Input({'type': 'heatmap-radius', 'index': MATCH}, 'value')],
        [State({'type': 'map-data-store', 'index': MATCH}, 'children')]
    )
    def update_visualization(height_attr, color_attr, view_mode, 
                            point_size, opacity, heatmap_radius, map_data_json):
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
                heatmap_radius=heatmap_radius
            )
            
        except Exception as e:
            print(f"Error updating visualization: {e}")
            traceback.print_exc()
            return create_error_figure(f"Error updating visualization: {str(e)}")