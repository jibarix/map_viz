# Puerto Rico Property Dashboard

A modular, interactive web dashboard for visualizing and analyzing property data from the Puerto Rico Catastro database.

## Overview

This dashboard allows you to upload CSV files from the PR Property Search Tool and explore the data through various visualizations and analyses. The application has been modularized into three separate components for better maintainability and easier debugging.

## Project Structure

The dashboard is organized into three modular components:

- **app.py** - Server connection and initialization
- **dashboard_ui.py** - UI components, styles, and layout
- **dashboard_data.py** - Data processing and calculation functions

Supporting files:
- **analyze_results.py** - Command-line tool for generating reports (separate from the dashboard)
- **property_analyzer.py** - Reusable analysis functions

## Installation

1. Install the required Python packages:
   ```
   pip install dash plotly pandas numpy statsmodels
   ```

2. Make sure all files are in the same directory.

## Usage

1. Run the dashboard:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:8050/
   ```

3. Use the dashboard interface to:
   - Upload your property search results (CSV file)
   - View summary statistics and charts
   - Explore different analyses through the tabs
   - Interact with the visualizations

## Dashboard Features

### Summary Tab
- Key statistics about your property data
- Property counts, price statistics, and value information
- Price distribution and property type breakdowns

### Price Trends Tab
- Analysis of property prices over time
- Both average and median prices by year
- Transaction volume data
- Yearly statistics table

### Property Values Tab
- Distribution of sale prices
- Property value components breakdown
- Comparison of assessed values to sale prices
- Value statistics by property type

### Spatial Analysis Tab
- Map of property locations
- Color-coding by price range
- Property density heatmap
- Statistics for different geographic areas

### Distance vs Price Tab
- Analysis of how property prices change with distance from center
- Price trends with distance
- Statistics by distance intervals

## Modular Architecture

The dashboard has been designed with a clear separation of concerns:

1. **app.py**: Handles server configuration and application initialization
   - Sets up the Dash server
   - Imports dashboard components
   - Contains error handling for initialization

2. **dashboard_ui.py**: Contains all UI-related code
   - Dashboard layout
   - UI components and styling
   - Callback functions for user interaction
   - Visualization generation

3. **dashboard_data.py**: Contains all data processing logic
   - Data cleaning and preprocessing
   - Statistical calculations
   - Data transformation for visualizations
   - Analysis functions

This modular approach makes it easier to maintain and extend the dashboard. You can modify the UI without affecting the data processing logic, and vice versa.

## Troubleshooting

If you encounter issues with the dashboard:

1. **Check for errors in the console output** - The server will display any errors when starting or processing data.

2. **Try a different port** - If port 8050 is already in use, you can change it in app.py:
   ```python
   app.run_server(debug=True, port=8055)  # Change to a different port
   ```

3. **Check your browser** - Make sure you're using a modern browser with JavaScript enabled.

4. **Data format issues** - The dashboard expects CSV files in the format provided by the PR Property Search Tool. If your data is formatted differently, you may need to adjust it.

## Extending the Dashboard

The modular design makes it easy to extend the dashboard:

1. To add new data processing functionality:
   - Add new functions to dashboard_data.py
   - Keep functions focused on a single responsibility

2. To add new visualizations:
   - Add new UI generation functions to dashboard_ui.py
   - Use the data processing functions from dashboard_data.py

3. To add a new tab:
   - Add a new tab definition in the tabs list in dashboard_ui.py
   - Create a new generator function for the tab content
   - Update the callback to handle the new tab value

## Contributing

Contributions are welcome! Feel free to submit pull requests or open issues for bugs and feature requests.