import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import dash_auth

# Get credentials from Render environment variables
VALID_USERS = {
    os.environ.get("DASH_USERNAME"): os.environ.get("DASH_PASSWORD")
}
  


# Initialize the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
auth = dash_auth.BasicAuth(app, VALID_USERS)
server = app.server
# Load data from Excel file
def load_data():
    # Read the Excel file with multiple sheets
    yearly_df = pd.read_csv('data/annual.csv', dtype={'Insurer':str})
    province_df = pd.read_csv('data/province.csv', dtype={'Insurer':str})
    generic_df = pd.read_csv('data/generic.csv', dtype={'Insurer':str})
    therapy_df = pd.read_csv('data/therapy.csv', dtype={'Insurer':str})
     
    # Calculate derived metrics for all dataframes
    for df in [yearly_df, province_df, generic_df, therapy_df]:
        df['Cost_Per_Claimant'] = df['Cost'] / df['Claimants']
        df['Cost_Per_Volume'] = df['Cost'] / df['Volumes']
        df['Claims_Per_Claimant'] = df['Volumes'] / df['Claimants']
    
    # Get unique insurers
    insurers = sorted(yearly_df['Insurer'].unique().tolist())
    insurers.remove('BOB')  # Remove BOB from the list to handle it separately
   
    # Calculate growth rates for yearly data
    # Group by Insurer and Year, then calculate pct_change within each group
    yearly_growth_rate_df = pd.DataFrame()
    
    for insurer in ['BOB'] + insurers:
        insurer_yearly = yearly_df[yearly_df['Insurer'] == insurer].sort_values('Year')
        
        # Calculate growth rates
        insurer_yearly['Claimants_Growth'] = insurer_yearly['Claimants'].pct_change() * 100
        insurer_yearly['Volumes_Growth'] = insurer_yearly['Volumes'].pct_change() * 100
        insurer_yearly['Cost_Growth'] = insurer_yearly['Cost'].pct_change() * 100
        insurer_yearly['Cost_Per_Claimant_Growth'] = insurer_yearly['Cost_Per_Claimant'].pct_change() * 100
        insurer_yearly['Cost_Per_Volume_Growth'] = insurer_yearly['Cost_Per_Volume'].pct_change() * 100
        insurer_yearly['Claims_Per_Claimant_Growth'] = insurer_yearly['Claims_Per_Claimant'].pct_change() * 100

      
        # Update the original dataframe
        yearly_growth_rate_df = pd.concat([yearly_growth_rate_df,insurer_yearly])
    yearly_df = yearly_growth_rate_df
    
    return yearly_df, province_df, generic_df, therapy_df, insurers

# Load the data
yearly_df, province_df, generic_df, therapy_df, insurers = load_data()
print(yearly_df.columns)

# Define available metrics
metrics = [
    {'label': 'Claimants', 'value': 'Claimants'},
    {'label': 'Volumes', 'value': 'Volumes'},
    {'label': 'Cost', 'value': 'Cost'},
    {'label': 'Cost Per Claimant', 'value': 'Cost_Per_Claimant'},
    {'label': 'Cost Per Volume', 'value': 'Cost_Per_Volume'},
    {'label': 'Claims Per Claimant', 'value': 'Claims_Per_Claimant'}
]

growth_metrics = [
    {'label': 'Claimants Growth', 'value': 'Claimants_Growth'},
    {'label': 'Volumes Growth', 'value': 'Volumes_Growth'},
    {'label': 'Cost Growth', 'value': 'Cost_Growth'},
    {'label': 'Cost Per Claimant Growth', 'value': 'Cost_Per_Claimant_Growth'},
    {'label': 'Cost Per Volume Growth', 'value': 'Cost_Per_Volume_Growth'},
    {'label': 'Claims Per Claimant Growth', 'value': 'Claims_Per_Claimant_Growth'}
]

