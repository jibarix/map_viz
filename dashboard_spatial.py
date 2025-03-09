#!/usr/bin/env python3
"""
Puerto Rico Property Dashboard - Spatial Analysis Tab
----------------------------------------------------
This module contains the UI components for the Spatial Analysis tab.
"""

from dash import html, dcc, dash_table
import plotly.express as px
import traceback

# Import dashboard styles
from dashboard_styles import styles

# Import data processing functions
from dashboard_data import (
    prepare_spatial_data,
    calculate_spatial_grid_stats
)

def generate_spatial_tab(df):
    """
    Generate content for the spatial analysis tab
    
    Args:
        df: Pandas DataFrame containing property data
        
    Returns:
        Dash HTML component containing the spatial analysis tab content
    """
    try:
        # Initial content container
        content = html.Div([
            html.H2("Spatial Analysis")
        ])
        
        # Check if we have coordinate data
        if 'INSIDE_X' not in df.columns or 'INSIDE_Y' not in df.columns:
            content.children.append(html.Div(
                html.P("Coordinate data (INSIDE_X, INSIDE_Y) is missing for spatial analysis."),
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
        
        # Prepare spatial data
        geo_df = prepare_spatial_data(df)
        if geo_df is None or len(geo_df) == 0:
            content.children.append(html.Div(
                html.P("After additional data cleaning, no valid coordinate data remained for analysis."),
                style=styles['error-message']
            ))
            return content
        
        # Create a scatter map
        scatter_map_div = html.Div()
        try:
            if 'SALESAMT' in geo_df.columns and 'VALID_SALE' in geo_df.columns:
                # Use only valid sales for coloring by price
                map_df = geo_df[geo_df['VALID_SALE']].copy()
                
                if len(map_df) > 0:
                    # Create scatter map colored by price
                    scatter_map = px.scatter(
                        map_df,
                        x='INSIDE_X',
                        y='INSIDE_Y',
                        color='SALESAMT',
                        size='SALESAMT',
                        color_continuous_scale=px.colors.sequential.Blues,
                        range_color=[0, min(1000000, map_df['SALESAMT'].max())],
                        opacity=0.7,
                        title='Property Locations Colored by Sale Price',
                        labels={
                            'INSIDE_X': 'Longitude',
                            'INSIDE_Y': 'Latitude',
                            'SALESAMT': 'Sale Price ($)'
                        },
                        hover_data=['TIPO', 'CABIDA', 'TOTALVAL', 'MUNICIPIO'] if all(col in map_df.columns for col in ['TIPO', 'CABIDA', 'TOTALVAL', 'MUNICIPIO']) else None
                    )
                    
                    scatter_map.update_layout(
                        coloraxis_colorbar=dict(
                            title="Sale Price",
                            tickformat="$,.0f"
                        )
                    )
                else:
                    # If no valid sales but we have coordinates, still show a scatter plot
                    scatter_map = px.scatter(
                        geo_df,
                        x='INSIDE_X',
                        y='INSIDE_Y',
                        title='Property Locations',
                        labels={
                            'INSIDE_X': 'Longitude',
                            'INSIDE_Y': 'Latitude'
                        },
                        hover_data=['TIPO', 'CABIDA', 'TOTALVAL', 'MUNICIPIO'] if all(col in geo_df.columns for col in ['TIPO', 'CABIDA', 'TOTALVAL', 'MUNICIPIO']) else None
                    )
            else:
                # Simple scatter plot for locations only
                scatter_map = px.scatter(
                    geo_df,
                    x='INSIDE_X',
                    y='INSIDE_Y',
                    title='Property Locations',
                    labels={
                        'INSIDE_X': 'Longitude',
                        'INSIDE_Y': 'Latitude'
                    },
                    hover_data=['TIPO', 'CABIDA', 'TOTALVAL', 'MUNICIPIO'] if all(col in geo_df.columns for col in ['TIPO', 'CABIDA', 'TOTALVAL', 'MUNICIPIO']) else None
                )
            
            scatter_map_div = html.Div([
                dcc.Graph(figure=scatter_map)
            ], style=styles['chart-container'])
            
        except Exception as e:
            print(f"Error creating scatter map: {e}")
            scatter_map_div = html.Div(
                html.P(f"Error creating scatter map: {str(e)}"),
                style=styles['error-message']
            )
        
        content.children.append(scatter_map_div)
        
        # Create a heatmap if we have enough data
        heatmap_div = html.Div()
        if len(geo_df) >= 20:
            try:
                heatmap = px.density_mapbox(
                    geo_df,
                    lat='INSIDE_Y', 
                    lon='INSIDE_X',
                    radius=10,
                    center=dict(lat=geo_df['INSIDE_Y'].mean(), lon=geo_df['INSIDE_X'].mean()),
                    zoom=10,
                    mapbox_style="carto-positron",
                    title='Property Density Heatmap'
                )
                
                heatmap_div = html.Div([
                    dcc.Graph(figure=heatmap)
                ], style=styles['chart-container'])
                
            except Exception as e:
                print(f"Error creating heatmap: {e}")
                heatmap_div = html.Div(
                    html.P(f"Error creating density heatmap. Using standard fallback instead."),
                    style=styles['info-message']
                )
                
                # Create fallback heatmap using standard density plot
                try:
                    fallback_heatmap = px.density_contour(
                        geo_df, 
                        x='INSIDE_X', 
                        y='INSIDE_Y',
                        title='Property Density Contour Map'
                    )
                    fallback_heatmap.update_traces(contours_coloring="fill", contours_showlabels=True)
                    
                    heatmap_div = html.Div([
                        dcc.Graph(figure=fallback_heatmap)
                    ], style=styles['chart-container'])
                except:
                    heatmap_div = html.Div(
                        html.P("Could not create heatmap visualization with the available data."),
                        style=styles['error-message']
                    )
        else:
            heatmap_div = html.Div(
                html.P(f"Not enough data points ({len(geo_df)}) to create a meaningful heatmap. At least 20 points needed."),
                style=styles['info-message']
            )
        
        content.children.append(heatmap_div)
        
        # Calculate spatial grid statistics
        grid_stats_div = html.Div()
        grid_stats = calculate_spatial_grid_stats(geo_df)
        
        if grid_stats is not None and len(grid_stats) > 0:
            grid_stats_table = dash_table.DataTable(
                id='grid-stats-table',
                columns=[
                    {"name": "Longitude Range", "id": "Longitude_Range"},
                    {"name": "Latitude Range", "id": "Latitude_Range"},
                    {"name": "Property Count", "id": "Property_Count"},
                    {"name": "Avg Price", "id": "Avg_Price", "type": "numeric", "format": {"specifier": "$,.2f"}},
                    {"name": "Median Price", "id": "Median_Price", "type": "numeric", "format": {"specifier": "$,.2f"}}
                ],
                data=grid_stats.to_dict('records'),
                sort_action="native",
                sort_mode="multi",
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px'
                },
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                }
            )
            
            grid_stats_div = html.Div([
                html.H3("Spatial Grid Statistics"),
                grid_stats_table
            ], style=styles['table-container'])
        else:
            grid_stats_div = html.Div(
                html.P("Could not calculate spatial grid statistics. Not enough valid sales with coordinate data."),
                style=styles['info-message']
            )
        
        content.children.append(grid_stats_div)
        
        return content
    
    except Exception as e:
        print(f"Error in generate_spatial_tab: {e}")
        traceback.print_exc()
        return html.Div([
            html.H4("Error generating spatial analysis tab:"),
            html.Pre(str(e)),
            html.Hr(),
            html.Pre(traceback.format_exc())
        ])