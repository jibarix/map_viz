#!/usr/bin/env python3
"""
Puerto Rico Property Dashboard - Area Analysis Tab
-------------------------------------------------
This module contains the UI components for the Area Analysis tab.
"""

from dash import html, dcc, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import traceback

# Import dashboard styles
from dashboard_styles import styles

def generate_area_analysis_tab(df):
    """
    Generate content for the area analysis tab
    
    Args:
        df: Pandas DataFrame containing property data
        
    Returns:
        Dash HTML component containing the area analysis tab content
    """
    try:
        # Initial content container
        content = html.Div([
            html.H2("Property Area Analysis")
        ])
        
        # Check if we have the necessary data
        if 'CABIDA' not in df.columns or 'SALESAMT' not in df.columns:
            content.children.append(html.Div(
                html.P("Area data (CABIDA) or price data (SALESAMT) is missing for area analysis."),
                style=styles['error-message']
            ))
            return content
        
        # Count records with valid area measurements
        valid_area_count = df.dropna(subset=['CABIDA']).shape[0]
        if valid_area_count == 0:
            content.children.append(html.Div(
                html.P("No valid area data found. All area measurements are missing or invalid."),
                style=styles['error-message']
            ))
            return content
        
        # Add info about available data
        content.children.append(html.Div(
            html.P(f"Found {valid_area_count} properties with valid area measurements."),
            style=styles['info-message']
        ))
        
        # Prepare data for area analysis
        area_df = prepare_area_analysis_data(df)
        if area_df is None or len(area_df) == 0:
            content.children.append(html.Div(
                html.P("After filtering for valid sales, no valid area data remained for analysis."),
                style=styles['error-message']
            ))
            return content
        
        # Add summary statistics card
        summary_stats = calculate_area_summary_stats(area_df)
        if summary_stats:
            stats_card = html.Div([
                html.Div([
                    html.H3("Area and Price Statistics"),
                    html.Div([
                        html.Div([
                            html.P(f"Average property size: {summary_stats['avg_area_sqm']:.2f} m² ({summary_stats['avg_area_sqft']:.2f} sq ft)"),
                            html.P(f"Median property size: {summary_stats['median_area_sqm']:.2f} m² ({summary_stats['median_area_sqft']:.2f} sq ft)"),
                            html.P(f"Size range: {summary_stats['min_area_sqm']:.2f} - {summary_stats['max_area_sqm']:.2f} m²")
                        ], style={'flex': '1'}),
                        html.Div([
                            html.P(f"Average price per sq ft: ${summary_stats['avg_price_per_sqft']:.2f}"),
                            html.P(f"Median price per sq ft: ${summary_stats['median_price_per_sqft']:.2f}"),
                            html.P(f"Price per sq ft range: ${summary_stats['min_price_per_sqft']:.2f} - ${summary_stats['max_price_per_sqft']:.2f}")
                        ], style={'flex': '1'})
                    ], style={'display': 'flex', 'flexWrap': 'wrap'})
                ], style=styles['summary-card'])
            ], style=styles['card-container'])
            
            content.children.append(stats_card)
        
        # Create a scatter plot of area vs price
        scatter_div = html.Div()
        try:
            scatter_fig = px.scatter(
                area_df,
                x='area_sqft',
                y='SALESAMT',
                title='Property Prices vs Area',
                labels={
                    'area_sqft': 'Property Area (sq ft)',
                    'SALESAMT': 'Sale Price ($)'
                },
                opacity=0.7,
                trendline='ols' if len(area_df) >= 10 else None
            )
            
            scatter_fig.update_layout(
                xaxis_title='Property Area (sq ft)',
                yaxis_title='Sale Price ($)',
                yaxis_tickformat='$,.0f'
            )
            
            scatter_div = html.Div([
                dcc.Graph(figure=scatter_fig)
            ], style=styles['chart-container'])
            
        except Exception as e:
            print(f"Error creating area scatter plot: {e}")
            scatter_div = html.Div(
                html.P(f"Error creating area scatter plot: {str(e)}"),
                style=styles['error-message']
            )
        
        content.children.append(scatter_div)
        
        # Create a scatter plot of area vs price per sqft
        price_sqft_div = html.Div()
        try:
            price_sqft_fig = px.scatter(
                area_df,
                x='area_sqft',
                y='price_per_sqft',
                title='Price per Square Foot vs Property Area',
                labels={
                    'area_sqft': 'Property Area (sq ft)',
                    'price_per_sqft': 'Price per Square Foot ($)'
                },
                opacity=0.7,
                trendline='ols' if len(area_df) >= 10 else None
            )
            
            price_sqft_fig.update_layout(
                xaxis_title='Property Area (sq ft)',
                yaxis_title='Price per Square Foot ($)',
                yaxis_tickformat='$,.2f'
            )
            
            price_sqft_div = html.Div([
                dcc.Graph(figure=price_sqft_fig)
            ], style=styles['chart-container'])
            
        except Exception as e:
            print(f"Error creating price per sqft plot: {e}")
            price_sqft_div = html.Div(
                html.P(f"Error creating price per square foot plot: {str(e)}"),
                style=styles['error-message']
            )
        
        content.children.append(price_sqft_div)
        
        # Calculate area bin statistics
        bin_stats = calculate_area_bin_stats(area_df)
        bin_stats_div = html.Div()
        
        if bin_stats is not None and len(bin_stats) > 0:
            try:
                # Create bar chart of average price per sqft by area bin
                bar_fig = px.bar(
                    bin_stats,
                    x='Area_Range',
                    y='Avg_Price_Per_Sqft',
                    title='Average Price per Square Foot by Property Size',
                    labels={
                        'Area_Range': 'Property Size Range (sq ft)',
                        'Avg_Price_Per_Sqft': 'Avg Price per Sq Ft ($)'
                    },
                    text_auto='.2f'
                )
                
                bar_fig.update_layout(
                    yaxis_tickformat='$,.2f'
                )
                
                # Create table of area bin statistics
                bin_stats_table = dash_table.DataTable(
                    id='area-bin-table',
                    columns=[
                        {"name": "Property Size Range", "id": "Area_Range"},
                        {"name": "Property Count", "id": "Property_Count"},
                        {"name": "Avg Price", "id": "Avg_Price", "type": "numeric", "format": {"specifier": "$,.2f"}},
                        {"name": "Avg Price/Sqft", "id": "Avg_Price_Per_Sqft", "type": "numeric", "format": {"specifier": "$,.2f"}},
                        {"name": "Median Price/Sqft", "id": "Median_Price_Per_Sqft", "type": "numeric", "format": {"specifier": "$,.2f"}},
                        {"name": "Avg Area (sq ft)", "id": "Avg_Area", "type": "numeric", "format": {"specifier": ",.2f"}}
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
                        html.H3("Price Statistics by Property Size"),
                        bin_stats_table
                    ], style=styles['table-container'])
                ])
            except Exception as e:
                print(f"Error creating area bin statistics visualization: {e}")
                bin_stats_div = html.Div(
                    html.P(f"Error creating area bin statistics visualization: {str(e)}"),
                    style=styles['error-message']
                )
        else:
            bin_stats_div = html.Div(
                html.P("Could not calculate area bin statistics. Not enough data for meaningful bins."),
                style=styles['info-message']
            )
        
        content.children.append(bin_stats_div)
        
        # Create distribution of price per sqft
        dist_div = html.Div()
        try:
            dist_fig = px.histogram(
                area_df,
                x='price_per_sqft',
                nbins=20,
                title='Distribution of Price per Square Foot',
                labels={'price_per_sqft': 'Price per Square Foot ($)'}
            )
            
            dist_fig.update_layout(
                xaxis_title='Price per Square Foot ($)',
                yaxis_title='Number of Properties',
                xaxis_tickformat='$,.2f'
            )
            
            dist_div = html.Div([
                dcc.Graph(figure=dist_fig)
            ], style=styles['chart-container'])
            
        except Exception as e:
            print(f"Error creating price per sqft distribution: {e}")
            dist_div = html.Div(
                html.P(f"Error creating price per square foot distribution: {str(e)}"),
                style=styles['error-message']
            )
        
        content.children.append(dist_div)
        
        return content
    
    except Exception as e:
        print(f"Error in generate_area_analysis_tab: {e}")
        traceback.print_exc()
        return html.Div([
            html.H4("Error generating area analysis tab:"),
            html.Pre(str(e)),
            html.Hr(),
            html.Pre(traceback.format_exc())
        ])

