#!/usr/bin/env python3
"""
Puerto Rico Property Dashboard - 3D Map Visualization Connector
--------------------------------------------------------------
This module serves as the main entry point for the map visualization tab,
importing and re-exporting the components from the separated modules.
"""

# Import the main functions from the separated modules
from map_data_processor import prepare_map_data, calculate_map_statistics
from map_visualization import (
    generate_kepler_map_tab, 
    create_map_visualization, 
    register_callbacks
)

# Re-export for backward compatibility
__all__ = [
    'generate_kepler_map_tab', 
    'prepare_map_data',
    'register_callbacks'
]