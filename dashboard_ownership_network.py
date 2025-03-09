#!/usr/bin/env python3
"""
Puerto Rico Property Dashboard - Ownership Network Analysis Tab
-------------------------------------------------------------
This module contains the UI components for analyzing property ownership networks.
"""

from dash import html, dcc, dash_table
import plotly.graph_objects as go
import networkx as nx
import pandas as pd
import numpy as np
import traceback
from collections import Counter

# Import dashboard styles
from dashboard_styles import styles

def generate_ownership_network_tab(df):
    """
    Generate content for the ownership network analysis tab
    
    Args:
        df: Pandas DataFrame containing property data
        
    Returns:
        Dash HTML component containing the ownership network analysis tab content
    """
    try:
        # Initial content container
        content = html.Div([
            html.H2("Ownership Network Analysis")
        ])
        
        # Check if we have the necessary data
        required_columns = ['SELLERNAME', 'BYERNAME', 'SALESAMT', 'SALESDTTM_FORMATTED']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            content.children.append(html.Div(
                html.P(f"Missing required columns for ownership network analysis: {', '.join(missing_columns)}"),
                style=styles['error-message']
            ))
            return content
        
        # Prepare data for network analysis
        network_df = prepare_network_data(df)
        if network_df is None or len(network_df) == 0:
            content.children.append(html.Div(
                html.P("Not enough valid transaction data for network analysis."),
                style=styles['error-message']
            ))
            return content
        
        # Create network statistics
        stats_div = create_network_statistics(network_df)
        content.children.append(stats_div)
        
        # Create top buyers and sellers tables
        participant_tables = create_participant_tables(network_df)
        content.children.append(participant_tables)
        
        # Create network visualization
        network_div = create_network_visualization(network_df)
        content.children.append(network_div)
        
        # Add transaction flow diagram
        flow_div = create_transaction_flow_diagram(network_df)
        content.children.append(flow_div)
        
        return content
    
    except Exception as e:
        print(f"Error in generate_ownership_network_tab: {e}")
        traceback.print_exc()
        return html.Div([
            html.H4("Error generating ownership network tab:"),
            html.Pre(str(e)),
            html.Hr(),
            html.Pre(traceback.format_exc())
        ])

def prepare_network_data(df, min_transaction_amount=1000):
    """Prepare data for network analysis"""
    try:
        # Create a copy to avoid modifying the original
        net_df = df.copy()
        
        # Filter for rows with valid seller and buyer names and valid sale amount
        net_df = net_df[
            (net_df['SELLERNAME'].notna()) & 
            (net_df['SELLERNAME'] != '') &
            (net_df['BYERNAME'].notna()) & 
            (net_df['BYERNAME'] != '') &
            (net_df['SALESAMT'] >= min_transaction_amount)
        ].copy()
        
        if len(net_df) == 0:
            return None
        
        # Clean and standardize names to help with matching
        for col in ['SELLERNAME', 'BYERNAME']:
            net_df[col] = net_df[col].str.upper().str.strip()
        
        # Add a transaction ID
        net_df['TRANSACTION_ID'] = range(1, len(net_df) + 1)
        
        # Convert date if present
        if 'SALESDTTM_FORMATTED' in net_df.columns:
            net_df['SALESDTTM_FORMATTED'] = pd.to_datetime(net_df['SALESDTTM_FORMATTED'], errors='coerce')
        
        print(f"Prepared {len(net_df)} records for network analysis")
        return net_df
    
    except Exception as e:
        print(f"Error preparing network data: {e}")
        return None

