import pandas as pd
import numpy as np
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import dash_bootstrap_components as dbc

pd.set_option('display.max_rows', 20)
pd.set_option('display.min_rows', 20)


DATA_FILE = 'data/income_classes_processed.csv'

# stylesheet with the .dbc class from dash-bootstrap-templates library
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash('Test Salary Plot', external_stylesheets=[dbc.themes.PULSE, dbc_css])

def combine_high_income_rows(df):
    min_income_threshold = 1500
    income_range_string = f'{min_income_threshold:,d}-'.replace(',', ' ')
    mask = df['min_income'] >= min_income_threshold
    group_by_headers = ['age_range', 'gender', 'min_income', 'income', 'max_income']
    df.loc[mask, 'min_income'] = min_income_threshold
    df.loc[mask, 'max_income'] = ''
    df.loc[mask, 'income'] = income_range_string
    df = df.groupby(group_by_headers, as_index=False).sum()
    return df


# Processing data
def calculate_percentiles(df):    
    group_by_headers = ['age_range', 'gender']
    df['percent_of_people'] = df['number_of_people'] / df.groupby(group_by_headers)['number_of_people'].transform('sum')
    df['percentile'] = df.groupby(group_by_headers)['percent_of_people'].cumsum()
    df['percentile'] = df['percentile'] * 100
    df['selected_income_bracket'] = False
    return df


def create_interpolation_series(df, percentiles):
    x = df['percentile'].to_numpy()
    y = df['min_income'].to_numpy()
    return np.interp(percentiles, x, y, left=0)
    

def create_interpolated_percentile_df(df):
    percentile_dfs_list = []
    percentiles=list(range(0,101))
    group_by_headers = ['age_range', 'gender']

    for headers, group in df.groupby(group_by_headers):
        interpolated_incomes = create_interpolation_series(group, percentiles)
        group_df = pd.DataFrame({
            'percentile': percentiles,
            'interpolated_income': interpolated_incomes
            })
        group_df[group_by_headers[0]] = headers[0]
        group_df[group_by_headers[1]] = headers[1]
        percentile_dfs_list.append(group_df)
    percentile_dfs = pd.concat(percentile_dfs_list)
    return percentile_dfs

def process_data(df):
    df = combine_high_income_rows(df)
    df = calculate_percentiles(df)
    df_interp = create_interpolated_percentile_df(df)
    return df, df_interp

df = pd.read_csv(DATA_FILE)
df, df_interp = process_data(df)

# App layout
app.layout = dbc.Container(html.Div([
    
    html.Div(children=[
        dbc.Row([
            html.Div(html.H1('Var är du på inkomstskalan?'))

        ]),
        dbc.Row([
            dbc.Col(html.Div(children=[
            html.H4('Din månadsinkomst före skatt är:'),

            html.Div(children='''
            Jämför med åldersgrupp och kön (män, kvinnor eller samtliga).
            '''),

            dcc.Input(id='salary-input', placeholder='0', type='text'),

            dcc.Dropdown(
                id="dropdown-age",
                options=["Totalt 20-64 år", "20-24 år", "25-29 år", "30-34 år", "35-39 år", "40-44 år", "45-49 år", "50-54 år", "55-59 år", "60-64 år"],
                value="Totalt 20-64 år"
            ),

            dcc.Dropdown(
                id="dropdown-gender",
                options=[
                    {'label': 'Kvinnor och män', 'value': 'Samtliga'},
                    {'label': 'Kvinnor', 'value': 'Kvinnor'},
                    {'label': 'Män', 'value': 'Män'},
                ],
                value="Samtliga"
            ),
        ])),

            dbc.Col(html.Div(children=[
                html.Div(id='graph-income-text')
        ]))
        
    ])]),

    dbc.Row(html.Div(children=[
        dcc.Graph(id="graph-income",
        config={'displayModeBar': False},
        ),
    ])),

    dbc.Row(html.Div(children=[
        dcc.Graph(id="graph-percentile",
        config={'displayModeBar': False},
        ),
    ]))


]), 
className='dbc')


def create_figure(df):
    fig = px.bar(
        df,
        x='income',
        y='number_of_people',
        color='selected_income_bracket',
    )

    fig.update_traces(hoverinfo="none", hovertemplate=None)
    fig.update_layout(xaxis={'categoryorder':'array', 'categoryarray': df['income'].iloc[0:45]}) #???
    fig.update_layout(showlegend=False)
    fig.layout.xaxis.fixedrange = True
    fig.layout.yaxis.fixedrange = True
    return fig


def create_percentile_figure(df, age_range, gender):
    print(df)
    mask = ((df['age_range']==age_range) & (df['gender']==gender))
    masked_df=df.loc[mask].copy()
    fig = px.bar(
        masked_df,
        x='percentile',
        y='interpolated_income', 
    )
    return fig


@app.callback(
    Output('graph-income-text', 'children'),
    Output("graph-income", "figure"),
    Output("graph-percentile", "figure"),
    Input('dropdown-age', 'value'),
    Input('dropdown-gender', 'value'),
    Input("salary-input", "value")
)
def update_page(age_range, gender, salary_input):

    mask = ((df['age_range']==age_range) & (df['gender']==gender))
    masked_df=df.loc[mask].copy()

    figure_percentile = create_percentile_figure(df_interp, age_range, gender)

    if salary_input:
        try:
            monthly_salary = int(salary_input)
            yearly_salary = monthly_salary/1000*12
        except:
            return [html.P('Fyll i siffror'),  create_figure(masked_df), figure_percentile]

        income_bracket = masked_df[yearly_salary >= masked_df['min_income']]['income'].iloc[-1]
        masked_df['selected_income_bracket'] = df['income'] == income_bracket
        masked_df['selected_income_bracket'] = df['income'] == income_bracket


        df_row = masked_df.loc[masked_df['income'] == income_bracket].iloc[0]
        percent_of_people = df_row['percent_of_people']
        percentile = df_row['percentile']


        children = html.Div([
            html.P(f"Du har en månadslön på {monthly_salary} kr. Det innebär en årslön på {yearly_salary} tkr."),
            html.P(f"{round(percent_of_people*100,1)}% av personer tjänar inom spannet {income_bracket} tkr per år. Du tjänar mer än {round(percentile*100, 1)}% av befolkingen"),
            
        ])
        return (children, create_figure(masked_df), figure_percentile)

    fig = create_figure(masked_df)

    return [html.P('Fyll i din månadslön'),  fig, figure_percentile]
    



if __name__ =='__main__':
    app.run_server(debug=True)