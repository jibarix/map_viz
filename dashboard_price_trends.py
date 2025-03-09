#!/usr/bin/env python3
"""
Puerto Rico Property Dashboard - Price Trends Tab
------------------------------------------------
This module contains the UI components for the Price Trends tab.
"""

from dash import html, dcc, dash_table
import plotly.graph_objects as go
import traceback

# Import dashboard styles
from dashboard_styles import styles

# Import data processing functions
from dashboard_data import calculate_yearly_stats

def generate_price_trends_tab(df):
    """
    Generate content for the price trends tab
    
    Args:
        df: Pandas DataFrame containing property data
        
    Returns:
        Dash HTML component containing the price trends tab content
    """
    try:
        # Check if we have the necessary data
        if 'SALESDTTM_FORMATTED' not in df.columns or 'SALESAMT' not in df.columns:
            return html.Div([
                html.H2("Price Trends Analysis"),
                html.Div(
                    html.P("Date or sales data is missing for price trend analysis."),
                    style=styles['error-message']
                )
            ])
        
        # Get yearly statistics
        recent_years = calculate_yearly_stats(df)
        if recent_years is None or len(recent_years) == 0:
            return html.Div([
                html.H2("Price Trends Analysis"),
                html.Div(
                    html.P("Not enough yearly data for price trend analysis."),
                    style=styles['error-message']
                )
            ])
        
        # Create price trends chart
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=recent_years['Year'],
            y=recent_years['Avg_Price'],
            mode='lines+markers',
            name='Average Price',
            line=dict(color='blue', width=2)
        ))
        fig1.add_trace(go.Scatter(
            x=recent_years['Year'],
            y=recent_years['Median_Price'],
            mode='lines+markers',
            name='Median Price',
            line=dict(color='green', width=2)
        ))
        
        fig1.update_layout(
            title='Property Prices Over Time',
            xaxis_title='Year',
            yaxis_title='Price ($)',
            yaxis_tickformat='$,.0f',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Create sales count chart
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=recent_years['Year'],
            y=recent_years['Sales_Count'],
            name='Number of Sales',
            marker_color='gray'
        ))
        
        fig2.update_layout(
            title='Number of Property Sales by Year',
            xaxis_title='Year',
            yaxis_title='Number of Sales'
        )
        
        # Create data table
        data_table = dash_table.DataTable(
            id='yearly-data-table',
            columns=[
                {"name": "Year", "id": "Year"},
                {"name": "Sales Count", "id": "Sales_Count"},
                {"name": "Average Price", "id": "Avg_Price", "type": "numeric", "format": {"specifier": "$,.2f"}},
                {"name": "Median Price", "id": "Median_Price", "type": "numeric", "format": {"specifier": "$,.2f"}},
                {"name": "Min Price", "id": "Min_Price", "type": "numeric", "format": {"specifier": "$,.2f"}},
                {"name": "Max Price", "id": "Max_Price", "type": "numeric", "format": {"specifier": "$,.2f"}}
            ],
            data=recent_years.to_dict('records'),
            sort_action="native",
            sort_mode="multi",
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'minWidth': '100px'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        )
        
        # Combine everything
        content = html.Div([
            html.H2("Price Trends Analysis"),
            html.Div([
                html.Div([
                    dcc.Graph(figure=fig1)
                ], style=styles['chart-container']),
                html.Div([
                    dcc.Graph(figure=fig2)
                ], style=styles['chart-container'])
            ], style=styles['chart-row']),
            html.Div([
                html.H3("Yearly Sales Data"),
                data_table
            ], style=styles['table-container'])
        ])
        
        return content
    
    except Exception as e:
        print(f"Error in generate_price_trends_tab: {e}")
        traceback.print_exc()
        return html.Div([
            html.H4("Error generating price trends tab:"),
            html.Pre(str(e))
        ])