# App layout
app.layout = html.Div([
    html.H1("Claims Dashboard", style={'textAlign': 'center', 'marginBottom': 30}),
    
    # Main layout with left panel and right content
    html.Div([
        # Left Panel for Insurer Selection
        html.Div([
            html.H3("Data Selection", style={'textAlign': 'center', 'marginBottom': 20}),
            
            # BOB Toggle
            html.Div([
                html.Label("Show Book of Business (BOB) Data:"),
                dcc.RadioItems(
                    id='bob-toggle',
                    options=[
                        {'label': 'Yes', 'value': 'BOB'},
                        {'label': 'No', 'value': 'insurer'}
                    ],
                    value='BOB',
                    labelStyle={'display': 'inline-block', 'marginRight': '10px'}
                )
            ], style={'marginBottom': 20}),
            
            # Insurer Dropdown (only visible when BOB is not selected)
            html.Div([
                html.Label("Select Insurer:"),
                dcc.Dropdown(
                    id='insurer-dropdown',
                    options=[{'label': f"Insurer {insurer}", 'value': insurer} for insurer in insurers],
                    value=insurers[0],
                    disabled=True
                )
            ], style={'marginBottom': 20, 'display': 'block'}),
            
            # Data Source Display
            html.Div([
                html.H4("Current Data Source:", style={'marginBottom': 5}),
                html.Div(id='data-source-display', style={
                    'padding': '10px',
                    'backgroundColor': '#f8f9fa',
                    'border': '1px solid #ddd',
                    'borderRadius': '5px',
                    'fontWeight': 'bold',
                    'textAlign': 'center'
                })
            ])
        ], style={
            'width': '20%',
            'padding': '20px',
            'backgroundColor': '#f8f9fa',
            'border': '1px solid #ddd',
            'borderRadius': '5px',
            'marginRight': '20px',
            'height': 'fit-content',
            'float': 'left'  # Add float left to ensure it stays on the left
        }),
        
        # Right Content with Tabs
        html.Div([
            dcc.Tabs([
                # Tab 1: Annual Trends
                dcc.Tab(label="Annual Trends", children=[
                    html.Div([
                        # Summary cards for latest year metrics
                        html.Div([
                            html.H3("Latest Year Summary", style={'textAlign': 'center', 'marginBottom': 20}),
                            # All metrics in a single container with 3 per row
                            html.Div([
                                # Row 1: Primary metrics
                                html.Div([
                                    # Claimants Card
                                    html.Div([
                                        html.H4("Total Claimants", style={'textAlign': 'center', 'marginBottom': 10}),
                                        html.H2(
                                            id='latest-year-claimants',
                                            children=f"{yearly_df.iloc[-1]['Claimants']:,.0f}",
                                            style={'textAlign': 'center', 'color': '#007BFF'}
                                        ),
                                        html.P(
                                            id='latest-year-claimants-growth',
                                            children=f"({yearly_df.iloc[-1]['Claimants_Growth']:.1f}% from previous year)" 
                                            if not pd.isna(yearly_df.iloc[-1]['Claimants_Growth']) else "",
                                            style={'textAlign': 'center', 'fontSize': '0.9em', 'color': '#666'}
                                        )
                                    ], style={'width': '31%', 'display': 'inline-block', 'border': '1px solid #ddd', 
                                            'borderRadius': '5px', 'padding': '15px', 'margin': '0 1%', 'verticalAlign': 'top'}),
                                    
                                    # Volumes Card
                                    html.Div([
                                        html.H4("Total Volumes", style={'textAlign': 'center', 'marginBottom': 10}),
                                        html.H2(
                                            id='latest-year-volumes',
                                            children=f"{yearly_df.iloc[-1]['Volumes']:,.0f}",
                                            style={'textAlign': 'center', 'color': '#28A745'}
                                        ),
                                        html.P(
                                            id='latest-year-volumes-growth',
                                            children=f"({yearly_df.iloc[-1]['Volumes_Growth']:.1f}% from previous year)"
                                            if not pd.isna(yearly_df.iloc[-1]['Volumes_Growth']) else "",
                                            style={'textAlign': 'center', 'fontSize': '0.9em', 'color': '#666'}
                                        )
                                    ], style={'width': '31%', 'display': 'inline-block', 'border': '1px solid #ddd', 
                                            'borderRadius': '5px', 'padding': '15px', 'margin': '0 1%', 'verticalAlign': 'top'}),
                                    
                                    # Cost Card
                                    html.Div([
                                        html.H4("Total Cost", style={'textAlign': 'center', 'marginBottom': 10}),
                                        html.H2(
                                            id='latest-year-cost',
                                            children=f"${yearly_df.iloc[-1]['Cost']:,.0f}",
                                            style={'textAlign': 'center', 'color': '#DC3545'}
                                        ),
                                        html.P(
                                            id='latest-year-cost-growth',
                                            children=f"({yearly_df.iloc[-1]['Cost_Growth']:.1f}% from previous year)"
                                            if not pd.isna(yearly_df.iloc[-1]['Cost_Growth']) else "",
                                            style={'textAlign': 'center', 'fontSize': '0.9em', 'color': '#666'}
                                        )
                                    ], style={'width': '31%', 'display': 'inline-block', 'border': '1px solid #ddd', 
                                            'borderRadius': '5px', 'padding': '15px', 'margin': '0 1%', 'verticalAlign': 'top'})
                                ], style={'marginBottom': 20, 'textAlign': 'center', 'width': '100%', 'display': 'flex', 'justifyContent': 'center'}),
                                
                                # Row 2: Derived metrics
                                html.Div([
                                    # Cost Per Claimant Card
                                    html.Div([
                                        html.H4("Cost Per Claimant", style={'textAlign': 'center', 'marginBottom': 10}),
                                        html.H2(
                                            id='latest-year-cost-per-claimant',
                                            children=f"${yearly_df.iloc[-1]['Cost_Per_Claimant']:,.2f}",
                                            style={'textAlign': 'center', 'color': '#6610F2'}
                                        ),
                                        html.P(
                                            id='latest-year-cost-per-claimant-growth',
                                            children=f"({yearly_df.iloc[-1]['Cost_Per_Claimant_Growth']:.1f}% from previous year)"
                                            if not pd.isna(yearly_df.iloc[-1]['Cost_Per_Claimant_Growth']) else "",
                                            style={'textAlign': 'center', 'fontSize': '0.9em', 'color': '#666'}
                                        )
                                    ], style={'width': '31%', 'display': 'inline-block', 'border': '1px solid #ddd', 
                                            'borderRadius': '5px', 'padding': '15px', 'margin': '0 1%', 'verticalAlign': 'top'}),
                                    
                                    # Cost Per Volume Card
                                    html.Div([
                                        html.H4("Cost Per Volume", style={'textAlign': 'center', 'marginBottom': 10}),
                                        html.H2(
                                            id='latest-year-cost-per-volume',
                                            children=f"${yearly_df.iloc[-1]['Cost_Per_Volume']:,.2f}",
                                            style={'textAlign': 'center', 'color': '#FD7E14'}
                                        ),
                                        html.P(
                                            id='latest-year-cost-per-volume-growth',
                                            children=f"({yearly_df.iloc[-1]['Cost_Per_Volume_Growth']:.1f}% from previous year)"
                                            if not pd.isna(yearly_df.iloc[-1]['Cost_Per_Volume_Growth']) else "",
                                            style={'textAlign': 'center', 'fontSize': '0.9em', 'color': '#666'}
                                        )
                                    ], style={'width': '31%', 'display': 'inline-block', 'border': '1px solid #ddd', 
                                            'borderRadius': '5px', 'padding': '15px', 'margin': '0 1%', 'verticalAlign': 'top'}),
                                    
                                    # Claims Per Claimant Card
                                    html.Div([
                                        html.H4("Claims Per Claimant", style={'textAlign': 'center', 'marginBottom': 10}),
                                        html.H2(
                                            id='latest-year-claims-per-claimant',
                                            children=f"{yearly_df.iloc[-1]['Claims_Per_Claimant']:,.2f}",
                                            style={'textAlign': 'center', 'color': '#20C997'}
                                        ),
                                        html.P(
                                            id='latest-year-claims-per-claimant-growth',
                                            children=f"({yearly_df.iloc[-1]['Claims_Per_Claimant_Growth']:.1f}% from previous year)"
                                            if not pd.isna(yearly_df.iloc[-1]['Claims_Per_Claimant_Growth']) else "",
                                            style={'textAlign': 'center', 'fontSize': '0.9em', 'color': '#666'}
                                        )
                                    ], style={'width': '31%', 'display': 'inline-block', 'border': '1px solid #ddd', 
                                            'borderRadius': '5px', 'padding': '15px', 'margin': '0 1%', 'verticalAlign': 'top'})
                                ], style={'marginBottom': 30, 'textAlign': 'center', 'width': '100%', 'display': 'flex', 'justifyContent': 'center'})
                            ]),
                        ]),
                        
                        html.H3("Annual Trends", style={'textAlign': 'center'}),
                        html.Div([
                            html.Label("Select Metrics:"),
                            dcc.Dropdown(
                                id='annual-metrics-dropdown',
                                options=metrics,
                                value=['Claimants', 'Volumes', 'Cost'],
                                multi=True
                            )
                        ], style={'width': '50%', 'margin': 'auto', 'marginBottom': 20}),
                        dcc.Graph(id='annual-trends-graph'),
                        
                        html.H3("Annual Growth Rates", style={'textAlign': 'center', 'marginTop': 40}),
                        html.Div([
                            html.Label("Select Growth Metrics:"),
                            dcc.Dropdown(
                                id='growth-metrics-dropdown',
                                options=growth_metrics,
                                value=['Claimants_Growth', 'Volumes_Growth', 'Cost_Growth'],
                                multi=True
                            )
                        ], style={'width': '50%', 'margin': 'auto', 'marginBottom': 20}),
                        dcc.Graph(id='growth-rates-graph')
                    ])
                ]),
                
                # Tab 2: Generic Name Analysis
                dcc.Tab(label="Generic Name Analysis", children=[
                    html.Div([
                        html.H3("Generic Name Analysis", style={'textAlign': 'center'}),
                        
                        # Selection controls
                        html.Div([
                            html.Div([
                                html.Label("Select Year:"),
                                dcc.Dropdown(
                                    id='generic-year-dropdown',
                                    options=[{'label': str(year), 'value': year} for year in yearly_df['Year'].unique()],
                                    value=yearly_df['Year'].max()
                                )
                            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '5%'}),
                            html.Div([
                                html.Label("Compare with Years:"),
                                dcc.Dropdown(
                                    id='generic-compare-years-dropdown',
                                    options=[{'label': str(year), 'value': year} for year in yearly_df['Year'].unique()],
                                    value=[],
                                    multi=True
                                )
                            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '5%'}),
                            html.Div([
                                html.Label("Select Metric:"),
                                dcc.Dropdown(
                                    id='generic-metric-dropdown',
                                    options=metrics,
                                    value='Cost'
                                )
                            ], style={'width': '30%', 'display': 'inline-block'})
                        ], style={'marginBottom': 20}),
                        
                        # Top 10 Generic Names Graph
                        html.Div([
                            html.H4("Top 10 Generic Names by Cost", style={'textAlign': 'center', 'marginBottom': 20}),
                            dcc.Graph(id='generic-bar-graph')
                        ], style={'width': '100%', 'marginBottom': 30}),
                        
                        # Generic Name Table with filtering
                        html.Div([
                            html.H4("Generic Name Data Table", style={'textAlign': 'center', 'marginBottom': 10}),
                            html.P("Filter the table to select specific generic names for analysis.", 
                                style={'textAlign': 'center', 'marginBottom': 15}),
                            dash_table.DataTable(
                                id='generic-table',
                                columns=[
                                    {"name": "Generic Name", "id": "Generic_Name"},
                                    {"name": "Claimants", "id": "Claimants", "type": "numeric", "format": {"specifier": ","}},
                                    {"name": "Volumes", "id": "Volumes", "type": "numeric", "format": {"specifier": ","}},
                                    {"name": "Cost ($)", "id": "Cost", "type": "numeric", "format": {"specifier": "$,.2f"}},
                                    {"name": "Cost Per Claimant ($)", "id": "Cost_Per_Claimant", "type": "numeric", "format": {"specifier": "$,.2f"}},
                                    {"name": "Cost Per Volume ($)", "id": "Cost_Per_Volume", "type": "numeric", "format": {"specifier": "$,.2f"}},
                                    {"name": "Claims Per Claimant", "id": "Claims_Per_Claimant", "type": "numeric", "format": {"specifier": ",.2f"}}
                                ],
                                data=[], # Will be populated by callback
                                filter_action="native",
                                sort_action="native",
                                sort_mode="multi",
                                page_size=10,
                                style_table={'overflowX': 'auto'},
                                style_cell={
                                    'textAlign': 'right',
                                    'padding': '8px',
                                    'minWidth': '100px'
                                },
                                style_header={
                                    'backgroundColor': 'rgb(230, 230, 230)',
                                    'fontWeight': 'bold',
                                    'textAlign': 'center'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'column_id': 'Generic_Name'},
                                        'textAlign': 'left'
                                    }
                                ]
                            )
                        ], style={'width': '100%', 'marginTop': 30})
                    ])
                ]),
                
                # Tab 3: Provincial Analysis
                dcc.Tab(label="Provincial Analysis", children=[
                    html.Div([
                        html.H3("Provincial Analysis", style={'textAlign': 'center'}),
                        html.Div([
                            html.Div([
                                html.Label("Select Year:"),
                                dcc.Dropdown(
                                    id='province-year-dropdown',
                                    options=[{'label': str(year), 'value': year} for year in yearly_df['Year'].unique()],
                                    value=yearly_df['Year'].max()
                                )
                            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '5%'}),
                            html.Div([
                                html.Label("Select Metric:"),
                                dcc.Dropdown(
                                    id='province-metric-dropdown',
                                    options=metrics,
                                    value='Cost'
                                )
                            ], style={'width': '30%', 'display': 'inline-block'})
                        ], style={'marginBottom': 20}),
                        dcc.Graph(id='province-bar-graph'),
                        
                        # Top provinces trend chart
                        html.H3("Top Provinces Trend", style={'textAlign': 'center', 'marginTop': 20}),
                        html.P("Showing trend of the selected metric for the top 5 provinces", 
                            style={'textAlign': 'center', 'marginBottom': 15}),
                        dcc.Graph(id='top-provinces-trend-graph'),
                        
                        # Annual trend by province section
                        html.H3("Annual Trend by Province", style={'textAlign': 'center', 'marginTop': 40}),
                        html.Div([
                            html.Div([
                                html.Label("Select Province:"),
                                dcc.Dropdown(
                                    id='province-trend-dropdown',
                                    options=[{'label': province, 'value': province} for province in province_df['Province'].unique()],
                                    value=province_df['Province'].iloc[0]
                                )
                            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '5%'}),
                            html.Div([
                                html.Label("Select Metric:"),
                                dcc.Dropdown(
                                    id='province-trend-metric-dropdown',
                                    options=metrics,
                                    value='Cost'
                                )
                            ], style={'width': '30%', 'display': 'inline-block'})
                        ], style={'marginBottom': 20}),
                        dcc.Graph(id='province-trend-graph')
                    ])
                ]),
                
                # Tab 4: Therapy Class
                dcc.Tab(label="Therapy Class", children=[
                    html.Div([
                        html.H3("Therapy Class Analysis", style={'textAlign': 'center'}),
                        
                        # Metric selection dropdown
                        html.Div([
                            html.Label("Select Metric:"),
                            dcc.Dropdown(
                                id='therapy-metric-dropdown',
                                options=metrics,
                                value='Cost',
                                clearable=False
                            )
                        ], style={'width': '50%', 'margin': 'auto', 'marginBottom': 20}),
                        
                        # Top 10 Therapy Classes by Cost
                        html.Div([
                            html.H4("Top 10 Therapy Classes by Cost", 
                                    style={'textAlign': 'center', 'marginTop': 30, 'marginBottom': 20}),
                            html.Div([
                                html.Div([
                                    html.Label("Select Year:"),
                                    dcc.Dropdown(
                                        id='therapy-year-dropdown',
                                        options=[{'label': str(year), 'value': year} for year in yearly_df['Year'].unique()],
                                        value=yearly_df['Year'].max()
                                    )
                                ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '5%'}),
                                html.Div([
                                    html.Label("Compare with Years:"),
                                    dcc.Dropdown(
                                        id='therapy-compare-years-dropdown',
                                        options=[{'label': str(year), 'value': year} for year in yearly_df['Year'].unique()],
                                        value=[],
                                        multi=True
                                    )
                                ], style={'width': '60%', 'display': 'inline-block'})
                            ], style={'marginBottom': 20}),
                            dcc.Graph(id='therapy-top10-graph')
                        ], style={'marginBottom': 40}),
                        
                        # Top 10 Therapy Classes Movement Over Years
                        html.Div([
                            html.H4("Top 10 Therapy Classes Movement (2018-2024)", 
                                    style={'textAlign': 'center', 'marginTop': 40, 'marginBottom': 20}),
                            dcc.Graph(id='therapy-movement-graph')
                        ]),
                        
                        # Therapy Class Ranking Movement Animation
                        html.Div([
                            html.H4("Therapy Class Ranking Movement (2018-2024)", 
                                    style={'textAlign': 'center', 'marginTop': 40, 'marginBottom': 20}),
                            html.Div([
                                html.Button(
                                    "Play Animation", 
                                    id="play-animation-button",
                                    style={
                                        'backgroundColor': '#007BFF',
                                        'color': 'white',
                                        'border': 'none',
                                        'padding': '10px 20px',
                                        'borderRadius': '5px',
                                        'cursor': 'pointer',
                                        'marginBottom': '20px'
                                    }
                                ),
                                html.Div(id='animation-year-display', style={
                                    'fontSize': '18px',
                                    'fontWeight': 'bold',
                                    'margin': '10px 0'
                                })
                            ], style={'textAlign': 'center'}),
                            dcc.Graph(id='therapy-ranking-graph'),
                            dcc.Interval(
                                id='animation-interval',
                                interval=1000,  # in milliseconds (1 second)
                                n_intervals=0,
                                disabled=True
                            ),
                            # Hidden div to store animation state
                            html.Div(id='animation-state', style={'display': 'none'})
                        ])
                    ])
                ])
            ])
        ], style={'width': '75%', 'float': 'left'})
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'width': '100%'})
])

