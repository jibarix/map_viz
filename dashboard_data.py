#!/usr/bin/env python3
"""
Puerto Rico Property Dashboard - Data Processing (FIXED VERSION)
------------------------------------------------
This file contains the data processing and calculation functions for the dashboard.
"""

import pandas as pd
import numpy as np
import base64
import io
from datetime import datetime

def parse_contents(contents, filename):
    """Parse uploaded file contents"""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        if 'csv' in filename:
            # Read the CSV into a pandas dataframe
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            
            # Clean the data
            df = clean_data(df)
            
            return df, f"Successfully loaded {filename} with {len(df)} rows"
        else:
            return None, "Please upload a CSV file."
    except Exception as e:
        return None, f"Error processing file: {str(e)}"

def clean_data(df):
    """Clean and prepare data for analysis"""
    # Copy the dataframe to avoid modifying the original
    clean_df = df.copy()
    
    # Convert date column if it exists
    if 'SALESDTTM_FORMATTED' in clean_df.columns:
        clean_df['SALESDTTM_FORMATTED'] = pd.to_datetime(clean_df['SALESDTTM_FORMATTED'], errors='coerce')
        clean_df['SALE_YEAR'] = clean_df['SALESDTTM_FORMATTED'].dt.year
        clean_df['SALE_MONTH'] = clean_df['SALESDTTM_FORMATTED'].dt.month
    
    # Clean numeric columns with more robust conversion
    numeric_cols = ['SALESAMT', 'TOTALVAL', 'LAND', 'STRUCTURE', 'MACHINERY', 'DISTANCE_MILES', 'CABIDA', 
                    'INSIDE_X', 'INSIDE_Y', 'DISTANCE_KM', 'Shape.STArea()', 'Shape.STLength()']
    
    for col in numeric_cols:
        if col in clean_df.columns:
            # Convert column to string first to handle any unexpected formats
            clean_df[col] = clean_df[col].astype(str).str.replace(',', '')
            # Then convert to numeric
            clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce')
    
    # Add a flag for valid sales (non-symbolic transactions)
    # Use a more lenient approach to defining valid sales
    if 'SALESAMT' in clean_df.columns:
        clean_df['VALID_SALE'] = clean_df['SALESAMT'] > 5000
    
    # Log summary of available spatial and distance data
    coord_count = clean_df.dropna(subset=['INSIDE_X', 'INSIDE_Y']).shape[0]
    distance_count = clean_df.dropna(subset=['DISTANCE_MILES']).shape[0] if 'DISTANCE_MILES' in clean_df.columns else 0
    print(f"Records with valid coordinates: {coord_count} of {len(clean_df)}")
    print(f"Records with valid distance: {distance_count} of {len(clean_df)}")
    
    return clean_df

