#!/usr/bin/env python3
"""
Puerto Rico Property Dashboard - Server Connection (Modular Version)
-------------------------------------------------------------------
This file handles the server connection and initialization for the dashboard.
"""

import dash
from dash import html
import traceback
import sys
import warnings

# Suppress React lifecycle method warnings from Plotly
warnings.filterwarnings("ignore", category=UserWarning, module="plotly")
warnings.filterwarnings("ignore", category=FutureWarning, module="plotly")

# Import dashboard styles
from dashboard_styles import styles

print("Initializing Dash application...")

# Initialize the Dash app
app = dash.Dash(
    __name__, 
    title="PR Property Dashboard",
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

# Create the Flask server
server = app.server

# Default layout - will be replaced by dashboard components
app.layout = html.Div([
    html.H1("PR Property Dashboard"),
    html.P("Loading dashboard components...")
])

# Import dashboard components after app is created to avoid circular imports
try:
    print("Loading dashboard UI components...")
    from dashboard_ui import init_dashboard_ui
    init_dashboard_ui(app)
    print("Dashboard UI components loaded successfully")
except Exception as e:
    print(f"Error loading dashboard UI components: {e}")
    traceback.print_exc()
    
    # Set error layout
    app.layout = html.Div([
        html.H1("Dashboard Error"),
        html.P("An error occurred while loading the dashboard components:"),
        html.Pre(str(e)),
        html.Hr(),
        html.P("Check the console for detailed error information.")
    ], style={'padding': '20px', 'color': 'red'})

# Run the server
if __name__ == '__main__':
    try:
        print(f"Starting Dash server on port 8050...")
        print(f"Python version: {sys.version}")
        print(f"Dash version: {dash.__version__}")
        app.run_server(debug=True)
        print("Server started successfully")
    except Exception as e:
        print(f"Error starting server: {e}")
        traceback.print_exc()