# Callbacks for insurer selection
@app.callback(
    [Output('insurer-dropdown', 'disabled'),
     Output('data-source-display', 'children')],
    [Input('bob-toggle', 'value')]
)
def update_insurer_selection(bob_toggle):
    if bob_toggle == 'BOB':
        return True, "Book of Business (BOB)"
    else:
        return False, "Selected Insurer"

# Callback for annual trends graph
@app.callback(
    Output('annual-trends-graph', 'figure'),
    [Input('annual-metrics-dropdown', 'value'),
     Input('bob-toggle', 'value'),
     Input('insurer-dropdown', 'value')]
)
def update_annual_trends(selected_metrics, bob_toggle, selected_insurer):
    if not selected_metrics:
        return go.Figure()
    
    # Filter data based on selected insurer
    insurer_value = bob_toggle if bob_toggle == 'BOB' else selected_insurer
    filtered_df = yearly_df[yearly_df['Insurer'] == insurer_value].sort_values('Year')
    
    if filtered_df.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    for metric in selected_metrics:
        # Normalize the values to make them comparable on the same scale
        if metric in ['Claimants', 'Volumes', 'Cost']:
            # For base metrics, normalize to the first year value
            normalized_values = filtered_df[metric] / filtered_df[metric].iloc[0]
            y_values = normalized_values
            y_title = "Normalized Value (First Year = 1)"
        else:
            # For derived metrics, use actual values
            y_values = filtered_df[metric]
            y_title = "Value"
        
        fig.add_trace(go.Scatter(
            x=filtered_df['Year'],
            y=y_values,
            mode='lines+markers',
            name=metric.replace('_', ' ')
        ))
    
    insurer_label = "BOB" if bob_toggle == 'BOB' else f"Insurer {selected_insurer}"
    fig.update_layout(
        title=f'Annual Trends - {insurer_label}',
        xaxis_title='Year',
        yaxis_title=y_title,
        legend_title='Metrics',
        hovermode='x unified'
    )
    
    return fig

