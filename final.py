from dash import Dash, html, dcc, Input, Output
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

# Set your Mapbox access token here
px.set_mapbox_access_token(open(".mapbox_token").read())

# Load the data and perform necessary operations
df_GHG_per_gas = pd.read_excel('GHGperGas_Cleaned.xlsx', sheet_name='Panel Total ghg')
df_GHG_diff = pd.read_excel('GHGperGas_Cleaned.xlsx', sheet_name='Difference not panel')
print("Succesfully loaded data")

# Replace 'Entity' with 'ADMIN' in the GHGtrend DataFrame
GHGtrend = df_GHG_per_gas.groupby(['Year', 'ADMIN'])['Total GHG emitted'].sum().reset_index()
print("Succesfully loaded GHGtrend")

# Sorting the DataFrame by the 'Diff percent' column in ascending order
df_sorted = df_GHG_diff.sort_values(by='Diff percent')
print("Succesfully loaded df_sorted")

# Select the top 5 lowest percent differences
top_5_lowest = df_sorted.nsmallest(5, 'Diff percent')
print("Succesfully loaded top_5_lowest")


# Select the top 5 highest percent differences
top_5_highest = df_sorted.nlargest(5, 'Diff percent')
print("Succesfully loaded top_5_highest")

# Concatenate the two DataFrames to get the final result with only the top 5 highest and top 5 lowest percent differences
df_5lowhigh = pd.concat([top_5_lowest, top_5_highest])
print("Succesfully concatenated low and high")

# Reshape the panel data to a tidy format
df_GHG_per_gas_tidy = df_GHG_per_gas.pivot_table(index='ADM0_A3', columns='Year', values='Total GHG emitted').reset_index()
print("Succesfully pivoted gas_tidy")

# Load geospatial data
zaworld = gpd.read_file('/Users/alfonsoreyes/Documents/Projects/DATA101 Project/datasetss')
print("Succesfully loaded zaworld")

# Merge GHG data with geospatial data
merged_df = zaworld.merge(df_GHG_per_gas_tidy, on='ADM0_A3', how='left')
print("Succesfully merged the two")

# Convert to geojson format
geojson = merged_df.geometry.__geo_interface__
print("Succesfully converted df to geojson")

# Initialize Dash application
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

print("Succesfully initialized dash")

# Create the choropleth map function
def create_choropleth_map(selected_year):
    fig = px.choropleth_mapbox(
    merged_df,
    geojson=geojson,  # Use the valid GeoJSON format
    locations=merged_df.index,  # Use the index as identifier
    color=selected_year,
    hover_name='ADMIN',
    mapbox_style="carto-positron",
    zoom=1,
    center={"lat": 37.0902, "lon": -95.7129}
)
    fig.update_layout(title=f"Choropleth Map of Total GHG Emissions per Country in {selected_year}")
    return fig

# Create the stacked bar chart function
def create_stacked_bar_chart(selected_country):
    # Filter data for the specific country
    country_data = df_GHG_per_gas[df_GHG_per_gas["ADMIN"] == selected_country]

    # Melt the DataFrame to the long format for a stacked bar chart
    country_data_melted = country_data.melt(
        id_vars=["Year", "ADMIN"],
        value_vars=[
            "Annual CO2 emissions",
            "Annual nitrous oxide emissions in CO2 equivalents",
            "Annual methane emissions in CO2 equivalents",
        ],
        var_name="Gas types",
        value_name="Emissions",
    )

    # Create the stacked bar chart using Plotly
    fig = px.bar(
        country_data_melted,
        x="Year",
        y="Emissions",
        color="Gas types",
        title=f"GHG Emissions for {selected_country} (1970-2021)",
        labels={"Year": "Year", "Emissions": "Emissions"},
        barmode="stack",
    )
    fig.update_layout(
        # margin=dict(l=20, r=20, t=80, b=20),
        paper_bgcolor="White",
    )
    fig.update_layout(
        width=int(750),
        legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="right", x=1),
    )

    return fig