def prepare_area_analysis_data(df, max_price=2000000):
    """Prepare data for area analysis"""
    # Create a copy to avoid modifying the original
    area_df = df.copy()
    
    # Filter for valid area and valid sales
    area_df = area_df[(area_df['VALID_SALE']) & 
                      (area_df['CABIDA'] > 0) & 
                      (area_df['CABIDA'].notna()) &
                      (area_df['SALESAMT'] <= max_price)]
    
    # Convert square meters to square feet (1 sq meter = 10.764 sq ft)
    area_df['area_sqft'] = area_df['CABIDA'] * 10.764
    
    # Calculate price per square foot
    area_df['price_per_sqft'] = area_df['SALESAMT'] / area_df['area_sqft']
    
    # Remove extreme outliers in price per sqft
    q1 = area_df['price_per_sqft'].quantile(0.05)
    q3 = area_df['price_per_sqft'].quantile(0.95)
    area_df = area_df[(area_df['price_per_sqft'] >= q1) & (area_df['price_per_sqft'] <= q3)]
    
    print(f"Records with valid area and price data after filtering: {len(area_df)}")
    
    return area_df if len(area_df) > 0 else None

def calculate_area_summary_stats(area_df):
    """Calculate summary statistics for area analysis"""
    if area_df is None or len(area_df) == 0:
        return None
    
    summary = {}
    
    # Area statistics in square meters
    summary['avg_area_sqm'] = area_df['CABIDA'].mean()
    summary['median_area_sqm'] = area_df['CABIDA'].median()
    summary['min_area_sqm'] = area_df['CABIDA'].min()
    summary['max_area_sqm'] = area_df['CABIDA'].max()
    
    # Area statistics in square feet
    summary['avg_area_sqft'] = area_df['area_sqft'].mean()
    summary['median_area_sqft'] = area_df['area_sqft'].median()
    summary['min_area_sqft'] = area_df['area_sqft'].min()
    summary['max_area_sqft'] = area_df['area_sqft'].max()
    
    # Price per square foot statistics
    summary['avg_price_per_sqft'] = area_df['price_per_sqft'].mean()
    summary['median_price_per_sqft'] = area_df['price_per_sqft'].median()
    summary['min_price_per_sqft'] = area_df['price_per_sqft'].min()
    summary['max_price_per_sqft'] = area_df['price_per_sqft'].max()
    
    return summary