# Callback for growth rates graph
@app.callback(
    Output('growth-rates-graph', 'figure'),
    [Input('growth-metrics-dropdown', 'value'),
     Input('bob-toggle', 'value'),
     Input('insurer-dropdown', 'value')]
)
def update_growth_rates(selected_metrics, bob_toggle, selected_insurer):
    if not selected_metrics:
        return go.Figure()
    
    # Filter data based on selected insurer
    insurer_value = bob_toggle if bob_toggle == 'BOB' else selected_insurer
    filtered_df = yearly_df[yearly_df['Insurer'] == insurer_value].sort_values('Year')
    
    if filtered_df.empty or len(filtered_df) <= 1:
        return go.Figure()
    
    fig = go.Figure()
    
    for metric in selected_metrics:
        fig.add_trace(go.Bar(
            x=filtered_df['Year'][1:],  # Skip first year as it has no growth rate
            y=filtered_df[metric][1:],
            name=metric.replace('_', ' ')
        ))
    
    insurer_label = "BOB" if bob_toggle == 'BOB' else f"Insurer {selected_insurer}"
    fig.update_layout(
        title=f'Annual Growth Rates - {insurer_label}',
        xaxis_title='Year',
        yaxis_title='Growth Rate (%)',
        legend_title='Metrics',
        hovermode='x unified'
    )
    
    return fig

# Callback for province bar graph
@app.callback(
    Output('province-bar-graph', 'figure'),
    [Input('province-year-dropdown', 'value'),
     Input('province-metric-dropdown', 'value'),
     Input('bob-toggle', 'value'),
     Input('insurer-dropdown', 'value')]
)
def update_province_bar(selected_year, selected_metric, bob_toggle, selected_insurer):
    # Filter data based on selected insurer and year
    insurer_value = bob_toggle if bob_toggle == 'BOB' else selected_insurer
    filtered_df = province_df[(province_df['Year'] == selected_year) & 
                             (province_df['Insurer'] == insurer_value)]
    
    if filtered_df.empty:
        return go.Figure()
    
    filtered_df = filtered_df.sort_values(by=selected_metric, ascending=False)
    
    insurer_label = "BOB" if bob_toggle == 'BOB' else f"Insurer {selected_insurer}"
    fig = px.bar(
        filtered_df,
        x='Province',
        y=selected_metric,
        title=f'{selected_metric.replace("_", " ")} by Province in {selected_year} - {insurer_label}',
        color='Province',
        text=selected_metric
    )
    
    fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    fig.update_layout(
        xaxis_title='Province',
        yaxis_title=selected_metric.replace('_', ' '),
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        height=600  # Increase height to show all data clearly
    )
    
    return fig

