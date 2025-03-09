#!/usr/bin/env python3
"""
Puerto Rico Property Dashboard - Styles
--------------------------------------
This module contains shared styles for the dashboard UI components.
"""

# CSS styles dictionary for consistent UI styling across modules
styles = {
    'container': {
        'maxWidth': '1200px',
        'margin': '0 auto',
        'padding': '20px',
        'backgroundColor': 'white',
        'boxShadow': '0 0 10px rgba(0,0,0,0.1)'
    },
    'title': {
        'color': '#2c3e50',
        'marginTop': '0'
    },
    'card-container': {
        'display': 'flex',
        'flexWrap': 'wrap',
        'gap': '20px',
        'marginBottom': '20px'
    },
    'summary-card': {
        'flex': '1',
        'minWidth': '200px',
        'backgroundColor': '#f8f9fa',
        'padding': '15px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
    },
    'chart-row': {
        'display': 'flex',
        'flexWrap': 'wrap',
        'gap': '20px',
        'marginBottom': '20px'
    },
    'chart-container': {
        'flex': '1 1 450px',
        'minWidth': '450px',
        'marginBottom': '20px',
        'backgroundColor': 'white',
        'padding': '15px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
    },
    'table-container': {
        'marginBottom': '30px',
        'backgroundColor': 'white',
        'padding': '15px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'
    },
    'upload': {
        'width': '100%',
        'height': '60px',
        'lineHeight': '60px',
        'borderWidth': '1px',
        'borderStyle': 'dashed',
        'borderRadius': '5px',
        'textAlign': 'center',
        'margin': '10px 0'
    },
    'error-message': {
        'backgroundColor': '#ffebee',
        'color': '#c62828',
        'padding': '15px',
        'borderRadius': '5px',
        'marginBottom': '20px'
    },
    'info-message': {
        'backgroundColor': '#e3f2fd',
        'color': '#0d47a1',
        'padding': '15px',
        'borderRadius': '5px',
        'marginBottom': '20px'
    },
    'success-message': {
        'backgroundColor': '#e8f5e9',
        'color': '#2e7d32',
        'padding': '15px',
        'borderRadius': '5px',
        'marginBottom': '20px'
    },
    'warning-message': {
        'backgroundColor': '#fff8e1',
        'color': '#f57f17',
        'padding': '15px',
        'borderRadius': '5px',
        'marginBottom': '20px'
    },
    'tab-content': {
        'padding': '20px',
        'border': '1px solid #ddd',
        'borderTop': 'none',
        'borderRadius': '0 0 5px 5px'
    },
    'footer': {
        'textAlign': 'center',
        'padding': '20px',
        'marginTop': '40px',
        'borderTop': '1px solid #eee',
        'color': '#777'
    }
}