# Create the diverging bar chart function
def create_diverging_bar_chart():
    # Assuming you have already created df_5lowhigh DataFrame and it contains the data for the top 5 lowest and highest emitters
    positive_diff_df = df_5lowhigh[df_5lowhigh["Diff percent"] >= 0]
    negative_diff_df = df_5lowhigh[df_5lowhigh["Diff percent"] < 0]

    # Sort the DataFrames for the bar chart
    positive_diff_df = positive_diff_df.sort_values(by='Diff percent', ascending=False)
    negative_diff_df = negative_diff_df.sort_values(by='Diff percent', ascending=True)

    # Create a figure
    fig = go.Figure()

    # Add the bars for positive percent differences
    fig.add_trace(go.Bar(
        x=positive_diff_df["Diff percent"],
        y=positive_diff_df["ADMIN"],
        orientation='h',
        marker=dict(color='red'),  # Set color for positive differences
        name='Positive Percent Difference'
    ))

    # Add the bars for negative percent differences
    fig.add_trace(go.Bar(
        x=negative_diff_df["Diff percent"],
        y=negative_diff_df["ADMIN"],
        orientation='h',
        marker=dict(color='green'),  # Set color for negative differences
        name='Negative Percent Difference'
    ))

    # Update the layout to display as a diverging bar chart
    fig.update_layout(
        title='Diverging Bar Chart of the top 5 countries with the highest negative and positive changes in emissions since 2015',
        xaxis=dict(
            tickformat="%", # Format x-axis tick labels as percentages
            range=[-2, 2],  # Set the range of the x-axis from -100% to 100%
            dtick=1,        # Set the interval between tick marks
        ),
        yaxis=dict(
            automargin=True,  # Automatically adjust margin to fit the labels
        ),
        barmode='overlay',  # Use 'overlay' to overlay positive and negative bars
        bargap=0.2,         # Adjust the gap between bars
        bargroupgap=0.1,    # Adjust the gap between bar groups
    )

    return fig

line_fig = px.line(
                GHGtrend,
                x="Year",
                y="Total GHG emitted",
                color="ADMIN",
                title="Trend of Total GHG Emitted per Country",
                markers=True,
                category_orders={
                    "ADMIN": GHGtrend.groupby("ADMIN")["Total GHG emitted"]
                    .sum()
                    .sort_values(ascending=False)
                    .index
                },
            )

print("Succesfully loaded all functions")

