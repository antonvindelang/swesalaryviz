import pandas as pd
import numpy as np
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import dash_bootstrap_components as dbc

INCOME_FILE = 'data/income_classes_processed.csv'
INTERP_FILE = 'data/percentiles_processed.csv'

df_income = pd.read_csv(INCOME_FILE)
df_interp = pd.read_csv(INTERP_FILE)


# stylesheet with the .dbc class from dash-bootstrap-templates library
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash('Test Salary Plot', external_stylesheets=[
           dbc.themes.PULSE, dbc_css])
server = app.server


# App layout
app.layout = dbc.Container(html.Div([

    html.Div(children=[
        dbc.Row([
            html.Div(html.H1('Var är du på inkomstskalan?')),
            html.P(
                'Data baserat på 2020 års inkomstdata från SCB. Percentiler är interpolerade från mindre granulär data.'),

        ]),
        dbc.Row([
            dbc.Col(html.Div(children=[

                html.H4('Din månadsinkomst före skatt är:'),

                html.Div(children='''
            Jämför med åldersgrupp och kön (män, kvinnor eller samtliga).
            '''),

                dcc.Input(id='salary-input',
                          className='input',
                          placeholder='Din månadslön',
                          type='text'),

                dcc.Dropdown(
                    id="dropdown-age",
                    className='dropdown',
                    options=["Totalt 20-64 år", "20-24 år", "25-29 år", "30-34 år",
                             "35-39 år", "40-44 år", "45-49 år", "50-54 år", "55-59 år", "60-64 år"],
                    value="Totalt 20-64 år"
                ),

                dcc.Dropdown(
                    id="dropdown-gender",
                    className='dropdown',
                    options=[
                        {'label': 'Kvinnor och män', 'value': 'Samtliga'},
                        {'label': 'Kvinnor', 'value': 'Kvinnor'},
                        {'label': 'Män', 'value': 'Män'},
                    ],
                    value="Samtliga"
                ),
            ])),

            dbc.Col(html.Div(children=[
                html.Div(id='graph-income-text', className='graphincometext')
            ]))

        ])]),

    dbc.Row(html.Div(children=[
        dcc.Graph(id="graph-income",
                  className="graph",
                  config={'displayModeBar': False},
                  ),
    ])),

    dbc.Row(html.Div(children=[
        dcc.Graph(id="graph-percentile",
                  config={'displayModeBar': False},
                  ),
    ])),


    dbc.Row(html.Div(children=[
        html.Footer('Data is sourced from Statistics Sweden'),

        html.Img(id='github_img',
                 className='githubimg',
                 src="assets/GitHub-Mark-32px.png", height='16px'),
        html.A('Check out the repository on github',
               href='https://github.com/antonvindelang/swesalaryviz', target="_blank"),
    ]),
        style={'text-align': 'right'})

]),
    className='dbc')


def create_income_figure(df):
    fig = px.bar(
        df,
        x='income',
        y='number_of_people',
        labels={
            'income': "Årsinkomst (tkr)",
            'number_of_people': 'Antal personer'
        },
        color='selected_income_bracket',
        color_discrete_map={
            False: "#A9A9A9",
            True: "#3CB371"
        },
        hover_data={"selected_income_bracket": False}
    )

    fig.update_layout(xaxis={
        'categoryorder': 'array',
        'categoryarray': df['income'].iloc[0:32],
        'showgrid': False,
        'fixedrange': True,
    },  # TODO: Fix magic number
        yaxis={
            'fixedrange': True,
            'showgrid': False,
    },
        showlegend=False,
        title_text='Antal personer i vald grupp per årsinkomstsintervall',
        font_family='Tahoma',
        plot_bgcolor='#E8E8E8',
        paper_bgcolor='#F8F8F8'
    )

    fig.layout.xaxis.fixedrange = True
    fig.layout.yaxis.fixedrange = True
    return fig


def create_percentile_figure(df, age_range, gender, salary_input):
    mask = ((df['age_range'] == age_range) & (df['gender'] == gender))
    masked_df = df.loc[mask].copy()
    if salary_input:
        try:
            monthly_salary = int(salary_input)
            yearly_salary = monthly_salary/1000*12
            percentile = masked_df[yearly_salary >=
                                   masked_df['interpolated_income']]['percentile'].iloc[-1]
            masked_df['selected_income_bracket'] = masked_df['percentile'] == percentile
        except Exception as e:
            pass

    fig = px.bar(
        masked_df,
        x='percentile',
        y='interpolated_income',
        color='selected_income_bracket',
        labels={
            'percentile': "Percentil",
            'interpolated_income': 'Genomsnittlig årsinkomst (tkr)'
        },
        color_discrete_map={
            False: "#A9A9A9",
            True: "#3CB371"
        },
        hover_data={"selected_income_bracket": False}
    )

    fig.update_layout(xaxis={
        'showgrid': False,
        'fixedrange': True,
    },  # TODO: Fix magic number
        yaxis={
            'fixedrange': True,
            'showgrid': False,
            'range': [0, 1500]

    },
        showlegend=False,
        title_text='Genomsnittlig årsinkomst per percentil',
        font_family='Tahoma',
        plot_bgcolor='#E8E8E8',
        paper_bgcolor='#F8F8F8'
    )

    fig.layout.xaxis.fixedrange = True
    fig.layout.yaxis.fixedrange = True
    return fig


def create_income_text(salary_input, df):
    if salary_input:
        try:
            monthly_salary = int(salary_input)
            yearly_salary = monthly_salary/1000*12
        except:
            return html.P('Fyll i siffror')

        income_bracket = df[yearly_salary >=
                            df['min_income']]['income'].iloc[-1]
        df['selected_income_bracket'] = df['income'] == income_bracket

        df_row = df.loc[df['income'] == income_bracket].iloc[0]
        percent_of_people = df_row['percent_of_people']
        percentile = df_row['percentile']

        return html.Div([
            html.P(
                f"Du har en månadslön på {monthly_salary:,d} kr. Det innebär en årslön på {int(yearly_salary):,d} tkr."),
            html.P(f"{round(percent_of_people*100,1)}% av befolkningen i vald grupp tjänar inom spannet {income_bracket} tkr per år. Du tjänar mer än {round(percentile, 1)}% av personer inom vald grupp"),
        ])
    else:
        return html.P('Fyll i din månadslön...')


@app.callback(
    Output('graph-income-text', 'children'),
    Output("graph-income", "figure"),
    Output("graph-percentile", "figure"),
    Input('dropdown-age', 'value'),
    Input('dropdown-gender', 'value'),
    Input("salary-input", "value")
)
def update_page(age_range, gender, salary_input):
    figure_percentile = create_percentile_figure(
        df_interp, age_range, gender, salary_input)
    income_mask = ((df_income['age_range'] == age_range)
                   & (df_income['gender'] == gender))
    df_income_masked = df_income.loc[income_mask].copy()
    income_text = create_income_text(salary_input, df_income_masked)
    figure_income = create_income_figure(df_income_masked)
    return [income_text,  figure_income, figure_percentile]


if __name__ == '__main__':
    app.run_server(debug=True)
