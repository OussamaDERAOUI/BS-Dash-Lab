import bs4
import requests
import time
import random as ran
import pandas as pd

import plotly.express as px

import dash
from dash import dash_table,dcc,html
from dash.dependencies import Input, Output


def scrape_mblock(movie_block):
    movieb_data = {}

    try:
        movieb_data['name'] = movie_block.find('a').get_text()  # Name of the movie
    except:
        movieb_data['name'] = None

    try:
        movieb_data['year'] = str(
            movie_block.find('span', {'class': 'lister-item-year'}).contents[0][1:-1])  # Release year
    except:
        movieb_data['year'] = None

    try:
        movieb_data['rating'] = float(
            movie_block.find('div', {'class': 'inline-block ratings-imdb-rating'}).get('data-value'))  # rating
    except:
        movieb_data['rating'] = None

    try:
        movieb_data['m_score'] = float(
            movie_block.find('span', {'class': 'metascore favorable'}).contents[0].strip())  # meta score
    except:
        movieb_data['m_score'] = None

    try:
        movieb_data['votes'] = int(movie_block.find('span', {'name': 'nv'}).get('data-value'))  # votes
    except:
        movieb_data['votes'] = None

    return movieb_data


def scrape_m_page(movie_blocks):
    page_movie_data = []
    num_blocks = len(movie_blocks)

    for block in range(num_blocks):
        page_movie_data.append(scrape_mblock(movie_blocks[block]))

    return page_movie_data


def scrape_this(link, t_count):
    # from IPython.core.debugger import set_trace

    base_url = link
    target = t_count

    current_mcount_start = 0
    current_mcount_end = 0
    remaining_mcount = target - current_mcount_end

    new_page_number = 1

    movie_data = []

    while remaining_mcount > 0:
        url = base_url + str(new_page_number)

        # set_trace()

        source = requests.get(url).text
        soup = bs4.BeautifulSoup(source, 'html.parser')

        movie_blocks = soup.findAll('div', {'class': 'lister-item-content'})

        movie_data.extend(scrape_m_page(movie_blocks))

        current_mcount_start = int(
            soup.find("div", {"class": "nav"}).find("div", {"class": "desc"}).contents[1].get_text().split("-")[0])

        current_mcount_end = int(
            soup.find("div", {"class": "nav"}).find("div", {"class": "desc"}).contents[1].get_text().split("-")[
                1].split(" ")[0])

        remaining_mcount = target - current_mcount_end

        print('\r' + "currently scraping movies from: " + str(current_mcount_start) + " - " + str(current_mcount_end),
              "| remaining count: " + str(remaining_mcount), flush=True, end="")

        new_page_number = current_mcount_end + 1

        time.sleep(ran.randint(0, 10))

    return movie_data

def scrap_data(top_movies,base_scraping_link):
    films = []
    films = scrape_this(base_scraping_link,int(top_movies))
    df = pd.DataFrame(films)
    df['year'] = df['year'].str.slice(0, 4)
    valid_years = ['2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023']
    df = df[df['year'].isin(valid_years)]
    df['m_score'] = df['m_score'].fillna(0)
    return df

base_scraping_link = "https://www.imdb.com/search/title/?release_date=2016-01-01,2023-01-05&sort=boxoffice_gross_us,desc&start=0"
top_movies = 50
df = scrap_data(top_movies,base_scraping_link)

# Initializing the app
app = dash.Dash(__name__)
server = app.server

# Building the app layout
app.layout = html.Div([
    html.H1("IMDB Dashboard", style={"text-align": "center"}),
    html.Br(),
    html.Div([
        html.Br(),
        html.H2("IMDB Movies dataset (2016-2023)", style={"text-align": "center"}),
        html.Br(),
        dash_table.DataTable(data=df.to_dict('records'), page_size=10)]),
    html.Div([
        html.Br(),
        html.H2("Top 5-50 movies by Rating/Metascore/Voting", style={"text-align": "center"}),
        html.Br(),
        dcc.Dropdown(id='metric-dropdown',
                     options=[
                         dict(label="Rating", value="rating"),
                         dict(label="Metascore", value="m_score"),
                         dict(label="Voting", value="votes")],
                     multi=False,
                     value="rating",
                     style={"width": "50%", 'display': 'inline-block'}
                     ),
        dcc.Dropdown(id='num-bars-dropdown',
                     options=[
                         dict(label="Top 5", value=5),
                         dict(label="Top 10", value=10),
                         dict(label="Top 25", value=25),
                         dict(label="Top 50", value=50)],
                     style={"width": "50%", 'display': 'inline-block'},
                     value=10),
        dcc.Graph(id='bar-chart'),
        html.Br(),
        html.H2("Total Number of Movies Grouped by Year", style={"text-align": "center"}),
        html.Br(),
        dcc.Graph(id='pie-chart')
        ,html.Br(),
html.H2("Average scores by Year", style={"text-align": "center"}),
html.Br(),
dcc.RadioItems(
    id='radio-chart',
    options=[
        {'label': 'Rating', 'value': 'rating'},
        {'label': 'Voting', 'value': 'votes'},
        {'label': 'Metascore', 'value': 'm_score'}
    ],
    value='rating',
    labelStyle={'display': 'block', 'margin': '10px'}
),
dcc.Graph(id='radio-chart-output')

    ])
])

@app.callback(
    output=Output('bar-chart', 'figure'),
    inputs=[Input('metric-dropdown', 'value'), Input('num-bars-dropdown', 'value')]
)

def update_bar_chart(metric, num_bars):
    sorted_df = df.sort_values(by=metric, ascending=False).head(num_bars)
    fig = px.bar(sorted_df, x='name', y=metric, color=metric)
    return fig

@app.callback(
    output=Output('pie-chart', 'figure'),
    inputs=[Input('metric-dropdown', 'value')]
)
def update_pie_chart(metric):
    grouped_df = df.groupby('year').size().reset_index(name='Count')
    fig = px.pie(grouped_df, values='Count', names='year',color_discrete_sequence=px.colors.qualitative.Pastel)
    return fig
@app.callback(
    output=Output('radio-chart-output', 'figure'),
    inputs=[Input('radio-chart', 'value')]
)
def update_radio_chart(option):
    if option == 'rating':
        chart_data = df.groupby('year')['rating'].mean().reset_index()
        chart_title = 'Average Rating by Year'
        x_label = 'year'
        y_label = 'rating'
    elif option == 'votes':
        chart_data = df.groupby('year')['votes'].sum().reset_index()
        chart_title = 'Average Voting by Year'
        x_label = 'year'
        y_label = 'votes'
    elif option == 'm_score':
        chart_data = df.groupby('year')['m_score'].mean().reset_index()
        chart_title = 'Average Metascore by Year'
        x_label = 'year'
        y_label = 'm_score'
    print(chart_data)
    fig = px.bar(chart_data, x=x_label,y=chart_data[y_label], color_discrete_sequence=px.colors.qualitative.Pastel  )
    fig.update_layout(title=chart_title)
    return fig

if __name__ == "__main__":
    app.run_server()