def calculate_summary_stats(df):
    """Calculate summary statistics for the dashboard"""
    stats = {}
    
    # Basic counts
    stats['total_properties'] = len(df)
    stats['properties_with_sales'] = len(df[df['SALESAMT'] > 0]) if 'SALESAMT' in df.columns else 0
    stats['valid_sales'] = len(df[df['VALID_SALE']]) if 'VALID_SALE' in df.columns else 0
    
    # Price statistics
    if 'SALESAMT' in df.columns and stats['valid_sales'] > 0:
        valid_sales = df[df['VALID_SALE']]['SALESAMT']
        stats['avg_price'] = valid_sales.mean()
        stats['median_price'] = valid_sales.median()
        stats['min_price'] = valid_sales.min()
        stats['max_price'] = valid_sales.max()
    else:
        stats['avg_price'] = stats['median_price'] = stats['min_price'] = stats['max_price'] = 0
    
    # Property values
    stats['avg_property_value'] = df['TOTALVAL'].mean() if 'TOTALVAL' in df.columns else 0
    
    # Area statistics
    if 'CABIDA' in df.columns and len(df[df['CABIDA'] > 0]) > 0:
        valid_area = df[df['CABIDA'] > 0]['CABIDA']
        stats['avg_area_sqm'] = valid_area.mean()
        stats['median_area_sqm'] = valid_area.median()
        
        # Convert to square feet
        stats['avg_area_sqft'] = stats['avg_area_sqm'] * 10.764
        stats['median_area_sqft'] = stats['median_area_sqm'] * 10.764
        
        # Calculate price per square foot if we have sales data
        if 'SALESAMT' in df.columns and stats['valid_sales'] > 0:
            # Get valid sales with valid area
            valid_sales_area = df[(df['VALID_SALE']) & (df['CABIDA'] > 0)]
            if len(valid_sales_area) > 0:
                valid_sales_area['area_sqft'] = valid_sales_area['CABIDA'] * 10.764
                valid_sales_area['price_per_sqft'] = valid_sales_area['SALESAMT'] / valid_sales_area['area_sqft']
                
                stats['avg_price_per_sqft'] = valid_sales_area['price_per_sqft'].mean()
                stats['median_price_per_sqft'] = valid_sales_area['price_per_sqft'].median()
                stats['properties_with_price_per_sqft'] = len(valid_sales_area)
    
    # Date range
    if 'SALESDTTM_FORMATTED' in df.columns:
        import pandas as pd
        date_values = df['SALESDTTM_FORMATTED'].dropna()
        if not date_values.empty:
            # Convert to datetime if not already
            try:
                # Check if we're dealing with strings that need conversion
                if isinstance(date_values.iloc[0], str):
                    date_values = pd.to_datetime(date_values, errors='coerce')
                
                min_date = date_values.min()
                max_date = date_values.max()
                
                # Format the dates using string formatting without strftime
                if isinstance(min_date, pd.Timestamp):
                    min_date_str = min_date.strftime('%Y-%m-%d')
                    max_date_str = max_date.strftime('%Y-%m-%d')
                else:
                    # Handle string dates if conversion didn't work
                    min_date_str = str(min_date)
                    max_date_str = str(max_date)
                
                stats['date_range'] = f"{min_date_str} to {max_date_str}"
            except Exception as e:
                print(f"Error formatting dates: {e}")
                stats['date_range'] = "Error formatting date range"
        else:
            stats['date_range'] = "No date data available"
    else:
        stats['date_range'] = "No date data available"
    
    # Municipality information
    if 'MUNICIPIO' in df.columns:
        municipalities = df['MUNICIPIO'].value_counts()
        stats['main_municipality'] = municipalities.index[0] if not municipalities.empty else "Unknown"
        stats['main_municipality_count'] = municipalities.iloc[0] if not municipalities.empty else 0
    else:
        stats['main_municipality'] = "Unknown"
        stats['main_municipality_count'] = 0
    
    # Add information about available data for spatial and distance analysis
    stats['has_spatial_data'] = ('INSIDE_X' in df.columns and 'INSIDE_Y' in df.columns)
    stats['spatial_data_count'] = df.dropna(subset=['INSIDE_X', 'INSIDE_Y']).shape[0] if stats['has_spatial_data'] else 0
    stats['has_distance_data'] = 'DISTANCE_MILES' in df.columns
    stats['distance_data_count'] = df.dropna(subset=['DISTANCE_MILES']).shape[0] if stats['has_distance_data'] else 0
    stats['has_area_data'] = 'CABIDA' in df.columns
    stats['area_data_count'] = df.dropna(subset=['CABIDA']).shape[0] if stats['has_area_data'] else 0
    
    return stats

def calculate_yearly_stats(df):
    """Calculate yearly statistics for price trends"""
    # Check if we have the necessary data
    if 'SALESDTTM_FORMATTED' not in df.columns or 'SALESAMT' not in df.columns:
        return None
    
    # Ensure we have year data
    if 'SALE_YEAR' not in df.columns:
        df['SALE_YEAR'] = pd.to_datetime(df['SALESDTTM_FORMATTED'], errors='coerce').dt.year
    
    # Group by year
    yearly_stats = df[df['VALID_SALE']].groupby('SALE_YEAR').agg({
        'SALESAMT': ['count', 'mean', 'median', 'min', 'max']
    }).reset_index()
    
    # Flatten the column names
    yearly_stats.columns = [
        'Year', 'Sales_Count', 'Avg_Price', 'Median_Price', 'Min_Price', 'Max_Price'
    ]
    
    # Filter to years with enough data
    recent_years = yearly_stats[yearly_stats['Sales_Count'] >= 1].copy()
    
    return recent_years