# Callback for top provinces trend graph
@app.callback(
    Output('top-provinces-trend-graph', 'figure'),
    [Input('province-metric-dropdown', 'value'),
     Input('bob-toggle', 'value'),
     Input('insurer-dropdown', 'value')]
)
def update_top_provinces_trend(selected_metric, bob_toggle, selected_insurer):
    # Filter data based on selected insurer
    insurer_value = bob_toggle if bob_toggle == 'BOB' else selected_insurer
    insurer_data = province_df[province_df['Insurer'] == insurer_value]
    
    if insurer_data.empty:
        return go.Figure()
    
    latest_year = insurer_data['Year'].max()
    latest_data = insurer_data[insurer_data['Year'] == latest_year]
    
    top_provinces = latest_data.sort_values(by=selected_metric, ascending=False).head(5)['Province'].tolist()
    top_provinces_data = insurer_data[insurer_data['Province'].isin(top_provinces)]
    
    insurer_label = "BOB" if bob_toggle == 'BOB' else f"Insurer {selected_insurer}"
    fig = px.line(
        top_provinces_data,
        x='Year',
        y=selected_metric,
        color='Province',
        title=f'Trend of {selected_metric.replace("_", " ")} for Top 5 Provinces - {insurer_label}',
        markers=True,
        line_shape='linear'
    )
    
    fig.update_layout(
        xaxis_title='Year',
        yaxis_title=selected_metric.replace('_', ' '),
        legend_title='Province',
        hovermode='x unified',
        height=600  # Increase height to show all data clearly
    )
    
    return fig

# Callback for province trend graph
@app.callback(
    Output('province-trend-graph', 'figure'),
    [Input('province-trend-dropdown', 'value'),
     Input('province-trend-metric-dropdown', 'value'),
     Input('bob-toggle', 'value'),
     Input('insurer-dropdown', 'value')]
)
def update_province_trend(selected_province, selected_metric, bob_toggle, selected_insurer):
    if not selected_province:
        return go.Figure()
    
    # Filter data based on selected insurer and province
    insurer_value = bob_toggle if bob_toggle == 'BOB' else selected_insurer
    filtered_df = province_df[(province_df['Province'] == selected_province) & 
                             (province_df['Insurer'] == insurer_value)].sort_values(by='Year')
    
    if filtered_df.empty:
        return go.Figure()
    
    # Get overall average for the selected insurer
    insurer_yearly = yearly_df[yearly_df['Insurer'] == insurer_value].sort_values('Year')
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=filtered_df['Year'],
        y=filtered_df[selected_metric],
        mode='lines+markers',
        name=f'{selected_province}',
        line=dict(color='#007BFF', width=3),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=insurer_yearly['Year'],
        y=insurer_yearly[selected_metric],
        mode='lines+markers',
        name='Overall Average',
        line=dict(color='#6c757d', width=2, dash='dash'),
        marker=dict(size=6)
    ))
    
    filtered_df['Growth'] = filtered_df[selected_metric].pct_change() * 100
    
    for i in range(1, len(filtered_df)):
        growth = filtered_df['Growth'].iloc[i]
        if not pd.isna(growth):
            fig.add_annotation(
                x=filtered_df['Year'].iloc[i],
                y=filtered_df[selected_metric].iloc[i],
                text=f"{growth:.1f}%",
                showarrow=True,
                arrowhead=4,
                arrowsize=1,
                arrowwidth=1,
                arrowcolor="#636363",
                ax=0,
                ay=-30,
                font=dict(size=10)
            )
    
    insurer_label = "BOB" if bob_toggle == 'BOB' else f"Insurer {selected_insurer}"
    fig.update_layout(
        title=f'Annual Trend of {selected_metric.replace("_", " ")} for {selected_province} - {insurer_label}',
        xaxis_title='Year',
        yaxis_title=selected_metric.replace('_', ' '),
        legend_title='Data Series',
        hovermode='x unified',
        height=600  # Increase height to show all data clearly
    )
    
    return fig

# Callback for generic table
@app.callback(
    Output('generic-table', 'data'),
    [Input('generic-year-dropdown', 'value'),
     Input('bob-toggle', 'value'),
     Input('insurer-dropdown', 'value')]
)
def update_generic_table(selected_year, bob_toggle, selected_insurer):
    # Filter data based on selected insurer and year
    insurer_value = bob_toggle if bob_toggle == 'BOB' else selected_insurer
    filtered_df = generic_df[(generic_df['Year'] == selected_year) & 
                            (generic_df['Insurer'] == insurer_value)]
    
    return filtered_df.to_dict('records')

