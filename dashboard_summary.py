#!/usr/bin/env python3
"""
Puerto Rico Property Dashboard - Summary Tab
--------------------------------------------
This module contains the UI components for the Summary tab.
"""

from dash import html, dcc, dash_table
import plotly.express as px
import traceback

# Import dashboard styles
from dashboard_styles import styles

# Import data processing functions
from dashboard_data import (
    calculate_summary_stats,
    prepare_price_distribution_data,
    prepare_monthly_price_per_sqft_data
)

def generate_summary_tab(df):
    """
    Generate content for the summary tab
    
    Args:
        df: Pandas DataFrame containing property data
        
    Returns:
        Dash HTML component containing the summary tab content
    """
    try:
        # Calculate summary statistics
        stats = calculate_summary_stats(df)
        
        # Create summary cards
        summary_cards = html.Div([
            html.Div([
                html.Div([
                    html.H3("Property Counts"),
                    html.P(f"Total properties: {stats['total_properties']}"),
                    html.P(f"Properties with sales: {stats['properties_with_sales']}"),
                    html.P(f"Valid sales (non-symbolic): {stats['valid_sales']}")
                ], style=styles['summary-card']),
                
                html.Div([
                    html.H3("Price Statistics"),
                    html.P(f"Average sale price: ${stats['avg_price']:,.2f}"),
                    html.P(f"Median sale price: ${stats['median_price']:,.2f}"),
                    html.P(f"Price range: ${stats['min_price']:,.2f} to ${stats['max_price']:,.2f}")
                ], style=styles['summary-card']),
                
                html.Div([
                    html.H3("Property Info"),
                    html.P(f"Average property value: ${stats['avg_property_value']:,.2f}"),
                    html.P(f"Date range: {stats['date_range']}"),
                    html.P(f"Main municipality: {stats['main_municipality']} ({stats['main_municipality_count']} properties)")
                ], style=styles['summary-card'])
            ], style=styles['card-container'])
        ])
        
        # Add area information if available
        area_cards = html.Div()
        if 'avg_area_sqm' in stats and 'avg_area_sqft' in stats:
            area_cards = html.Div([
                html.Div([
                    html.H3("Area Statistics"),
                    html.P(f"Average property size: {stats['avg_area_sqm']:,.2f} m² ({stats['avg_area_sqft']:,.2f} sq ft)"),
                    html.P(f"Median property size: {stats['median_area_sqm']:,.2f} m² ({stats['median_area_sqft']:,.2f} sq ft)"),
                    html.P(f"Properties with area data: {stats['area_data_count']}")
                ], style=styles['summary-card']),
                
                html.Div([
                    html.H3("Price per Square Foot"),
                    html.P(f"Average price per sq ft: ${stats.get('avg_price_per_sqft', 0):,.2f}"),
                    html.P(f"Median price per sq ft: ${stats.get('median_price_per_sqft', 0):,.2f}"),
                    html.P(f"Properties with price/sqft: {stats.get('properties_with_price_per_sqft', 0)}")
                ], style=styles['summary-card']) if 'avg_price_per_sqft' in stats else html.Div()
            ], style=styles['card-container'])
        
        # Create a price per sqft over time chart
        price_sqft_time_div = html.Div()
        monthly_sqft_data = prepare_monthly_price_per_sqft_data(df)
        if monthly_sqft_data is not None:
            # Create line chart
            price_sqft_fig = px.line(
                monthly_sqft_data,
                x='month_date',
                y=['avg_price_per_sqft', 'median_price_per_sqft'],
                title='Price per Square Foot Over Time',
                labels={
                    'month_date': 'Month',
                    'value': 'Price per Square Foot ($)',
                    'variable': 'Metric'
                },
                color_discrete_map={
                    'avg_price_per_sqft': 'blue',
                    'median_price_per_sqft': 'green'
                }
            )
            
            price_sqft_fig.update_layout(
                xaxis_title='Month',
                yaxis_title='Price per Square Foot ($)',
                yaxis_tickformat='$,.2f',
                legend_title_text='',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Add data point count as annotations
            price_sqft_fig.update_traces(
                hovertemplate='%{y:$,.2f}<br>Month: %{x|%b %Y}<br>Properties: %{text}',
                text=monthly_sqft_data['sqft_property_count']
            )
            
            price_sqft_time_div = html.Div([
                html.H3("Price per Square Foot Trends"),
                dcc.Graph(figure=price_sqft_fig)
            ], style=styles['chart-container'])
        else:
            # Fallback to original price distribution if we don't have enough data for time series
            sales_df = prepare_price_distribution_data(df)
            if sales_df is not None:
                # Create histogram
                price_fig = px.histogram(
                    sales_df,
                    x='SALESAMT',
                    nbins=20,
                    title='Distribution of Property Sale Prices',
                    labels={'SALESAMT': 'Sale Price ($)'},
                    opacity=0.8
                )
                
                price_fig.update_layout(
                    xaxis_title='Sale Price ($)',
                    yaxis_title='Number of Properties',
                    xaxis_tickformat='$,.0f'
                )
                
                price_sqft_time_div = html.Div([
                    html.H3("Price Distribution"),
                    dcc.Graph(figure=price_fig)
                ], style=styles['chart-container'])
        
        # Add info about data availability
        data_availability = html.Div()
        data_items = []
        
        if 'has_spatial_data' in stats:
            spatial_info = f"✓ {stats['spatial_data_count']} records with coordinates" if stats['has_spatial_data'] else "✗ No coordinate data available"
            data_items.append(html.P(f"Spatial Analysis: {spatial_info}"))
            
        if 'has_distance_data' in stats:
            distance_info = f"✓ {stats['distance_data_count']} records with distance measurements" if stats['has_distance_data'] else "✗ No distance data available"
            data_items.append(html.P(f"Distance Analysis: {distance_info}"))
            
        if 'has_area_data' in stats:
            area_info = f"✓ {stats['area_data_count']} records with area measurements" if stats['has_area_data'] else "✗ No area data available"
            data_items.append(html.P(f"Area Analysis: {area_info}"))
        
        if data_items:
            data_availability = html.Div([
                html.H3("Data Availability"),
                html.Div(data_items, style=styles['info-message'])
            ])
        
        # Combine all elements
        content = html.Div([
            html.H2("Property Data Summary"),
            summary_cards,
            area_cards,
            data_availability,
            # Only include price_sqft_time_div, property_types is removed
            price_sqft_time_div
        ])
        
        return content
    
    except Exception as e:
        print(f"Error in generate_summary_tab: {e}")
        traceback.print_exc()
        return html.Div([
            html.H4("Error generating summary tab:"),
            html.Pre(str(e))
        ])