def create_network_statistics(net_df):
    """Create summary statistics for the ownership network"""
    try:
        # Count unique participants
        unique_sellers = net_df['SELLERNAME'].nunique()
        unique_buyers = net_df['BYERNAME'].nunique()
        
        # Count all participants (some may be both buyers and sellers)
        all_participants = pd.concat([
            net_df['SELLERNAME'], 
            net_df['BYERNAME']
        ]).unique()
        total_participants = len(all_participants)
        
        # Calculate total transaction value
        total_value = net_df['SALESAMT'].sum()
        avg_transaction = net_df['SALESAMT'].mean()
        
        # Count repeat participants (appear more than once in either role)
        seller_counts = net_df['SELLERNAME'].value_counts()
        buyer_counts = net_df['BYERNAME'].value_counts()
        repeat_sellers = sum(seller_counts > 1)
        repeat_buyers = sum(buyer_counts > 1)
        
        # Count entities that are both buyers and sellers
        dual_participants = set(net_df['SELLERNAME']).intersection(set(net_df['BYERNAME']))
        dual_count = len(dual_participants)
        
        # Create statistics cards
        stats_div = html.Div([
            html.Div([
                html.H3("Network Statistics"),
                html.P(f"Total transactions: {len(net_df)}"),
                html.P(f"Total unique participants: {total_participants}"),
                html.P(f"Total transaction value: ${total_value:,.2f}"),
                html.P(f"Average transaction: ${avg_transaction:,.2f}")
            ], style=styles['summary-card']),
            
            html.Div([
                html.H3("Participant Details"),
                html.P(f"Unique sellers: {unique_sellers}"),
                html.P(f"Unique buyers: {unique_buyers}"),
                html.P(f"Participants as both buyer & seller: {dual_count} ({dual_count/total_participants*100:.1f}%)"),
                html.P(f"Repeat sellers: {repeat_sellers}"),
                html.P(f"Repeat buyers: {repeat_buyers}")
            ], style=styles['summary-card'])
        ], style=styles['card-container'])
        
        return stats_div
    
    except Exception as e:
        print(f"Error creating network statistics: {e}")
        return html.Div(
            html.P(f"Error generating network statistics: {str(e)}"),
            style=styles['error-message']
        )

def create_participant_tables(net_df, top_n=10):
    """Create tables for top buyers and sellers"""
    try:
        # Top sellers by number of properties sold
        top_sellers_count = net_df['SELLERNAME'].value_counts().reset_index()
        top_sellers_count.columns = ['Seller', 'Properties Sold']
        top_sellers_count = top_sellers_count.head(top_n)
        
        # Top sellers by total value
        top_sellers_value = net_df.groupby('SELLERNAME')['SALESAMT'].sum().reset_index()
        top_sellers_value.columns = ['Seller', 'Total Sales Value']
        top_sellers_value = top_sellers_value.sort_values('Total Sales Value', ascending=False).head(top_n)
        
        # Top buyers by number of properties purchased
        top_buyers_count = net_df['BYERNAME'].value_counts().reset_index()
        top_buyers_count.columns = ['Buyer', 'Properties Purchased']
        top_buyers_count = top_buyers_count.head(top_n)
        
        # Top buyers by total value
        top_buyers_value = net_df.groupby('BYERNAME')['SALESAMT'].sum().reset_index()
        top_buyers_value.columns = ['Buyer', 'Total Purchase Value']
        top_buyers_value = top_buyers_value.sort_values('Total Purchase Value', ascending=False).head(top_n)
        
        # Create tables
        sellers_count_table = dash_table.DataTable(
            id='top-sellers-count',
            columns=[
                {"name": "Seller", "id": "Seller"},
                {"name": "Properties Sold", "id": "Properties Sold"}
            ],
            data=top_sellers_count.to_dict('records'),
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
        )
        
        sellers_value_table = dash_table.DataTable(
            id='top-sellers-value',
            columns=[
                {"name": "Seller", "id": "Seller"},
                {"name": "Total Sales Value", "id": "Total Sales Value", "type": "numeric", "format": {"specifier": "$,.2f"}}
            ],
            data=top_sellers_value.to_dict('records'),
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
        )
        
        buyers_count_table = dash_table.DataTable(
            id='top-buyers-count',
            columns=[
                {"name": "Buyer", "id": "Buyer"},
                {"name": "Properties Purchased", "id": "Properties Purchased"}
            ],
            data=top_buyers_count.to_dict('records'),
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
        )
        
        buyers_value_table = dash_table.DataTable(
            id='top-buyers-value',
            columns=[
                {"name": "Buyer", "id": "Buyer"},
                {"name": "Total Purchase Value", "id": "Total Purchase Value", "type": "numeric", "format": {"specifier": "$,.2f"}}
            ],
            data=top_buyers_value.to_dict('records'),
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
        )
        
        # Combine tables into a layout
        tables_div = html.Div([
            html.Div([
                html.H3("Top Sellers (By Count)"),
                sellers_count_table
            ], style=styles['table-container']),
            
            html.Div([
                html.H3("Top Sellers (By Value)"),
                sellers_value_table
            ], style=styles['table-container']),
            
            html.Div([
                html.H3("Top Buyers (By Count)"),
                buyers_count_table
            ], style=styles['table-container']),
            
            html.Div([
                html.H3("Top Buyers (By Value)"),
                buyers_value_table
            ], style=styles['table-container'])
        ])
        
        return tables_div
    
    except Exception as e:
        print(f"Error creating participant tables: {e}")
        return html.Div(
            html.P(f"Error generating participant tables: {str(e)}"),
            style=styles['error-message']
        )

