#!/usr/bin/env python3
"""
Puerto Rico Property Dashboard - Map Data Processing Module
----------------------------------------------------------
This module handles data processing, preparation, and statistics calculation
for the interactive map visualization component.
"""

import pandas as pd
import numpy as np
import traceback

def prepare_map_data(df):
    """
    Prepare data for map visualization
    
    Args:
        df: Input DataFrame with property data
        
    Returns:
        DataFrame with cleaned data ready for map visualization
    """
    try:
        # Create a copy to avoid modifying the original
        map_df = df.copy()
        
        # Filter to records with valid coordinates
        map_df = map_df.dropna(subset=['INSIDE_X', 'INSIDE_Y'])
        
        # Remove any records with 0 coordinates (likely invalid)
        map_df = map_df[(map_df['INSIDE_X'] != 0) & (map_df['INSIDE_Y'] != 0)]
        
        # Keep only essential columns for the map
        keep_cols = ['INSIDE_X', 'INSIDE_Y', 'CATASTRO', 'MUNICIPIO', 'TIPO', 'CABIDA', 
                     'SALESAMT', 'TOTALVAL', 'SALESDTTM_FORMATTED']
        
        map_df = map_df[[col for col in keep_cols if col in map_df.columns]]
        
        # Process sales amount data
        if 'SALESAMT' in map_df.columns:
            map_df['SALESAMT'] = pd.to_numeric(map_df['SALESAMT'], errors='coerce')
            # Fill NaN values with 0
            map_df['SALESAMT'] = map_df['SALESAMT'].fillna(0)
        
        # Calculate price per square foot if both columns are available
        if 'SALESAMT' in map_df.columns and 'CABIDA' in map_df.columns:
            # Convert to numeric
            map_df['CABIDA'] = pd.to_numeric(map_df['CABIDA'], errors='coerce')
            # Remove zeros to avoid division by zero
            valid_area = (map_df['CABIDA'] > 0)
            # Calculate price per square foot (1 sq meter = 10.764 sq ft)
            map_df['price_per_sqft'] = 0
            map_df.loc[valid_area, 'price_per_sqft'] = map_df.loc[valid_area, 'SALESAMT'] / (map_df.loc[valid_area, 'CABIDA'] * 10.764)
            
            # Remove extreme outliers
            # Use quantiles to handle any remaining oddities in the data
            q_low = map_df['price_per_sqft'].quantile(0.01)
            q_high = map_df['price_per_sqft'].quantile(0.99)
            map_df.loc[(map_df['price_per_sqft'] < q_low) | (map_df['price_per_sqft'] > q_high), 'price_per_sqft'] = map_df['price_per_sqft'].median()
        
        # Fill missing values for categorical columns with 'Unknown'
        for col in ['TIPO', 'MUNICIPIO']:
            if col in map_df.columns:
                map_df[col] = map_df[col].fillna('Unknown')
        
        # Remove any null values which could cause WebGL rendering issues
        map_df = map_df.fillna({
            'INSIDE_X': map_df['INSIDE_X'].mean(),
            'INSIDE_Y': map_df['INSIDE_Y'].mean(),
            'SALESAMT': 0,
            'price_per_sqft': 0
        })
        
        # If dataset is too large, sample it to prevent browser performance issues
        if len(map_df) > 2000:
            print(f"Dataset contains {len(map_df)} points, sampling to 2000 for performance")
            map_df = map_df.sample(2000, random_state=42)
            
        return map_df
    
    except Exception as e:
        print(f"Error preparing map data: {e}")
        traceback.print_exc()
        return None

