# Import necessary libraries
from dash import Dash, html, dcc, Input, Output, ctx, callback
import pandas as pd
import geopandas as gpd
import plotly.express as px
import dash_bootstrap_components as dbc

px.set_mapbox_access_token(open(".mapbox_token").read())

# Initialize Dash application
app = Dash(__name__, 
           external_stylesheets=[dbc.themes.BOOTSTRAP])

# Sample data for the choropleth map and bar chart (you can replace this with your actual data)
countries = ["USA", "Canada", "Mexico"]
values = [100, 50, 30]

# Create the choropleth map
fig_map = px.choropleth(
    data_frame={"country": countries, "value": values},
    locations="country",
    color="value",
    locationmode="country names",
    title="Raning in Manila"
)

# Create the stacked bar chart
fig_bar = px.bar(
    data_frame={"country": countries, "value": values},
    x="country",
    y="value",
    title="Stacked Bar Chart"
)

# App layout
app.layout = html.Div([
# Chloropleth Map
    # dcc.Graph(figure=fig_map, style={"width": "70%", "display": "inline-block"}),

# Stacked bar chart
    # dcc.Graph(figure=fig_bar, style={"width": "30%", "display": "inline-block"}),

# Year slider
    html.Div([
        dcc.Slider(
            id="year-slider",
            min=2000,
            max=2030,
            value=2020,
            marks={str(year): str(year) for year in range(2000, 2031)},
            step=None
        )
    ], style={"width": "70%", "padding-top": "20px"})
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)