def calculate_area_bin_stats(area_df, num_bins=5):
    """Calculate statistics by area bins"""
    # Validate inputs
    if area_df is None or len(area_df) == 0:
        print("No area data available for bin statistics")
        return None
    
    # Adjust number of bins based on amount of data
    if len(area_df) < 10:
        num_bins = 2
    elif len(area_df) < 30:
        num_bins = 3
    
    try:
        # Create area bins
        area_df['area_bin'] = pd.qcut(
            area_df['area_sqft'],
            q=num_bins,
            duplicates='drop'
        )
        
        # Group by area bins
        bin_stats = area_df.groupby('area_bin').agg({
            'SALESAMT': ['count', 'mean'],
            'price_per_sqft': ['mean', 'median'],
            'area_sqft': 'mean'
        }).reset_index()
        
        # Flatten columns
        bin_stats.columns = [
            'Area_Range', 'Property_Count', 'Avg_Price', 
            'Avg_Price_Per_Sqft', 'Median_Price_Per_Sqft', 'Avg_Area'
        ]
        
        # Convert the pandas Interval objects to strings for JSON serialization
        bin_stats['Area_Range'] = bin_stats['Area_Range'].astype(str)
        
        print(f"Created area bin statistics with {len(bin_stats)} bins")
        return bin_stats
    
    except Exception as e:
        print(f"Error creating area bin statistics: {str(e)}")
        return None