def create_hover_template(df):
    """
    Create a hover template and customdata array for map visualization
    
    Args:
        df: DataFrame with map data
        
    Returns:
        tuple: (hover_template, customdata_array)
    """
    # Create customdata array
    custom_cols = []
    
    # Add essential columns to customdata
    if 'CATASTRO' in df.columns:
        custom_cols.append(df['CATASTRO'])
    
    if 'TIPO' in df.columns:
        custom_cols.append(df['TIPO'])
    
    if 'MUNICIPIO' in df.columns:
        custom_cols.append(df['MUNICIPIO'])
    
    if 'SALESAMT' in df.columns:
        custom_cols.append(df['SALESAMT'])
    
    if 'price_per_sqft' in df.columns:
        custom_cols.append(df['price_per_sqft'])
    
    # Build hover template
    template_parts = []
    custom_index = 0
    
    if 'CATASTRO' in df.columns:
        template_parts.append("ID: %{customdata[" + str(custom_index) + "]}")
        custom_index += 1
    
    if 'TIPO' in df.columns:
        template_parts.append("Type: %{customdata[" + str(custom_index) + "]}")
        custom_index += 1
    
    if 'MUNICIPIO' in df.columns:
        template_parts.append("Municipality: %{customdata[" + str(custom_index) + "]}")
        custom_index += 1
    
    if 'SALESAMT' in df.columns:
        template_parts.append("Sale Price: $%{customdata[" + str(custom_index) + "]:.2f}")
        custom_index += 1
    
    if 'price_per_sqft' in df.columns:
        template_parts.append("Price per Sq Ft: $%{customdata[" + str(custom_index) + "]:.2f}")
        custom_index += 1
    
    # Add coordinates
    template_parts.append("<br>Longitude: %{x:.6f}")
    template_parts.append("Latitude: %{y:.6f}")
    
    # Add extra info tag
    template_parts.append("<extra></extra>")
    
    # Join parts into a single template string
    template = "<br>".join(template_parts)
    
    # If we have customdata columns, build the customdata array
    if custom_cols:
        customdata = np.column_stack(custom_cols)
    else:
        # Default empty customdata
        customdata = np.zeros((len(df), 1))
    
    return template, customdata

def calculate_map_statistics(map_df):
    """
    Calculate statistics for the map data
    
    Args:
        map_df: DataFrame with prepared map data
        
    Returns:
        dict: Statistics about the map data
    """
    stats = {}
    
    # Basic count
    stats['total_properties'] = len(map_df)
    
    # Sale price stats if available
    if 'SALESAMT' in map_df.columns:
        valid_sales = map_df[map_df['SALESAMT'] > 1000]
        stats['sales_count'] = len(valid_sales)
        stats['avg_price'] = valid_sales['SALESAMT'].mean() if len(valid_sales) > 0 else 0
        stats['max_price'] = valid_sales['SALESAMT'].max() if len(valid_sales) > 0 else 0
        stats['min_price'] = valid_sales['SALESAMT'].min() if len(valid_sales) > 0 else 0
    
    # Price per sqft stats if available
    if 'price_per_sqft' in map_df.columns:
        valid_price_sqft = map_df[map_df['price_per_sqft'] > 0]
        stats['price_sqft_count'] = len(valid_price_sqft)
        stats['avg_price_sqft'] = valid_price_sqft['price_per_sqft'].mean() if len(valid_price_sqft) > 0 else 0
        stats['max_price_sqft'] = valid_price_sqft['price_per_sqft'].max() if len(valid_price_sqft) > 0 else 0
        stats['min_price_sqft'] = valid_price_sqft['price_per_sqft'].min() if len(valid_price_sqft) > 0 else 0
    
    # Municipality stats if available
    if 'MUNICIPIO' in map_df.columns:
        top_municipalities = map_df['MUNICIPIO'].value_counts().head(3)
        stats['top_municipality'] = top_municipalities.index[0] if len(top_municipalities) > 0 else "Unknown"
        stats['top_municipality_count'] = top_municipalities.iloc[0] if len(top_municipalities) > 0 else 0
        stats['municipalities_count'] = map_df['MUNICIPIO'].nunique()
    
    # Property type stats if available
    if 'TIPO' in map_df.columns:
        top_types = map_df['TIPO'].value_counts().head(3)
        stats['top_property_type'] = top_types.index[0] if len(top_types) > 0 else "Unknown"
        stats['top_property_type_count'] = top_types.iloc[0] if len(top_types) > 0 else 0
        stats['property_types_count'] = map_df['TIPO'].nunique()
    
    return stats