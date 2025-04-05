# main.py

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import plotly.graph_objects as go
# Load dataset
postings = pd.read_csv("/Users/nithyareddybilla/Downloads/archive (5)/postings.csv")
skills = pd.read_csv("/Users/nithyareddybilla/Downloads/archive (5)/mappings/skills.csv")
job_skills = pd.read_csv("/Users/nithyareddybilla/Downloads/archive (5)/jobs/job_skills.csv")

# --- Preprocessing ---

# Top 10 Job Titles
top_jobs = postings['title'].value_counts().head(10).reset_index()
top_jobs.columns = ['Job Title', 'Count']

# Average salary pie chart
salary_df = postings.dropna(subset=["max_salary", "med_salary", "min_salary"])
salary_summary = salary_df[["max_salary", "med_salary", "min_salary"]].mean()

# --- US State Job Distribution ---
us_jobs = postings[(postings['location'].str.contains('United States|USA|US|U.S.', na=False)) |
                   (postings['location'].str.contains(', [A-Z]{2}', na=False))]
us_jobs = us_jobs[~us_jobs['location'].isna()]
us_jobs['state'] = us_jobs['location'].str.extract(r',\s*([A-Z]{2})')
state_counts = us_jobs['state'].value_counts().reset_index()
state_counts.columns = ['state', 'job_count']


# Word Cloud for Skills
merged_skills = job_skills.merge(skills, on='skill_abr', how='left')
skill_string = ' '.join(merged_skills['skill_abr'].dropna())
wordcloud = WordCloud(width=800, height=400, background_color='white').generate(skill_string)
buf = BytesIO()
plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
plt.tight_layout()
plt.savefig(buf, format="png")
plt.close()
wordcloud_img = base64.b64encode(buf.getvalue()).decode()

# Grouped salary by work type & remote
postings['remote_allowed'] = postings['remote_allowed'].map({0.0: 'Non-Remote', 1.0: 'Remote'})
grouped_salaries = postings.groupby(['formatted_work_type', 'remote_allowed'])['med_salary'].mean().unstack()

# Average salary by state
state_salary = postings.groupby(postings['location'].str.extract(r',\s*(\w+)$')[0])['med_salary'].mean().nlargest(10).reset_index()
state_salary.columns = ['State', 'Average Salary']

# Country job count (simplified to use US only if location column not ideal)
postings['country'] = postings['location'].str.extract(r',\s*(\w+)$')
country_jobs = postings['country'].value_counts().head(10).reset_index()
country_jobs.columns = ['Country', 'Number of Jobs']
# --- Sunburst Hierarchy Preprocessing ---
geo_df = postings.dropna(subset=['location'])

# Extract city and state from location (e.g., "Dallas, TX")
geo_df[['city', 'state']] = geo_df['location'].str.extract(r'^([^,]+),\s*([A-Z]{2})')
geo_df['country'] = 'United States'  # Static for now

# Group by country > state > city
grouped_geo = geo_df.groupby(['country', 'state', 'city']).size().reset_index(name='job_count')
# --- Industry Company Count Analysis ---
companies = pd.read_csv("/Users/nithyareddybilla/Downloads/archive (5)/companies/companies.csv")
company_industries = pd.read_csv("/Users/nithyareddybilla/Downloads/archive (5)/companies/company_industries.csv")
industries = pd.read_csv("/Users/nithyareddybilla/Downloads/archive (5)/mappings/industries.csv")

# For safety, print structure if needed
print("company_industries columns:", company_industries.columns)
print("industries columns:", industries.columns)

# Count top industries by company appearance
top_industries = company_industries['industry'].value_counts().head(10).reset_index()
top_industries.columns = ['Industry', 'Company Count']

# --- Top 10 In-Demand Skills ---
skills_df = job_skills.merge(skills, on="skill_abr", how="left")
top_skills = skills_df['skill_name'].value_counts().head(10).reset_index()
top_skills.columns = ['Skill', 'Job Count']

# --- Top Skills by State ---
job_skills = pd.read_csv("/Users/nithyareddybilla/Downloads/archive (5)/jobs/job_skills.csv")
skills = pd.read_csv("/Users/nithyareddybilla/Downloads/archive (5)/mappings/skills.csv")