def calculate_property_type_stats(df):
    """Calculate statistics by property type"""
    if 'TIPO' not in df.columns or 'SALESAMT' not in df.columns:
        return None
    
    # Group by property type
    type_stats = df[df['VALID_SALE']].groupby('TIPO').agg({
        'SALESAMT': ['count', 'mean', 'median'],
        'TOTALVAL': ['mean', 'median']
    }).reset_index()
    
    # Flatten columns
    type_stats.columns = [
        'Property_Type', 'Sales_Count', 'Avg_Sale_Price', 'Median_Sale_Price', 
        'Avg_Value', 'Median_Value'
    ]
    
    return type_stats

def calculate_property_components(df):
    """Calculate average values of property components"""
    if not all(col in df.columns for col in ['LAND', 'STRUCTURE', 'MACHINERY']):
        return None
    
    # Calculate averages
    avg_land = df['LAND'].mean()
    avg_structure = df['STRUCTURE'].mean()
    avg_machinery = df['MACHINERY'].mean()
    
    # Create data for chart
    components_data = pd.DataFrame({
        'Component': ['Land', 'Structure', 'Machinery'],
        'Value': [avg_land, avg_structure, avg_machinery]
    })
    
    return components_data

def prepare_price_distribution_data(df, max_price=2000000):
    """Prepare data for price distribution histogram"""
    if 'SALESAMT' not in df.columns or 'VALID_SALE' not in df.columns:
        return None
    
    # Filter for valid sales and cap at specified max price
    sales_df = df[(df['VALID_SALE']) & (df['SALESAMT'] <= max_price)].copy()
    
    return sales_df if len(sales_df) > 0 else None

def prepare_spatial_data(df):
    """Prepare data for spatial analysis - FIXED VERSION"""
    # Check if we have coordinate data
    if 'INSIDE_X' not in df.columns or 'INSIDE_Y' not in df.columns:
        print("Missing coordinate columns: INSIDE_X or INSIDE_Y")
        return None
    
    # Create a copy to avoid modifying the original
    geo_df = df.copy()
    
    # Ensure the coordinates are numeric
    for col in ['INSIDE_X', 'INSIDE_Y']:
        geo_df[col] = pd.to_numeric(geo_df[col], errors='coerce')
    
    # Filter out rows with missing or invalid coordinates
    # Also check for extreme outliers or zero values which might indicate bad data
    geo_df = geo_df[(geo_df['INSIDE_X'].notna()) & 
                    (geo_df['INSIDE_Y'].notna()) & 
                    (geo_df['INSIDE_X'] != 0) & 
                    (geo_df['INSIDE_Y'] != 0)]
    
    print(f"Records with valid coordinates after cleaning: {len(geo_df)} of {len(df)}")
    
    # If no valid coordinates, return None
    if len(geo_df) == 0:
        print("No valid coordinate data after filtering")
        return None
    
    # Create price brackets if we have price data
    if 'SALESAMT' in geo_df.columns and 'VALID_SALE' in geo_df.columns:
        valid_price_df = geo_df[geo_df['VALID_SALE']]
        if len(valid_price_df) > 0:
            geo_df.loc[valid_price_df.index, 'price_bracket'] = pd.cut(
                valid_price_df['SALESAMT'],
                bins=[0, 50000, 100000, 200000, 500000, float('inf')],
                labels=['<$50K', '$50K-$100K', '$100K-$200K', '$200K-$500K', '>$500K']
            )
            print(f"Added price brackets for {len(valid_price_df)} records with valid sales")
    
    return geo_df