def create_network_visualization(net_df, max_nodes=50):
    """Create network visualization of ownership transfers"""
    try:
        # Create a NetworkX graph
        G = nx.DiGraph()
        
        # If we have too many transactions, sample to reduce visual complexity
        sample_df = net_df
        if len(net_df) > max_nodes:
            # Focus on major participants
            top_sellers = net_df['SELLERNAME'].value_counts().nlargest(max_nodes // 2).index
            top_buyers = net_df['BYERNAME'].value_counts().nlargest(max_nodes // 2).index
            
            # Filter to include only transactions involving top participants
            sample_df = net_df[
                (net_df['SELLERNAME'].isin(top_sellers)) | 
                (net_df['BYERNAME'].isin(top_buyers))
            ].head(max_nodes)
        
        # Add nodes and edges
        for _, row in sample_df.iterrows():
            seller = row['SELLERNAME']
            buyer = row['BYERNAME']
            amount = row['SALESAMT']
            
            # Add nodes if they don't exist
            if seller not in G:
                G.add_node(seller, type='seller')
            if buyer not in G:
                G.add_node(buyer, type='buyer')
            
            # Add or update edge
            if G.has_edge(seller, buyer):
                G[seller][buyer]['weight'] += 1
                G[seller][buyer]['total_value'] += amount
            else:
                G.add_edge(seller, buyer, weight=1, total_value=amount)
        
        # Calculate node positions using a spring layout
        pos = nx.spring_layout(G)
        
        # Create edge traces
        edge_traces = []
        for edge in G.edges(data=True):
            source, target, data = edge
            x0, y0 = pos[source]
            x1, y1 = pos[target]
            
            # Scale line width based on weight (number of transactions)
            width = min(data['weight'] * 2, 10)
            
            # Scale opacity based on total value
            max_value = max([e[2]['total_value'] for e in G.edges(data=True)])
            opacity = min(data['total_value'] / max_value, 1) * 0.8 + 0.2
            
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                line=dict(width=width, color=f'rgba(100, 100, 100, {opacity})'),
                hoverinfo='text',
                text=f"Transactions: {data['weight']}<br>Total Value: ${data['total_value']:,.2f}",
                mode='lines'
            )
            edge_traces.append(edge_trace)
        
        # Create node traces
        node_traces = {}
        
        # Identify nodes that are both buyers and sellers
        both_roles = set(sample_df['SELLERNAME']).intersection(set(sample_df['BYERNAME']))
        
        # Create separate traces for different node types
        for node_type, color in [
            ('seller', 'red'), 
            ('buyer', 'blue'), 
            ('both', 'purple')
        ]:
            node_traces[node_type] = go.Scatter(
                x=[],
                y=[],
                text=[],
                mode='markers',
                hoverinfo='text',
                marker=dict(
                    color=color,
                    size=15,
                    line=dict(width=2, color='black')
                )
            )
        
        # Add nodes to the appropriate trace
        for node in G.nodes():
            x, y = pos[node]
            
            # Determine node type
            node_type = 'both' if node in both_roles else 'seller' if node in sample_df['SELLERNAME'].values else 'buyer'
            
            # Add to the appropriate trace
            node_traces[node_type]['x'] = node_traces[node_type]['x'] + (x,)
            node_traces[node_type]['y'] = node_traces[node_type]['y'] + (y,)
            
            # Calculate node statistics
            sells = sample_df[sample_df['SELLERNAME'] == node]['SALESAMT'].sum()
            buys = sample_df[sample_df['BYERNAME'] == node]['SALESAMT'].sum()
            
            # Create hover text
            node_traces[node_type]['text'] = node_traces[node_type]['text'] + (
                f"Name: {node}<br>"
                f"Role: {node_type.title()}<br>"
                f"Total Sales: ${sells:,.2f}<br>"
                f"Total Purchases: ${buys:,.2f}",
            )
        
        # Create figure with corrected configuration
        fig = go.Figure(
            data=edge_traces + list(node_traces.values()),
            layout=go.Layout(
                title='Property Ownership Network',
                titlefont=dict(size=16),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                annotations=[
                    dict(
                        text="Network of property transfers between buyers and sellers<br>"
                             "Red: Sellers | Blue: Buyers | Purple: Both",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.01, y=-0.01
                    )
                ],
                # Removed the problematic 'uirevision' property
                dragmode='pan'
            )
        )
        
        # Create the network visualization div with corrected config
        network_div = html.Div([
            html.H3("Property Transfer Network"),
            dcc.Graph(
                figure=fig,
                config={
                    'scrollZoom': True,
                    'displayModeBar': True,
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                    'responsive': True,
                    # Removed problematic 'useResizeHandler' and 'eventListenerOptions'
                    'doubleClick': 'reset'
                }
            )
        ], style=styles['chart-container'])
        
        return network_div
    
    except Exception as e:
        print(f"Error creating network visualization: {e}")
        return html.Div(
            html.P(f"Error generating network visualization: {str(e)}"),
            style=styles['error-message']
        )

def create_transaction_flow_diagram(net_df, top_n=5):
    """Create a Sankey diagram showing transaction flows between top entities"""
    try:
        # Get top participants by transaction count
        top_sellers = net_df['SELLERNAME'].value_counts().nlargest(top_n).index.tolist()
        top_buyers = net_df['BYERNAME'].value_counts().nlargest(top_n).index.tolist()
        
        # Include transactions involving top participants
        flow_df = net_df[
            (net_df['SELLERNAME'].isin(top_sellers)) | 
            (net_df['BYERNAME'].isin(top_buyers))
        ].copy()
        
        if len(flow_df) == 0:
            return html.Div(
                html.P("Not enough data for transaction flow diagram."),
                style=styles['info-message']
            )
        
        # Group other participants
        flow_df.loc[~flow_df['SELLERNAME'].isin(top_sellers), 'SELLERNAME'] = 'Other Sellers'
        flow_df.loc[~flow_df['BYERNAME'].isin(top_buyers), 'BYERNAME'] = 'Other Buyers'
        
        # Aggregate flows
        flows = flow_df.groupby(['SELLERNAME', 'BYERNAME'])['SALESAMT'].sum().reset_index()
        
        # Prepare nodes and links for Sankey diagram
        all_nodes = list(set(flows['SELLERNAME'].tolist() + flows['BYERNAME'].tolist()))
        node_indices = {node: i for i, node in enumerate(all_nodes)}
        
        sankey_links = []
        for _, row in flows.iterrows():
            sankey_links.append({
                'source': node_indices[row['SELLERNAME']],
                'target': node_indices[row['BYERNAME']],
                'value': row['SALESAMT']
            })
        
        # Create Sankey diagram with corrected configuration
        sankey_fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_nodes,
                color=["rgba(255,0,0,0.8)" if "Seller" in n else "rgba(0,0,255,0.8)" for n in all_nodes]
            ),
            link=dict(
                source=[link['source'] for link in sankey_links],
                target=[link['target'] for link in sankey_links],
                value=[link['value'] for link in sankey_links]
            )
        )])
        
        sankey_fig.update_layout(
            title_text="Property Transaction Flows",
            font_size=12,
            # Removed problematic 'uirevision' property
            dragmode='pan'
        )
        
        # Create the flow diagram div with corrected config
        flow_div = html.Div([
            html.H3("Transaction Flow Diagram"),
            dcc.Graph(
                figure=sankey_fig,
                config={
                    'displayModeBar': True,
                    'responsive': True,
                    # Removed problematic 'useResizeHandler' and 'eventListenerOptions'
                    'doubleClick': 'reset'
                }
            )
        ], style=styles['chart-container'])
        
        return flow_div
    
    except Exception as e:
        print(f"Error creating transaction flow diagram: {e}")
        return html.Div(
            html.P(f"Error generating transaction flow diagram: {str(e)}"),
            style=styles['error-message']
        )