# Callback for generic name bar graph with insurer filtering
@app.callback(
    Output('generic-bar-graph', 'figure'),
    [Input('generic-year-dropdown', 'value'),
     Input('generic-metric-dropdown', 'value'),
     Input('generic-compare-years-dropdown', 'value'),
     Input('bob-toggle', 'value'),
     Input('insurer-dropdown', 'value')]
)
def update_generic_bar(selected_year, selected_metric, compare_years, bob_toggle, selected_insurer):
    # Filter data based on selected insurer and year
    insurer_value = bob_toggle if bob_toggle == 'BOB' else selected_insurer
    filtered_df = generic_df[(generic_df['Year'] == selected_year) & 
                            (generic_df['Insurer'] == insurer_value)]
    
    if filtered_df.empty:
        return go.Figure()
    
    # Sort by cost and get top 10
    top_10_by_cost = filtered_df.sort_values(by='Cost', ascending=False).head(10)
    
    # Calculate percentage of total cost
    total_cost = filtered_df['Cost'].sum()
    top_10_by_cost['Percent_of_Total'] = (top_10_by_cost['Cost'] / total_cost) * 100
    
    # Get the generic names to use for comparison
    top_10_names = top_10_by_cost['Generic_Name'].tolist()
    
    # Sort by the selected metric for display
    top_10_by_cost = top_10_by_cost.sort_values(by=selected_metric, ascending=True)
    
    # Create figure with two y-axes
    fig = go.Figure()
    
    # Add bars for the selected year
    fig.add_trace(go.Bar(
        y=top_10_by_cost['Generic_Name'],
        x=top_10_by_cost[selected_metric],
        orientation='h',
        name=f"{selected_year}",
        marker=dict(color='#007BFF'),
        text=top_10_by_cost[selected_metric].apply(lambda x: f"{x:,.0f}" if selected_metric not in ['Cost_Per_Claimant', 'Cost_Per_Volume'] else f"${x:,.2f}"),
        textposition='outside',
        hoverinfo='text',
        hovertext=[
            f"{row['Generic_Name']}<br>"
            f"{selected_year}: {row[selected_metric]:,.2f}<br>"
            f"% of Total Cost: {row['Percent_of_Total']:.1f}%"
            for _, row in top_10_by_cost.iterrows()
        ]
    ))
    
    # Add comparison years if selected
    colors = ['#28A745', '#FD7E14', '#6610F2', '#20C997']
    for i, year in enumerate(compare_years):
        if year != selected_year:  # Skip if it's the same as the selected year
            year_data = generic_df[(generic_df['Year'] == year) & 
                                  (generic_df['Insurer'] == insurer_value)]
            
            # Filter for the top 10 names from the selected year
            year_data = year_data[year_data['Generic_Name'].isin(top_10_names)]
            
            if not year_data.empty:
                # Sort to match the order of the selected year
                year_data = year_data.set_index('Generic_Name').reindex(top_10_by_cost['Generic_Name']).reset_index()
                
                # Add bars for this comparison year
                fig.add_trace(go.Bar(
                    y=year_data['Generic_Name'],
                    x=year_data[selected_metric],
                    orientation='h',
                    name=f"{year}",
                    marker=dict(color=colors[i % len(colors)]),
                    opacity=0.7,
                    hoverinfo='text',
                    hovertext=[
                        f"{row['Generic_Name']}<br>"
                        f"{year}: {row[selected_metric]:,.2f}"
                        for _, row in year_data.iterrows()
                    ]
                ))
    
    # Always add markers for percentage of total cost
    fig.add_trace(go.Scatter(
        y=top_10_by_cost['Generic_Name'],
        x=top_10_by_cost['Percent_of_Total'],
        mode='markers+text',
        name='% of Total Cost',
        marker=dict(
            symbol='circle',
            size=12,
            color='#DC3545'
        ),
        text=top_10_by_cost['Percent_of_Total'].apply(lambda x: f"{x:.1f}%"),
        textposition='middle right',
        xaxis='x2'
    ))
    
    # Update layout with secondary x-axis
    insurer_label = "BOB" if bob_toggle == 'BOB' else f"Insurer {selected_insurer}"
    fig.update_layout(
        xaxis2=dict(
            title='% of Total Cost',
            overlaying='x',
            side='top',
            range=[0, max(top_10_by_cost['Percent_of_Total']) * 1.2],
            showgrid=False
        ),
        title=f'Top 10 Generic Names by Cost - {selected_metric.replace("_", " ")} ({selected_year}) - {insurer_label}',
        xaxis=dict(
            title=selected_metric.replace('_', ' '),
            showgrid=True
        ),
        yaxis=dict(
            title='Generic Name',
            categoryorder='array',
            categoryarray=top_10_by_cost['Generic_Name'].tolist()
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        margin=dict(l=20, r=20, t=80, b=20),
        height=600,
        barmode='group' if compare_years else 'relative'
    )
    
    return fig

# Callback for therapy top 10 graph
@app.callback(
    Output('therapy-top10-graph', 'figure'),
    [Input('therapy-metric-dropdown', 'value'),
     Input('therapy-year-dropdown', 'value'),
     Input('therapy-compare-years-dropdown', 'value'),
     Input('bob-toggle', 'value'),
     Input('insurer-dropdown', 'value')]
)
def update_therapy_top10(selected_metric, selected_year, compare_years, bob_toggle, selected_insurer):
    # Filter data based on selected insurer and year
    insurer_value = bob_toggle if bob_toggle == 'BOB' else selected_insurer
    selected_data = therapy_df[(therapy_df['Year'] == selected_year) & 
                              (therapy_df['Insurer'] == insurer_value)]
    
    if selected_data.empty:
        return go.Figure()
    
    # Sort by cost and get top 10
    top_10_by_cost = selected_data.sort_values(by='Cost', ascending=False).head(10)
    
    # Calculate percentage of total cost
    total_cost = selected_data['Cost'].sum()
    top_10_by_cost['Percent_of_Total'] = (top_10_by_cost['Cost'] / total_cost) * 100
    
    # Get the therapy classes to use for comparison
    top_10_classes = top_10_by_cost['Therapy_Class'].tolist()
    
    # Sort by the selected metric for display
    top_10_by_cost = top_10_by_cost.sort_values(by=selected_metric, ascending=True)
    
    # Create figure with two y-axes
    fig = go.Figure()
    
    # Add bars for the selected year
    fig.add_trace(go.Bar(
        y=top_10_by_cost['Therapy_Class'],
        x=top_10_by_cost[selected_metric],
        orientation='h',
        name=f"{selected_year}",
        marker=dict(color='#007BFF'),
        text=top_10_by_cost[selected_metric].apply(lambda x: f"{x:,.0f}" if selected_metric not in ['Cost_Per_Claimant', 'Cost_Per_Volume'] else f"${x:,.2f}"),
        textposition='outside',
        hoverinfo='text',
        hovertext=[
            f"{row['Therapy_Class']}<br>"
            f"{selected_year}: {row[selected_metric]:,.2f}<br>"
            f"% of Total Cost: {row['Percent_of_Total']:.1f}%"
            for _, row in top_10_by_cost.iterrows()
        ]
    ))
    
    # Add comparison years if selected
    colors = ['#28A745', '#FD7E14', '#6610F2', '#20C997']
    for i, year in enumerate(compare_years):
        if year != selected_year:  # Skip if it's the same as the selected year
            year_data = therapy_df[(therapy_df['Year'] == year) & 
                                  (therapy_df['Insurer'] == insurer_value)]
            
            # Filter for the top 10 classes from the selected year
            year_data = year_data[year_data['Therapy_Class'].isin(top_10_classes)]
            
            if not year_data.empty:
                # Sort to match the order of the selected year
                year_data = year_data.set_index('Therapy_Class').reindex(top_10_by_cost['Therapy_Class']).reset_index()
                
                # Add bars for this comparison year
                fig.add_trace(go.Bar(
                    y=year_data['Therapy_Class'],
                    x=year_data[selected_metric],
                    orientation='h',
                    name=f"{year}",
                    marker=dict(color=colors[i % len(colors)]),
                    opacity=0.7,
                    hoverinfo='text',
                    hovertext=[
                        f"{row['Therapy_Class']}<br>"
                        f"{year}: {row[selected_metric]:,.2f}"
                        for _, row in year_data.iterrows()
                    ]
                ))
    
    # Always add markers for percentage of total cost
    fig.add_trace(go.Scatter(
        y=top_10_by_cost['Therapy_Class'],
        x=top_10_by_cost['Percent_of_Total'],
        mode='markers+text',
        name='% of Total Cost',
        marker=dict(
            symbol='circle',
            size=12,
            color='#DC3545'
        ),
        text=top_10_by_cost['Percent_of_Total'].apply(lambda x: f"{x:.1f}%"),
        textposition='middle right',
        xaxis='x2'
    ))
    
    # Update layout with secondary x-axis
    insurer_label = "BOB" if bob_toggle == 'BOB' else f"Insurer {selected_insurer}"
    fig.update_layout(
        xaxis2=dict(
            title='% of Total Cost',
            overlaying='x',
            side='top',
            range=[0, max(top_10_by_cost['Percent_of_Total']) * 1.2],
            showgrid=False
        ),
        title=f'Top 10 Therapy Classes by Cost - {selected_metric.replace("_", " ")} ({selected_year}) - {insurer_label}',
        xaxis=dict(
            title=selected_metric.replace('_', ' '),
            showgrid=True
        ),
        yaxis=dict(
            title='Therapy Class',
            categoryorder='array',
            categoryarray=top_10_by_cost['Therapy_Class'].tolist()
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        margin=dict(l=20, r=20, t=80, b=20),
        height=600,
        barmode='group' if compare_years else 'relative'
    )
    
    return fig

# Callback for therapy movement graph with insurer filtering
@app.callback(
    Output('therapy-movement-graph', 'figure'),
    [Input('therapy-metric-dropdown', 'value'),
     Input('therapy-year-dropdown', 'value'),
     Input('bob-toggle', 'value'),
     Input('insurer-dropdown', 'value')]
)
def update_therapy_movement(selected_metric, selected_year, bob_toggle, selected_insurer):
    # Filter data based on selected insurer
    insurer_value = bob_toggle if bob_toggle == 'BOB' else selected_insurer
    
    # Get data for the selected year and insurer
    selected_data = therapy_df[(therapy_df['Year'] == selected_year) & 
                              (therapy_df['Insurer'] == insurer_value)]
    
    if selected_data.empty:
        return go.Figure()
    
    # Get top 10 therapy classes by cost in the selected year
    top_10_classes = selected_data.sort_values(by='Cost', ascending=False).head(10)['Therapy_Class'].tolist()
    
    # Filter data for these top 10 classes across all years for the selected insurer
    filtered_df = therapy_df[(therapy_df['Therapy_Class'].isin(top_10_classes)) & 
                            (therapy_df['Insurer'] == insurer_value)]
    
    # Create a figure
    fig = go.Figure()
    
    # Add a line for each therapy class
    for therapy_class in top_10_classes:
        class_data = filtered_df[filtered_df['Therapy_Class'] == therapy_class].sort_values(by='Year')
        
        if not class_data.empty:
            fig.add_trace(go.Scatter(
                x=class_data['Year'],
                y=class_data[selected_metric],
                mode='lines+markers',
                name=therapy_class,
                hovertemplate=
                    f"{therapy_class}<br>" +
                    "Year: %{x}<br>" +
                    f"{selected_metric.replace('_', ' ')}: " + 
                    ("%{y:$,.2f}" if selected_metric in ['Cost_Per_Claimant', 'Cost_Per_Volume'] else 
                     ("%{y:$,.0f}" if selected_metric == 'Cost' else "%{y:,.0f}")) +
                    "<extra></extra>"
            ))
    
    # Update layout
    insurer_label = "BOB" if bob_toggle == 'BOB' else f"Insurer {selected_insurer}"
    fig.update_layout(
        title=f'Movement of Top 10 Therapy Classes (2018-2024) - {selected_metric.replace("_", " ")} - {insurer_label}',
        xaxis=dict(
            title='Year',
            tickmode='array',
            tickvals=list(range(2018, 2025)),
            ticktext=[str(year) for year in range(2018, 2025)]
        ),
        yaxis=dict(
            title=selected_metric.replace('_', ' '),
            showgrid=True
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.2,
            xanchor='center',
            x=0.5
        ),
        margin=dict(l=20, r=20, t=80, b=100),
        height=600,
        hovermode='closest'
    )
    
    return fig

# Callback to update the latest year summary cards based on insurer selection
@app.callback(
    [Output('latest-year-claimants', 'children'),
     Output('latest-year-volumes', 'children'),
     Output('latest-year-cost', 'children'),
     Output('latest-year-cost-per-claimant', 'children'),
     Output('latest-year-cost-per-volume', 'children'),
     Output('latest-year-claims-per-claimant', 'children'),
     Output('latest-year-claimants-growth', 'children'),
     Output('latest-year-volumes-growth', 'children'),
     Output('latest-year-cost-growth', 'children'),
     Output('latest-year-cost-per-claimant-growth', 'children'),
     Output('latest-year-cost-per-volume-growth', 'children'),
     Output('latest-year-claims-per-claimant-growth', 'children')],
    [Input('bob-toggle', 'value'),
     Input('insurer-dropdown', 'value')]
)
def update_latest_year_summary(bob_toggle, selected_insurer):
    # Filter data based on selected insurer
    insurer_value = bob_toggle if bob_toggle == 'BOB' else selected_insurer
    filtered_df = yearly_df[yearly_df['Insurer'] == insurer_value].sort_values('Year')
    
    if filtered_df.empty:
        # Return empty values if no data
        return ["N/A"] * 12
    
    # Get the latest year data
    latest_data = filtered_df.iloc[-1]
    
    # Format the values
    claimants = f"{latest_data['Claimants']:,.0f}"
    volumes = f"{latest_data['Volumes']:,.0f}"
    cost = f"${latest_data['Cost']:,.0f}"
    cost_per_claimant = f"${latest_data['Cost_Per_Claimant']:,.2f}"
    cost_per_volume = f"${latest_data['Cost_Per_Volume']:,.2f}"
    claims_per_claimant = f"{latest_data['Claims_Per_Claimant']:,.2f}"
    
    # Format the growth rates
    claimants_growth = f"({latest_data['Claimants_Growth']:.1f}% from previous year)" if not pd.isna(latest_data['Claimants_Growth']) else ""
    volumes_growth = f"({latest_data['Volumes_Growth']:.1f}% from previous year)" if not pd.isna(latest_data['Volumes_Growth']) else ""
    cost_growth = f"({latest_data['Cost_Growth']:.1f}% from previous year)" if not pd.isna(latest_data['Cost_Growth']) else ""
    cost_per_claimant_growth = f"({latest_data['Cost_Per_Claimant_Growth']:.1f}% from previous year)" if not pd.isna(latest_data['Cost_Per_Claimant_Growth']) else ""
    cost_per_volume_growth = f"({latest_data['Cost_Per_Volume_Growth']:.1f}% from previous year)" if not pd.isna(latest_data['Cost_Per_Volume_Growth']) else ""
    claims_per_claimant_growth = f"({latest_data['Claims_Per_Claimant_Growth']:.1f}% from previous year)" if not pd.isna(latest_data['Claims_Per_Claimant_Growth']) else ""
    
    return [
        claimants, volumes, cost, 
        cost_per_claimant, cost_per_volume, claims_per_claimant,
        claimants_growth, volumes_growth, cost_growth,
        cost_per_claimant_growth, cost_per_volume_growth, claims_per_claimant_growth
    ]

# Callback to toggle animation interval
@app.callback(
    [Output('animation-interval', 'disabled'),
     Output('animation-state', 'children')],
    [Input('play-animation-button', 'n_clicks')],
    [State('animation-state', 'children')]
)
def toggle_animation(n_clicks, current_state):
    if n_clicks is None:
        # Initial state: animation is disabled
        return True, "stopped"
    
    # Toggle the animation state
    if current_state == "stopped" or current_state is None:
        return False, "playing"
    else:
        return True, "stopped"

# Callback to update the year display during animation
@app.callback(
    Output('animation-year-display', 'children'),
    [Input('animation-interval', 'n_intervals')],
    [State('animation-state', 'children')]
)
def update_year_display(n_intervals, animation_state):
    if animation_state != "playing":
        return "Year: 2018"
    
    # Calculate which year to show based on the interval count
    years = list(range(2018, 2025))
    year_index = n_intervals % len(years)
    return f"Year: {years[year_index]}"

# Callback for therapy ranking graph with animation and insurer filtering
@app.callback(
    Output('therapy-ranking-graph', 'figure'),
    [Input('animation-interval', 'n_intervals'),
     Input('therapy-metric-dropdown', 'value'),
     Input('bob-toggle', 'value'),
     Input('insurer-dropdown', 'value')],
    [State('animation-state', 'children')]
)
def update_therapy_ranking(n_intervals, selected_metric, bob_toggle, selected_insurer, animation_state):
    # Filter data based on selected insurer
    insurer_value = bob_toggle if bob_toggle == 'BOB' else selected_insurer
    
    # Get all years from 2018 to 2024
    years = list(range(2018, 2025))
    
    # Determine which year to display
    if animation_state == "playing":
        display_year = years[n_intervals % len(years)]
    else:
        # Default to the first year when not animating
        display_year = years[0]
    
    # Get data for the current year and insurer
    year_data = therapy_df[(therapy_df['Year'] == display_year) & 
                          (therapy_df['Insurer'] == insurer_value)]
    
    if year_data.empty:
        return go.Figure()
    
    # Sort by the selected metric to determine rankings
    ranked_data = year_data.sort_values(by=selected_metric, ascending=False)
    
    # Add a bar for each therapy class, showing its rank
    colors = px.colors.qualitative.Plotly
    
    # Get top 15 classes for better visibility
    top_classes = ranked_data.head(15)
    
    # Create a figure
    fig = go.Figure()
    
    # Create the horizontal bar chart
    fig.add_trace(go.Bar(
        y=[f"{i+1}. {row['Therapy_Class']}" for i, (_, row) in enumerate(top_classes.iterrows())],
        x=top_classes[selected_metric],
        orientation='h',
        marker=dict(
            color=[colors[i % len(colors)] for i in range(len(top_classes))],
            line=dict(width=1)
        ),
        text=top_classes[selected_metric].apply(lambda x: f"{x:,.0f}" if selected_metric not in ['Cost_Per_Claimant', 'Cost_Per_Volume'] 
                                               else f"${x:,.2f}"),
        textposition='outside',
        hoverinfo='text',
        hovertext=[
            f"Rank {i+1}: {row['Therapy_Class']}<br>"
            f"{selected_metric.replace('_', ' ')}: " + 
            (f"${row[selected_metric]:,.2f}" if selected_metric in ['Cost_Per_Claimant', 'Cost_Per_Volume'] 
             else f"${row[selected_metric]:,.0f}" if selected_metric == 'Cost' else f"{row[selected_metric]:,.0f}")
            for i, (_, row) in enumerate(top_classes.iterrows())
        ]
    ))
    
    # Update layout
    insurer_label = "BOB" if bob_toggle == 'BOB' else f"Insurer {selected_insurer}"
    fig.update_layout(
        title=f'Therapy Class Rankings by {selected_metric.replace("_", " ")} in {display_year} - {insurer_label}',
        xaxis=dict(
            title=selected_metric.replace('_', ' '),
            showgrid=True
        ),
        yaxis=dict(
            title='Rank and Therapy Class',
            autorange="reversed"  # To show rank 1 at the top
        ),
        margin=dict(l=20, r=20, t=80, b=20),
        height=600
    )
    
    # Add annotations to show rank changes from previous year (if not the first year)
    if display_year > 2018 and animation_state == "playing":
        prev_year = display_year - 1
        prev_year_data = therapy_df[(therapy_df['Year'] == prev_year) & 
                                   (therapy_df['Insurer'] == insurer_value)]
        
        if not prev_year_data.empty:
            # Sort previous year data by the selected metric
            prev_ranked_data = prev_year_data.sort_values(by=selected_metric, ascending=False)
            
            # Create a mapping of therapy class to previous rank
            prev_ranks = {row['Therapy_Class']: i+1 for i, (_, row) in enumerate(prev_ranked_data.iterrows())}
            
            # Add annotations for rank changes
            for i, (_, row) in enumerate(top_classes.iterrows()):
                therapy_class = row['Therapy_Class']
                current_rank = i + 1
                
                if therapy_class in prev_ranks:
                    prev_rank = prev_ranks[therapy_class]
                    rank_change = prev_rank - current_rank
                    
                    if rank_change != 0:
                        # Determine color and symbol based on direction of change
                        if rank_change > 0:
                            # Improved rank (moved up)
                            color = 'green'
                            symbol = '▲'
                        else:
                            # Worsened rank (moved down)
                            color = 'red'
                            symbol = '▼'
                        
                        fig.add_annotation(
                            y=f"{current_rank}. {therapy_class}",
                            x=row[selected_metric] * 1.02,  # Position slightly to the right of the bar
                            text=f"{symbol} {abs(rank_change)}",
                            showarrow=False,
                            font=dict(color=color, size=12),
                            align='left'
                        )
    
    return fig

# Run the app
if __name__ == '__main__':
   # app.run_server(debug=False, host="0.0.0.0", port=8080)
    app.run_server(debug=False)