def calculate_spatial_grid_stats(geo_df):
    """Calculate statistics by spatial grid - FIXED VERSION"""
    # Validate inputs
    if geo_df is None or len(geo_df) == 0:
        print("No geo data available for grid statistics")
        return None
    
    if 'SALESAMT' not in geo_df.columns or 'VALID_SALE' not in geo_df.columns:
        print("Missing sales data for grid statistics")
        return None
    
    # Get only records with valid sales for price statistics
    price_df = geo_df[geo_df['VALID_SALE']].copy()
    
    # Check if we have enough data
    if len(price_df) < 5:
        print(f"Not enough price data for grid statistics: {len(price_df)} records")
        return None
    
    # Use fewer bins if we don't have much data
    num_bins = 3 if len(price_df) < 25 else 5
    
    try:
        # Create grid cells based on coordinates
        price_df['grid_x'] = pd.qcut(price_df['INSIDE_X'], q=num_bins, duplicates='drop')
        price_df['grid_y'] = pd.qcut(price_df['INSIDE_Y'], q=num_bins, duplicates='drop')
        
        # Group by grid cells
        grid_stats = price_df.groupby(['grid_x', 'grid_y']).agg({
            'CATASTRO': 'count',
            'SALESAMT': ['mean', 'median']
        }).reset_index()
        
        # Flatten columns
        grid_stats.columns = [
            'Longitude_Range', 'Latitude_Range', 'Property_Count', 
            'Avg_Price', 'Median_Price'
        ]
        
        # IMPORTANT FIX: Convert the pandas Interval objects to strings for JSON serialization
        grid_stats['Longitude_Range'] = grid_stats['Longitude_Range'].astype(str)
        grid_stats['Latitude_Range'] = grid_stats['Latitude_Range'].astype(str)
        
        print(f"Created grid statistics with {len(grid_stats)} cells")
        return grid_stats
    
    except Exception as e:
        print(f"Error creating grid statistics: {str(e)}")
        return None

def prepare_distance_data(df):
    """Prepare data for distance vs price analysis - FIXED VERSION"""
    # Check if we have distance and price data
    if 'DISTANCE_MILES' not in df.columns:
        print("Missing DISTANCE_MILES column")
        return None
    
    if 'SALESAMT' not in df.columns or 'VALID_SALE' not in df.columns:
        print("Missing sales price or valid sale flag")
        return None
    
    # Create a copy to avoid modifying the original
    dist_df = df.copy()
    
    # Ensure distance is numeric
    dist_df['DISTANCE_MILES'] = pd.to_numeric(dist_df['DISTANCE_MILES'], errors='coerce')
    
    # Filter to valid sales with distance data
    dist_df = dist_df[(dist_df['VALID_SALE']) & (dist_df['DISTANCE_MILES'].notna()) & (dist_df['DISTANCE_MILES'] > 0)]
    
    print(f"Records with valid distance and price: {len(dist_df)} of {len(df)}")
    
    return dist_df if len(dist_df) > 0 else None

def calculate_distance_bin_stats(dist_df, num_bins=5):
    """Calculate statistics by distance bins - FIXED VERSION"""
    # Validate inputs
    if dist_df is None or len(dist_df) == 0:
        print("No distance data available for bin statistics")
        return None
    
    # Adjust number of bins based on amount of data
    if len(dist_df) < 10:
        num_bins = 2
    elif len(dist_df) < 30:
        num_bins = 3
    
    try:
        # Create distance bins using qcut
        dist_df['distance_bin'] = pd.qcut(
            dist_df['DISTANCE_MILES'],
            q=num_bins,
            duplicates='drop'
        )
        
        # Group by distance bins
        bin_stats = dist_df.groupby('distance_bin').agg({
            'SALESAMT': ['count', 'mean', 'median'],
            'DISTANCE_MILES': 'mean'
        }).reset_index()
        
        # Flatten columns
        bin_stats.columns = [
            'Distance_Range', 'Property_Count', 'Avg_Price', 'Median_Price', 'Avg_Distance'
        ]
        
        # IMPORTANT FIX: Convert the pandas Interval objects to strings for JSON serialization
        bin_stats['Distance_Range'] = bin_stats['Distance_Range'].astype(str)
        
        print(f"Created distance bin statistics with {len(bin_stats)} bins")
        return bin_stats
    
    except Exception as e:
        print(f"Error creating distance bin statistics: {str(e)}")
        return None

