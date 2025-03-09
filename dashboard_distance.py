#!/usr/bin/env python3
"""
Puerto Rico Property Dashboard - Distance Analysis Tab
-----------------------------------------------------
This module contains the UI components for the Price vs. Distance tab.
"""

from dash import html, dcc, dash_table
import plotly.express as px
import traceback

# Import dashboard styles
from dashboard_styles import styles

# Import data processing functions
from dashboard_data import (
    prepare_distance_data,
    calculate_distance_bin_stats,
    calculate_distance_stats
)

def generate_distance_tab(df):
    """
    Generate content for the distance analysis tab
    
    Args:
        df: Pandas DataFrame containing property data
        
    Returns:
        Dash HTML component containing the distance analysis tab content
    """
    try:
        # Initial content container
        content = html.Div([
            html.H2("Price vs. Distance Analysis")
        ])
        
        # Check if we have distance data
        if 'DISTANCE_MILES' not in df.columns or 'SALESAMT' not in df.columns:
            content.children.append(html.Div(
                html.P("Distance data (DISTANCE_MILES) or price data (SALESAMT) is missing for distance analysis."),
                style=styles['error-message']
            ))
            return content
        
        # Count records with valid distance measurements
        valid_distance_count = df.dropna(subset=['DISTANCE_MILES']).shape[0]
        if valid_distance_count == 0:
            content.children.append(html.Div(
                html.P("No valid distance data found. All distance measurements are missing or invalid."),
                style=styles['error-message']
            ))
            return content
        
        # Add info about available data
        content.children.append(html.Div(
            html.P(f"Found {valid_distance_count} properties with valid distance measurements."),
            style=styles['info-message']
        ))
        
        # Prepare distance data
        dist_df = prepare_distance_data(df)
        if dist_df is None or len(dist_df) == 0:
            content.children.append(html.Div(
                html.P("After filtering for valid sales, no valid distance data remained for analysis."),
                style=styles['error-message']
            ))
            return content
        
        # Create a scatter plot of distance vs price
        scatter_div = html.Div()
        try:
            scatter_fig = px.scatter(
                dist_df,
                x='DISTANCE_MILES',
                y='SALESAMT',
                title='Property Prices vs Distance',
                labels={
                    'DISTANCE_MILES': 'Distance (miles)',
                    'SALESAMT': 'Sale Price ($)'
                },
                opacity=0.7,
                trendline='ols' if len(dist_df) >= 10 else None
            )
            
            scatter_fig.update_layout(
                xaxis_title='Distance (miles)',
                yaxis_title='Sale Price ($)',
                yaxis_tickformat='$,.0f'
            )
            
            scatter_div = html.Div([
                dcc.Graph(figure=scatter_fig)
            ], style=styles['chart-container'])
            
        except Exception as e:
            print(f"Error creating scatter plot: {e}")
            scatter_div = html.Div(
                html.P(f"Error creating scatter plot: {str(e)}"),
                style=styles['error-message']
            )
        
        content.children.append(scatter_div)
        
        # Calculate distance bin statistics
        bin_stats = calculate_distance_bin_stats(dist_df)
        bin_stats_div = html.Div()
        
        if bin_stats is not None and len(bin_stats) > 0:
            try:
                # Create bar chart of average prices by distance bin
                bar_fig = px.bar(
                    bin_stats,
                    x='Distance_Range',
                    y='Avg_Price',
                    title='Average Price by Distance',
                    labels={
                        'Distance_Range': 'Distance Range (miles)',
                        'Avg_Price': 'Average Price ($)'
                    },
                    text_auto='.2s'
                )
                
                bar_fig.update_layout(
                    yaxis_tickformat='$,.0f'
                )
                
                # Create table of distance bin statistics
                bin_stats_table = dash_table.DataTable(
                    id='distance-bin-table',
                    columns=[
                        {"name": "Distance Range", "id": "Distance_Range"},
                        {"name": "Property Count", "id": "Property_Count"},
                        {"name": "Avg Price", "id": "Avg_Price", "type": "numeric", "format": {"specifier": "$,.2f"}},
                        {"name": "Median Price", "id": "Median_Price", "type": "numeric", "format": {"specifier": "$,.2f"}},
                        {"name": "Avg Distance", "id": "Avg_Distance", "type": "numeric", "format": {"specifier": ".2f"}}
                    ],
                    data=bin_stats.to_dict('records'),
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
                
                bin_stats_div = html.Div([
                    html.Div([
                        dcc.Graph(figure=bar_fig)
                    ], style=styles['chart-container']),
                    html.Div([
                        html.H3("Price Statistics by Distance"),
                        bin_stats_table
                    ], style=styles['table-container'])
                ])
            except Exception as e:
                print(f"Error creating bin statistics visualization: {e}")
                bin_stats_div = html.Div(
                    html.P(f"Error creating bin statistics visualization: {str(e)}"),
                    style=styles['error-message']
                )
        else:
            bin_stats_div = html.Div(
                html.P("Could not calculate distance bin statistics. Not enough data for meaningful bins."),
                style=styles['info-message']
            )
        
        content.children.append(bin_stats_div)
        
        # Detailed distance statistics
        distance_stats = calculate_distance_stats(dist_df)
        distance_stats_div = html.Div()
        
        if distance_stats is not None and len(distance_stats) > 0:
            try:
                # Create line chart of prices vs exact distance
                line_fig = px.line(
                    distance_stats,
                    x='Rounded_Distance',
                    y=['Avg_Price', 'Median_Price'],
                    title='Price Trends by Distance',
                    labels={
                        'Rounded_Distance': 'Distance (miles)',
                        'value': 'Price ($)',
                        'variable': 'Metric'
                    }
                )
                
                line_fig.update_layout(
                    xaxis_title='Distance (miles)',
                    yaxis_title='Price ($)',
                    yaxis_tickformat='$,.0f',
                    legend_title_text='Metric'
                )
                
                distance_stats_div = html.Div([
                    dcc.Graph(figure=line_fig)
                ], style=styles['chart-container'])
            except Exception as e:
                print(f"Error creating distance stats visualization: {e}")
                distance_stats_div = html.Div(
                    html.P(f"Error creating detailed distance statistics visualization: {str(e)}"),
                    style=styles['error-message']
                )
        else:
            distance_stats_div = html.Div(
                html.P("Could not calculate detailed distance statistics. Not enough valid data points."),
                style=styles['info-message']
            )
        
        content.children.append(distance_stats_div)
        
        return content
    
    except Exception as e:
        print(f"Error in generate_distance_tab: {e}")
        traceback.print_exc()
        return html.Div([
            html.H4("Error generating distance analysis tab:"),
            html.Pre(str(e)),
            html.Hr(),
            html.Pre(traceback.format_exc())
        ])