# Extract state from location
postings['state'] = postings['location'].str.extract(r',\s*([A-Z]{2})$')

# Merge postings with job_skills
job_post_skills = postings[['job_id', 'state']].merge(job_skills, on='job_id', how='left')

# Merge with skill names
full_data = job_post_skills.merge(skills, on='skill_abr', how='left')

# Count each skill by state
skill_counts_by_state = full_data.groupby(['state', 'skill_abr']).size()

# Get top 10 skills per state
top_skills_by_state = skill_counts_by_state.groupby(level=0).nlargest(10).reset_index(level=0, drop=True).reset_index(name='count')

# Set default state (can turn this into dropdown later)
state = 'NC'
top_skills_in_state = top_skills_by_state[top_skills_by_state['state'] == state]



# --- Dash App ---
app = dash.Dash(__name__)

app.layout = html.Div([
   html.H1("The Hiring Pulse: Job Market Analysis & Dynamic Dashboard", 
        style={
            'textAlign': 'center',
            'color': '#2c3e50',
            'marginBottom': '30px',
            'fontFamily': 'Helvetica, Arial, sans-serif'
        }),

    html.Div([
        dcc.Graph(
            figure=px.bar(
                top_industries,
                x='Industry',
                y='Company Count',
                title="🏢 Top 10 Industries by Number of Companies",
                text='Company Count',
                color='Company Count',
                color_continuous_scale='Purples'  # Optional: Try 'Blues', 'Sunset', etc.
            ).update_layout(xaxis_tickangle=-45)
        )
        ], style={'padding': '20px 0'}),
    html.Div([
        dcc.Graph(
            figure=px.bar(
                top_skills,
                x='Skill',
                y='Job Count',
                title="🚀 Top 10 In-Demand Skills in Job Postings",
                text='Job Count',
                color='Job Count',
                color_continuous_scale='Tealgrn'  # Optional: Try 'Blues', 'Plasma', 'Sunset'
            ).update_layout(xaxis_tickangle=-45)
        )
    ], style={'padding': '20px 0'}),


    html.Div([
        html.Div([
            dcc.Graph(
            figure=px.choropleth(
                state_counts,
                locations='state',
                locationmode="USA-states",
                color='job_count',
                scope="usa",
                color_continuous_scale="Sunset",  # 🔁 Feel free to swap to 'Plasma', 'Cividis', etc.
                title="Jobs Distribution by State in the United States"
            )
        )
        ], className='six columns'),
    ], className='row'),

    html.Div([
        html.Div([
            html.Img(src='data:image/png;base64,{}'.format(wordcloud_img),
                     style={'width': '100%', 'height': '400px'})
        ], className='six columns'),
    ], className='row'),

    html.Div([
        dcc.Graph(
        figure=go.Figure(
            data=[
                go.Bar(name=col, x=grouped_salaries.index, y=grouped_salaries[col])
                for col in grouped_salaries.columns
            ],
            layout=go.Layout(
                title="Average Median Salary by Work Type and Remote Allowance",
                xaxis_title="Work Type",
                yaxis_title="Average Median Salary",
                barmode='group'
            )
        )
    )

    ]),
    html.Div([
    dcc.Graph(
        figure=px.sunburst(
            grouped_geo,
            path=['country', 'state', 'city'],
            values='job_count',
            title="🌐 Global Job Opportunities Sunburst: From Country to City",
            height=600
        )
    )
    ], style={'padding': '20px 0'}),

    html.Div([
        html.Div([
            dcc.Graph(
                figure=px.bar(
                    top_skills_in_state,
                    x='skill_abr',
                    y='count',
                    title=f"Top 10 Skills in Demand in {state}",
                    labels={'skill_abr': 'Skill', 'count': 'Job Count'},
                    color='count',
                    color_continuous_scale='Blues'
                ).update_layout(xaxis_tickangle=45)
            )
            ], style={'width': '48%', 'display': 'inline-block', 'padding': '0 1%'}),


        html.Div([
            dcc.Graph(
                figure=px.bar(
                    state_salary, 
                    x='State', 
                    y='Average Salary', 
                    title='Top 10 States with Highest Average Salary',
                    color_discrete_sequence=['#EF553B']
                )
            )
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '0 1%'})
    ]),

])

if __name__ == '__main__':
    app.run(debug=True)

