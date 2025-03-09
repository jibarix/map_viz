#!/usr/bin/env python3
"""
Puerto Rico Property Dashboard - Property Values Tab
---------------------------------------------------
This module contains the UI components for the Property Values tab.
"""

from dash import html, dcc, dash_table
import plotly.express as px
import plotly.graph_objects as go
import traceback

# Import dashboard styles
from dashboard_styles import styles

# Import data processing functions
from dashboard_data import (
    prepare_price_distribution_data,
    calculate_property_components,
    calculate_property_type_stats
)

def generate_property_values_tab(df):
    """
    Generate content for property values tab
    
    Args:
        df: Pandas DataFrame containing property data
        
    Returns:
        Dash HTML component containing the property values tab content
    """
    try:
        # Initialize container
        content = html.Div([
            html.H2("Property Values Analysis")
        ])
        
        # Price distribution histogram
        sales_df = prepare_price_distribution_data(df)
        if sales_df is not None:
            price_fig = px.histogram(
                sales_df,
                x='SALESAMT',
                nbins=30,
                title='Distribution of Property Sale Prices',
                labels={'SALESAMT': 'Sale Price ($)'},
                color_discrete_sequence=['blue']
            )
            
            price_fig.update_layout(
                xaxis_title='Sale Price ($)',
                yaxis_title='Number of Properties',
                xaxis_tickformat='$,.0f'
            )
            
            content.children.append(html.Div([
                dcc.Graph(figure=price_fig)
            ], style=styles['chart-container']))
        else:
            content.children.append(html.Div(
                html.P("Not enough valid sales data to display price distribution."),
                style=styles['info-message']
            ))
        
        # Property value components
        components_data = calculate_property_components(df)
        if components_data is not None:
            components_fig = px.bar(
                components_data,
                x='Component',
                y='Value',
                title='Average Property Value Components',
                labels={'Value': 'Value ($)'},
                color_discrete_sequence=['green']
            )
            
            components_fig.update_layout(
                yaxis_tickformat='$,.0f'
            )
            
            content.children.append(html.Div([
                dcc.Graph(figure=components_fig)
            ], style=styles['chart-container']))
        else:
            content.children.append(html.Div(
                html.P("Property component data (LAND, STRUCTURE, MACHINERY) is missing or incomplete."),
                style=styles['info-message']
            ))
        
        # Total value vs sale price scatter plot
        if all(col in df.columns for col in ['TOTALVAL', 'SALESAMT']) and 'VALID_SALE' in df.columns and sum(df['VALID_SALE']) > 0:
            # Filter data
            plot_df = df[(df['VALID_SALE']) & (df['TOTALVAL'] > 0) & (df['SALESAMT'] <= 2000000)]
            
            if len(plot_df) > 0:
                scatter_fig = px.scatter(
                    plot_df,
                    x='TOTALVAL',
                    y='SALESAMT',
                    title='Property Value vs Sale Price',
                    labels={
                        'TOTALVAL': 'Total Assessed Value ($)',
                        'SALESAMT': 'Sale Price ($)'
                    },
                    opacity=0.7
                )
                
                # Add diagonal line (x=y)
                max_val = max(plot_df['TOTALVAL'].max(), plot_df['SALESAMT'].max())
                scatter_fig.add_trace(
                    go.Scatter(
                        x=[0, max_val],
                        y=[0, max_val],
                        mode='lines',
                        line=dict(color='red', dash='dash'),
                        showlegend=False
                    )
                )
                
                scatter_fig.update_layout(
                    xaxis_tickformat='$,.0f',
                    yaxis_tickformat='$,.0f'
                )
                
                content.children.append(html.Div([
                    dcc.Graph(figure=scatter_fig)
                ], style=styles['chart-container']))
        
        # Create a table of property value statistics by property type
        type_stats = calculate_property_type_stats(df)
        if type_stats is not None:
            type_stats_table = dash_table.DataTable(
                id='type-stats-table',
                columns=[
                    {"name": "Property Type", "id": "Property_Type"},
                    {"name": "Sales Count", "id": "Sales_Count"},
                    {"name": "Avg Sale Price", "id": "Avg_Sale_Price", "type": "numeric", "format": {"specifier": "$,.2f"}},
                    {"name": "Median Sale Price", "id": "Median_Sale_Price", "type": "numeric", "format": {"specifier": "$,.2f"}},
                    {"name": "Avg Value", "id": "Avg_Value", "type": "numeric", "format": {"specifier": "$,.2f"}},
                    {"name": "Median Value", "id": "Median_Value", "type": "numeric", "format": {"specifier": "$,.2f"}}
                ],
                data=type_stats.to_dict('records'),
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
            
            content.children.append(html.Div([
                html.H3("Property Value Statistics by Type"),
                type_stats_table
            ], style=styles['table-container']))
        
        return content
    
    except Exception as e:
        print(f"Error in generate_property_values_tab: {e}")
        traceback.print_exc()
        return html.Div([
            html.H4("Error generating property values tab:"),
            html.Pre(str(e))
        ])