# App layout
app.layout = html.Div(style={'font-family': 'Nirmala UI, Proxima Nova, sans-serif', 'margin': '1in', 'color': '#FFDEAD', 'background-color': '#e9f1f4', 'justify-content': 'center', 'text-align': 'justify',}, children=[
     html.Div(style={'font-family': 'Nirmala UI, Proxima Nova, sans-serif', 'color': '#FFDEAD', 'background-color': '#cfe0e7', 'justify-content': 'center', 'text-align': 'justify',}, children=[
    html.H1("Visualizing the Fight Against Climate Change", style={'color': '#555', 'margin-bottom': '0.12in', 'text-align': 'center', 'padding': '10px'}),]),
    html.H5("Cudo, Hernandez, Lamberte, Reyes", style={'color': '#555', 'margin-bottom': '0.12in', 'font-style': 'italic', 'justify-content': 'center', 'padding': '10px'}),
    html.P("Climate change is a pressing global issue we're facing, and it is impacting various parts of our lives. Shifts in growing seasons and water availability now make it harder for farmers to produce food. Coastal communities face threats from rising sea levels, leading to flooding and livelihood disruptions. Our warming and more acidic oceans harm marine life, biodiversity, and ecosystem stability. Climate change has now also worsened air quality and exacerbated heat-related illnesses, affecting public health. Combatting climate change is crucial for it affects everyone, and its effects are felt even more by vulnerable  communities.", style={'color': '#555', 'margin-bottom': '0.12in', 'padding': '15px'}),
    html.P("Greenhouse gases (GHGs) are the primary driver of climate change. When we burn fossil fuels, deforest land, and engage in certain industrial activities, we release significant amounts of greenhouse gases into the atmosphere. These gases act like a blanket, trapping heat and causing the Earth's temperature to rise, leading to global warming. This warming, in turn, triggers various consequences such as ones mentioned above.", style={'color': '#555', 'margin-bottom': '0.12in', 'padding': '15px'}),
    html.P([
        "To address climate change's impacts by curbing GHG emissions",
        html.Span(" we must first track and understand the general trend for global GHG emissions over the years.", style={'color': '#fd9372', 'margin-bottom': '0.12in', 'font-weight': 'bold'})
    ], style={'color': '#555', 'margin-bottom': '0.12in', 'justify-content': 'center', 'padding': '15px'} ),

    html.Div(style={'font-family': 'Nirmala UI, Proxima Nova, sans-serif', 'color': '#FFDEAD', 'background-color': '#cfe0e7', 'justify-content': 'center', 'text-align': 'justify',}, children=[
    html.H1("Line Chart as a whole", style={'color': '#555', 'margin-bottom': '0.12in', 'text-align': 'center', 'padding': '10px'}),]),
     dcc.Graph(id='line-chartall', figure=px.line(GHGtrend, x="Year", y="Total GHG emitted",
                                              color="ADMIN",
                                              title="Trend of Total GHG Emitted per Country",
                                              markers=True,
                                              category_orders={
                                                  "ADMIN": GHGtrend.groupby("ADMIN")["Total GHG emitted"].sum().sort_values(ascending=False).index}
                                              )
               ),

    html.P("It is hard to visualize the trend of GHG per country across the years so below is a line chart which can be filtired out! Play around with it for a bit.", style={'color': '#555', 'margin-bottom': '0.12in', 'justify-content': 'center', 'padding': '15px'}),
    html.Div(style={'font-family': 'Nirmala UI, Proxima Nova, sans-serif', 'color': '#FFDEAD', 'background-color': '#cfe0e7', 'justify-content': 'center', 'text-align': 'justify',}, children=[
    html.H1("Line Chart with options", style={'color': '#555', 'margin-bottom': '0.12in', 'text-align': 'center', 'padding': '10px'}),]),
    # Line Chart from the first code
    dcc.Dropdown(
        id='country-dropdown',
        options=[{'label': country, 'value': country} for country in GHGtrend['ADMIN'].unique()],
        multi=True,
        placeholder="Select countries...",
        style={'width': '50%','color': 'black', 'padding': '10px'}
    ),
    dcc.Graph(id='line-chart'),


     html.P("This line chart showcases the trends of GHG emissions on a global scale over several decades. The x-axis indicates the years or time periods studied, while the y-axis represents emission levels.", style={'color': '#555', 'margin-bottom': '0.12in', 'padding': '15px'}),
     html.P([
        "On December 12, 2015, during COP21, The Paris Agreement was adopted. The Paris Agreement is a landmark international accord ratified by 196 countries and the EU, which specifically strives to limit the rise in global temperature below 2 degrees Celsius, with an aspirational target of only 1.5 degrees Celsius above pre-industrial levels through coordinated efforts to reduce GHG emissions. ", 
        html.Span("This agreement represents a critical step in the fight against climate change.", style={'color': '#fd9372', 'font-weight': 'bold'})
    ], style={'color': '#555', 'margin-bottom': '0.12in', 'justify-content': 'center', 'padding': '15px'}),
      html.P("This line chart clearly illustrates a general upward trajectory in GHG emissions projected for the upcoming years. This pronounced increase can be attributed to heightened investments, the effects of globalization, and the dynamics of international trade, as highlighted by Ahmed et al. (2022). However, the comprehensive policies outlined by the 2015 Paris Agreement have ushered nations towards a shared objective: to curtail the escalation of global temperature by maintaining a rise of less than 1.5°C.", style={'color': '#555', 'margin-bottom': '0.12in', 'padding': '10px'}),
      html.P([
        "Achieving this crucial aim demands a significant reduction in the volume of greenhouse gas emissions produced by each country. Therefore, in the aftermath of 2015, we should anticipate witnessing a discernible shift among certain nations, marked by a substantial decrease in their emissions output. A desirable outcome would involve a greater number of countries achieving negative growth in their GHG emissions, as opposed to those registering a positive trajectory, or countries with negative growth should have a greater magnitude than those who have positive growth.",
        html.Span(" This would be a testament to the collective efforts aimed at mitigating the surge in global temperatures, aligning with the ultimate goal of the Paris Agreement.", style={'color': '#fd9372', 'font-weight': 'bold'}),
        " To see that, we take at the top 5 largest and top 5 lowest percent changes in total GHG emissions using 2015 as a base year and 2021 as the latest year."
    ], style={'color': '#555', 'margin-bottom': '0.12in', 'justify-content': 'center', 'padding': '15px'}),

       html.Div(style={'font-family': 'Nirmala UI, Proxima Nova, sans-serif', 'color': '#FFDEAD', 'background-color': '#cfe0e7', 'justify-content': 'center', 'text-align': 'justify',}, children=[
    html.H1("Diverging Bar Chart", style={'color': '#555', 'margin-bottom': '0.12in', 'text-align': 'center', 'padding': '10px'}),]),

    # Diverging Bar Chart for top 5 lowest and highest emitters
    dcc.Graph(id='diverging-bar-chart', figure=create_diverging_bar_chart(), style={"width": "100%", "display": "inline-block"}),
    

         html.H1(html.Span("Oh no!", style={'color': '#fd9372', 'font-weight': 'bold', 'justify-content': 'center', 'text-align': 'center', 'padding': '10px'}), style={'text-align': 'center'}),
         html.P(["It seems that the top 5 locations with a positive growth in GHG emissions have a greater magnitude as compared to those that have a negative growth rate. What is even worse is that most of these nations are either developing countries, which normally do not emit a lot of GHG in the first place, or countries that normally don’t have an advanced urban area enough to generate significant amounts of GHG like the ",
         html.Span("Cook Islands!", style={'color': '#fd9372', 'font-weight': 'bold'})], style={'color': '#555', 'margin-bottom': '0.5in', 'justify-content': 'center', 'padding': '15px'} ),

         html.H1(html.Span("However!", style={'color': '#fd9372', 'font-weight': 'bold', 'justify-content': 'center', 'text-align': 'center', 'padding': '15px'}), style={'text-align': 'center'}),
         html.P(["Taking a look at the diverging dataset ", 
         html.Span("may not give out the whole truth", style={'color': '#fd9372', 'font-weight': 'bold'}), 
           " of the situation. After all, it only provides the top 5 biggest rates of change in both the positive and negative directions. Thus, it is important to visualize the GHG emissions of the whole world throughout periods of time (especially in 2015-2021). Thus, the choropleth map below showcases just that. You may be able to look at the GHG emitted per country over time. Colors closer to yellow represent high total GHG emitted and colors closer to purple represent the opposite. Check out the visualization below."], style={'color': '#555', 'justify-content': 'center', 'padding': '15px'}),

         html.Div(style={'font-family': 'Nirmala UI, Proxima Nova, sans-serif', 'color': '#FFDEAD', 'background-color': '#cfe0e7', 'justify-content': 'center', 'text-align': 'justify',}, children=[
    html.H1("The Gas Giants: Choropleth Map", style={'color': '#555', 'margin-bottom': '0.12in', 'text-align': 'center', 'padding': '10px'}),]),
   # Choropleth Map and stacked bar chart from the updated code
        dbc.Row(
            children=[
                dbc.Col(
                    children=[
                        html.Div(
                            dcc.Loading(
                                id="map-loading",
                                type="circle",
                                children=dcc.Graph(
                                    id="choropleth-map",
                                    style={"width": "100%", "display": "inline-block"},
                                ),
                            ),
                            style={
                                "width": "100%",
                                "display": "flex",
                                "justify-content": "center",
                            },
                        )
                    ],
                    width=6,
                ),
                dbc.Col(
                    children=[
                        # Stacked Bar Chart for selected country from the updated code
                        dcc.Loading(
                            id="bar-loading",
                            type="circle",
                            children=dcc.Graph(
                                id="stacked-bar-chart",
                                style={"width": "50%", "display": "inline-block"},
                            ),
                        )
                    ],
                    width=4,
                ),
            ]
        ),
    
    # Slider for selecting the year from the updated code
    dcc.Slider(
        id='year-slider',
        min=df_GHG_per_gas['Year'].min(),
        max=df_GHG_per_gas['Year'].max(),
        value=df_GHG_per_gas['Year'].max(),
        tooltip={"placement": "bottom", "always_visible": True},
        marks=None,
        step=1
    ),

    html.P("You may try clicking on a country from the choropleth map to showcase its decomposition of Green House Gasses in a stacked bar chart below", style={'color': '#fd9372', 'font-weight': 'bold', 'padding': '15px'}),
    html.Div(style={'font-family': 'Nirmala UI, Proxima Nova, sans-serif', 'color': '#FFDEAD', 'background-color': '#cfe0e7', 'justify-content': 'center', 'text-align': 'justify',}, children=[
    html.H1("The Carbon Cartel: Methane, Carbon Dioxide, and Nitrous Oxide", style={'color': '#555', 'margin-bottom': '0.12in', 'text-align': 'center', 'padding': '10px'}),]),
    html.P(["Compared to the line chart, the Choropleth map actually gives a clearer output of which countries are emitting how much GHG. Take note that this is total GHG. This is important because we want to see other countries, ",
           html.Span("especially developed ones", style={'color': '#fd9372', 'font-weight': 'bold'}),
           " because they have a considerable impact on a global scale."], style={'color': '#555', 'margin-bottom': '0.5in', 'padding': '15px'}),
    html.P("Based on the choropleth map, three obvious generalizations can be made: Developed and bigger countries like the USA and Brazil are one of the biggest contributors of GHG (1). Countries that emit the least amount of GHG are usually developing countries (2). The biggest contributor to GHG is China which is not surprising given its heavily industrial economy (3).", style={'color': '#555', 'margin-bottom': '0.5in',  'padding': '15px'}),
    html.P(["It is evident, that as the choropleth map changes over the years, GHG emitted, especially for developed countries, ",
           html.Span("gets larger and larger.", style={'color': '#fd9372', 'font-weight': 'bold'})], style={'color': '#555', 'margin-bottom': '0.5in', 'padding': '15px'}),
    html.P("That is quite concerning, but let's explore the situation further by visualizing the gas decomposition through a stacked bar chart. Various industries and specific circumstances within a country can influence the composition of the greenhouse gases they emit. Hence, understanding this decomposition can be instrumental in making informed policy decisions to effectively reduce their overall greenhouse gas emissions. ", style={'color': '#555', 'margin-bottom': '0.5in', 'padding': '15px'}),
    

   

    html.P("Some countries have different compositions than others. One emits more methane, the other emits more carbon dioxide. It is important to know this because these gasses are emitted by various kinds of factors. Knowing those factors, countries can use them to create policies to efficiently reduce overall GHG emissions.", style={'color': '#555', 'margin-bottom': '0.5in', 'padding': '15px'}),
    html.Div(style={'font-family': 'Nirmala UI, Proxima Nova, sans-serif', 'color': '#FFDEAD', 'background-color': '#cfe0e7', 'justify-content': 'center', 'text-align': 'justify',}, children=[
    html.H1("Were the Paris Agreement goals achieved?", style={'color': '#555', 'margin-bottom': '0.12in', 'text-align': 'center', 'padding': '10px'}),]),
    html.P(["The ultimate end goal of the Paris Agreement was to reduce rising global temperatures under 1.5C. To do that, considerable amounts of effort are placed into reducing GHG emissions. Some countries have already contributed to this, others have yet to kickstart their programs, and others show no signs of reducing their emissions anytime soon. ",
           html.Span("So it is hard to say even with this visualization. However, at the current level and data, it seems that progress is slow.", style={'color': '#fd9372', 'font-weight': 'bold'})], style={'color': '#555', 'margin-bottom': '0.5in', 'padding': '15px'}),

    html.Div(style={'font-family': 'Nirmala UI, Proxima Nova, sans-serif', 'color': '#FFDEAD', 'background-color': '#cfe0e7', 'justify-content': 'center', 'text-align': 'justify',}, children=[
    html.H1("Conclusion", style={'color': '#555', 'margin-bottom': '0.12in', 'text-align': 'center', 'padding': '10px'}),]),
    html.P("Given such a time frame from 2015 to 2021, it cannot be said for certain that the Paris Agreement goals were achieved. Evidence from the visualizations shows that the majority of the countries continue to have rising emissions per year. We can only hope that this trend does not continue in the future.", style={'color': '#555', 'margin-bottom': '0.5in', 'padding': '15px'}),
    html.P([
        "Regardless of this, it is too early to say that the Paris Agreement goals were not reached. Policies ",
        html.Span("take a lot of time to implement, and results are usually delayed or lagged in time.",
                  style={'color': '#fd9372', 'font-weight': 'bold'}),
        " This visualization, however, can just give ",
        html.Span("a clear overview of the current situation with regard to it.",
                  style={'color': '#fd9372', 'font-weight': 'bold'}),
        " In the end, it is up to the policymakers and world leaders to decide to accelerate the reduction of GHG emission initiatives in the future."
    ], style={'color': '#555', 'margin-bottom': '0.5in', 'padding': '15px'}),

    ])

# Callback to update the stacked bar chart based on the selected country from the choropleth map
@app.callback(
    Output('stacked-bar-chart', 'figure'),
    Input('choropleth-map', 'clickData')
)
def update_stacked_bar_chart(click_data):
    if click_data is None:
        # If no country is clicked, show an empty figure
        return px.bar()

    selected_country = click_data['points'][0]['hovertext']
    return create_stacked_bar_chart(selected_country)

# Callback to update the choropleth map based on the selected year from the updated code
@app.callback(
    Output('choropleth-map', 'figure'),
    Input('year-slider', 'value')
)
def update_choropleth_map(selected_year):
    return create_choropleth_map(selected_year)

@app.callback(
    Output('line-chart', 'figure'),
    [Input('country-dropdown', 'value')]
)
def update_line_chart(selected_countries):
    if selected_countries:
        filtered_df = GHGtrend[GHGtrend['ADMIN'].isin(selected_countries)].rename(columns={'ADMIN': 'Countries'})
        fig = px.line(filtered_df, x='Year', y='Total GHG emitted', color='Countries', title="GHG Emission Over Time")
    else:
        fig = go.Figure()
    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)