def calculate_distance_stats(dist_df):
    """Calculate detailed statistics by rounded distance - FIXED VERSION"""
    # Validate inputs
    if dist_df is None or len(dist_df) == 0:
        print("No distance data available for detailed statistics")
        return None
    
    try:
        # Use a more appropriate rounding based on the data range
        max_distance = dist_df['DISTANCE_MILES'].max()
        round_precision = 1
        
        if max_distance > 50:
            round_precision = 5
        elif max_distance > 20:
            round_precision = 2
        
        # Group by rounded distance
        dist_df['rounded_distance'] = np.round(dist_df['DISTANCE_MILES'], round_precision)
        
        # Merge small groups to prevent having too many with just 1-2 properties
        value_counts = dist_df['rounded_distance'].value_counts()
        small_values = value_counts[value_counts < 3].index.tolist()
        
        # If we have small groups, adjust the rounding to merge them
        if len(small_values) > len(value_counts) / 3:
            print(f"Too many small groups ({len(small_values)}), adjusting rounding")
            round_precision = round_precision * 2
            dist_df['rounded_distance'] = np.round(dist_df['DISTANCE_MILES'], round_precision)
        
        # Calculate statistics
        distance_stats = dist_df.groupby('rounded_distance').agg({
            'SALESAMT': ['count', 'mean', 'median', 'min', 'max'],
            'DISTANCE_MILES': 'mean'
        }).reset_index()
        
        # Flatten columns
        distance_stats.columns = [
            'Rounded_Distance', 'Property_Count', 'Avg_Price', 'Median_Price', 
            'Min_Price', 'Max_Price', 'Exact_Avg_Distance'
        ]
        
        # Make sure Rounded_Distance is a float or int (not a complex object)
        distance_stats['Rounded_Distance'] = distance_stats['Rounded_Distance'].astype(float)
        
        print(f"Created detailed distance statistics with {len(distance_stats)} distance points")
        return distance_stats
    
    except Exception as e:
        print(f"Error creating detailed distance statistics: {str(e)}")
        return None

def prepare_monthly_price_per_sqft_data(df):
    """
    Prepare monthly price per square foot data for visualization
    
    Args:
        df: Pandas DataFrame containing property data
        
    Returns:
        Pandas DataFrame with monthly price/sqft data or None if not enough data
    """
    # Check if we have the necessary data
    if not all(col in df.columns for col in ['SALESDTTM_FORMATTED', 'SALESAMT', 'CABIDA']):
        print("Missing required columns for monthly price per sqft analysis")
        return None
    
    # Create a working copy
    monthly_df = df.copy()
    
    # Ensure date is in datetime format
    monthly_df['SALESDTTM_FORMATTED'] = pd.to_datetime(monthly_df['SALESDTTM_FORMATTED'], errors='coerce')
    
    # Filter for valid sales with area data
    monthly_df = monthly_df[
        (monthly_df['VALID_SALE']) & 
        (monthly_df['CABIDA'] > 0) & 
        (monthly_df['SALESDTTM_FORMATTED'].notna())
    ].copy()
    
    if len(monthly_df) < 3:
        print("Not enough data points for monthly price per sqft analysis")
        return None
    
    # Calculate area in square feet and price per square foot
    monthly_df['area_sqft'] = monthly_df['CABIDA'] * 10.764
    monthly_df['price_per_sqft'] = monthly_df['SALESAMT'] / monthly_df['area_sqft']
    
    # Remove extreme outliers in price per sqft (beyond 1st and 99th percentiles)
    q1 = monthly_df['price_per_sqft'].quantile(0.01)
    q3 = monthly_df['price_per_sqft'].quantile(0.99)
    monthly_df = monthly_df[(monthly_df['price_per_sqft'] >= q1) & (monthly_df['price_per_sqft'] <= q3)]
    
    # Extract year-month
    monthly_df['year_month'] = monthly_df['SALESDTTM_FORMATTED'].dt.to_period('M')
    
    # Group by year-month and calculate statistics
    monthly_stats = monthly_df.groupby('year_month').agg({
        'price_per_sqft': ['mean', 'median', 'count'],
        'SALESAMT': ['mean', 'count']
    }).reset_index()
    
    # Flatten the column names
    monthly_stats.columns = [
        'year_month', 'avg_price_per_sqft', 'median_price_per_sqft', 
        'sqft_property_count', 'avg_price', 'sale_count'
    ]
    
    # Convert back to datetime for easier plotting (use the start of each month)
    monthly_stats['month_date'] = monthly_stats['year_month'].dt.to_timestamp()
    
    # Sort by date
    monthly_stats = monthly_stats.sort_values('month_date')
    
    # Keep only months with at least 2 data points for more reliable statistics
    monthly_stats = monthly_stats[monthly_stats['sqft_property_count'] >= 2]
    
    return monthly_stats if len(monthly_stats) >= 2 else None