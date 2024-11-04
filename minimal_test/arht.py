from flask import Flask, render_template, Flask, jsonify
from flask_mysqldb import MySQL
import datetime
import pandas as pd
import numpy as np
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go

TIME_BETWEEN_MEASURES = datetime.timedelta(minutes=20)

app = Flask(__name__)
# data = ((datetime.datetime(2024, 11, 2, 10, 14, 9), 21.6, 53.1, 20.5, 60.9, 19.7, 57.4, 23.7, 45.0, 20.3, 69.3, 'Bedroom'), (datetime.datetime(2024, 11, 2, 10, 14, 11), 0.0, 0.0, 0.0, 0.0, 20.5, 64.4, 20.9, 66.5, 22.8, 48.0, 'Living+Room'), (datetime.datetime(2024, 11, 2, 10, 34, 8), 21.6, 52.4, 20.8, 59.4, 20.4, 55.1, 22.5, 47.3, 20.6, 67.4, 'Bedroom'), (datetime.datetime(2024, 11, 2, 10, 34, 12), 0.0, 0.0, 0.0, 0.0, 20.6, 63.4, 21.0, 65.7, 22.9, 47.0, 'Living+Room'), (datetime.datetime(2024, 11, 2, 10, 54, 9), 21.7, 51.6, 21.0, 58.5, 20.4, 54.9, 22.3, 48.0, 20.9, 66.6, 'Bedroom'), (datetime.datetime(2024, 11, 2, 10, 54, 11), 0.0, 0.0, 0.0, 0.0, 20.8, 63.0, 21.2, 65.5, 22.9, 47.0, 'Living+Room'), (datetime.datetime(2024, 11, 2, 11, 14, 9), 21.9, 51.6, 21.2, 58.3, 20.7, 55.5, 22.1, 49.2, 21.1, 66.3, 'Bedroom'), (datetime.datetime(2024, 11, 2, 11, 14, 11), 0.0, 0.0, 0.0, 0.0, 21.0, 62.8, 21.3, 65.4, 23.0, 47.0, 'Living+Room'), (datetime.datetime(2024, 11, 2, 11, 34, 9), 22.3, 50.8, 21.7, 57.1, 21.3, 53.5, 22.6, 48.3, 21.4, 65.2, 'Bedroom'), (datetime.datetime(2024, 11, 2, 11, 34, 11), 0.0, 0.0, 0.0, 0.0, 21.2, 62.3, 21.5, 64.9, 23.2, 46.3, 'Living+Room'), (datetime.datetime(2024, 11, 2, 11, 54, 9), 23.3, 50.8, 22.7, 56.3, 21.9, 53.0, 23.3, 49.6, 22.3, 64.7, 'Bedroom'), (datetime.datetime(2024, 11, 2, 11, 54, 11), 0.0, 0.0, 0.0, 0.0, 21.7, 62.2, 22.1, 64.6, 23.5, 46.8, 'Living+Room'), (datetime.datetime(2024, 11, 2, 12, 14, 8), 23.9, 47.4, 23.2, 53.0, 22.6, 50.3, 23.9, 45.1, 22.7, 62.0, 'Bedroom'), (datetime.datetime(2024, 11, 2, 12, 14, 11), 0.0, 0.0, 0.0, 0.0, 22.0, 60.5, 22.5, 63.2, 24.0, 44.9, 'Living+Room'), (datetime.datetime(2024, 11, 2, 12, 34, 9), 24.6, 46.0, 23.9, 51.6, 23.3, 48.2, 24.7, 43.1, 23.3, 61.6, 'Bedroom'), (datetime.datetime(2024, 11, 2, 12, 34, 11), 0.0, 0.0, 0.0, 0.0, 22.5, 60.3, 22.9, 62.8, 24.4, 44.9, 'Living+Room'), (datetime.datetime(2024, 11, 2, 12, 54, 9), 24.7, 46.6, 24.0, 52.5, 23.2, 50.4, 24.6, 45.6, 23.5, 61.1, 'Bedroom'), (datetime.datetime(2024, 11, 2, 12, 54, 12), 0.0, 0.0, 0.0, 0.0, 22.7, 59.5, 23.0, 62.4, 25.2, 42.9, 'Living+Room'), (datetime.datetime(2024, 11, 2, 13, 14, 9), 24.6, 46.9, 23.9, 52.4, 23.1, 51.0, 24.6, 45.5, 23.7, 60.8, 'Bedroom'), (datetime.datetime(2024, 11, 2, 13, 14, 12), 0.0, 0.0, 0.0, 0.0, 22.9, 59.2, 23.1, 62.2, 25.6, 42.2, 'Living+Room'), (datetime.datetime(2024, 11, 2, 13, 34, 9), 24.8, 46.7, 24.2, 52.1, 23.3, 50.4, 24.6, 45.3, 24.0, 60.4, 'Bedroom'), (datetime.datetime(2024, 11, 2, 13, 34, 12), 0.0, 0.0, 0.0, 0.0, 23.1, 59.3, 23.4, 62.4, 25.7, 42.8, 'Living+Room'), (datetime.datetime(2024, 11, 2, 13, 54, 9), 25.2, 45.8, 24.5, 51.4, 23.5, 49.6, 25.1, 44.2, 24.2, 60.1, 'Bedroom'), (datetime.datetime(2024, 11, 2, 13, 54, 12), 0.0, 0.0, 0.0, 0.0, 23.4, 58.8, 23.6, 62.0, 26.0, 42.1, 'Living+Room'), (datetime.datetime(2024, 11, 2, 14, 14, 9), 25.5, 45.6, 24.8, 50.9, 24.0, 48.9, 25.3, 44.6, 24.4, 59.8, 'Bedroom'), (datetime.datetime(2024, 11, 2, 14, 14, 12), 0.0, 0.0, 0.0, 0.0, 23.6, 58.5, 23.8, 61.7, 26.2, 42.1, 'Living+Room'), (datetime.datetime(2024, 11, 2, 14, 34, 9), 25.7, 45.6, 25.0, 50.7, 24.3, 48.5, 25.6, 44.2, 24.6, 59.6, 'Bedroom'), (datetime.datetime(2024, 11, 2, 14, 34, 12), 0.0, 0.0, 0.0, 0.0, 23.8, 58.3, 24.0, 61.5, 26.5, 41.3, 'Living+Room'), (datetime.datetime(2024, 11, 2, 14, 54, 9), 25.6, 45.6, 24.8, 50.8, 23.8, 50.0, 25.5, 44.1, 24.7, 59.4, 'Bedroom'), (datetime.datetime(2024, 11, 2, 14, 54, 12), 0.0, 0.0, 0.0, 0.0, 24.0, 58.1, 24.1, 61.4, 26.7, 41.1, 'Living+Room'), (datetime.datetime(2024, 11, 2, 15, 14, 9), 25.2, 45.7, 24.4, 50.8, 23.3, 50.5, 25.1, 44.7, 24.8, 58.9, 'Bedroom'), (datetime.datetime(2024, 11, 2, 15, 14, 12), 0.0, 0.0, 0.0, 0.0, 24.1, 57.7, 24.2, 61.2, 26.8, 40.6, 'Living+Room'), (datetime.datetime(2024, 11, 2, 15, 34, 9), 24.4, 47.7, 23.9, 52.3, 22.8, 52.6, 24.4, 46.4, 24.7, 59.2, 'Bedroom'), (datetime.datetime(2024, 11, 2, 15, 34, 12), 0.0, 0.0, 0.0, 0.0, 24.1, 57.7, 24.0, 61.7, 26.7, 40.7, 'Living+Room'))

fig_comb= go.Figure()
df = pd.read_csv("data.csv")
df['sens_time'] = pd.to_datetime(df['sens_time'])
df['sens_time'] = df['sens_time'].dt.strftime('%Y-%m-%d %H:%M')
df = df.replace(0, np.nan)
df = df.loc[(df['sens_time'] >= '2024-10-28 00:00')]
fig_temp17 = px.line(df, x='sens_time', y='temp_pin17', color='room_name')
fig_temp19 = px.line(df, x='sens_time', y='temp_pin19', color='room_name')
fig_temp23 = px.line(df, x='sens_time', y='temp_pin23', color='room_name')
fig_temp32 = px.line(df, x='sens_time', y='temp_pin32', color='room_name')
fig_temp33 = px.line(df, x='sens_time', y='temp_pin33', color='room_name')
fig_hum17 = px.line(df, x='sens_time', y='humidity_pin17', color='room_name')
fig_hum19 = px.line(df, x='sens_time', y='humidity_pin19', color='room_name')
fig_hum23 = px.line(df, x='sens_time', y='humidity_pin23', color='room_name')
fig_hum32 = px.line(df, x='sens_time', y='humidity_pin32', color='room_name')
fig_hum33 = px.line(df, x='sens_time', y='humidity_pin33', color='room_name')


def get_data():
    pass
    

@app.route("/")
def index():
    return render_template("index.html")

#debug data
@app.route("/debug_data")
def display_data():
    # print(df.describe())
    global df
  
    # fig = px.line(df, x='sens_time', y='temp1', color='name')
    # fig2 = px.line(df, x='sens_time', y='temp2', color='name')
    # fig3 = px.line(df, x='sens_time', y='temp3', color='name')
    # fig4 = px.line(df, x='sens_time', y='temp4', color='name')
    # fig5 = px.line(df, x='sens_time', y='temp5', color='name')

    # fig6 = go.Figure(data=fig3.data+fig4.data+fig5.data)
    temps = fig_temp17.data + fig_temp19.data + fig_temp23.data + fig_temp32.data + fig_temp33.data
    hums =  fig_hum17.data + fig_hum19.data + fig_hum23.data +  fig_hum32.data + fig_hum33.data
    # fig6 = go.Figure(data=fig3.data+fig4.data+fig5.data)
    fig_comb= go.Figure(data=temps)
    # fig.add_lin
    # fig.add_scatter(x=df['sens_time'], y=df[df['name']=='Bedroom']['temp1'], name="temp1")
    # fig.add_scatter(x=df['sens_time'], y=df[df['name']=='Bedroom']['temp2'], name="temp2")
    # fig.add_scatter(x=df['sens_time'], y=df[df['name']=='Bedroom']['temp3'], name="temp3")
    # fig.add_scatter(x=df['sens_time'], y=df[df['name']=='Bedroom']['temp4'], name="temp4")
    # fig.add_scatter(x=df['sens_time'], y=df[df['name']=='Bedroom']['temp5'], name="temp5")
    # fig.add_scatter(x=df['sens_time'], y=df.query('name==Living+Room')['temp3'], name="temp3", color='name')
    # fig.add_scatter(x=df['sens_time'], y=df.query('name==Living+Room')['temp4'], name="temp4", color='name')
    # fig.add_scatter(x=df['sens_time'], y=df['temp4'], name="temp4", color='name')
    # fig.add_scatter(x=df['sens_time'], y=df['temp5'], name="temp5", color='name')
    # print(df)
    # fig.add_trace(go.Scatter(x=df['sens_time'], y=df['temp4'], name="temp4", mode="lines+markers", line=dict(color='royalblue', width=4)))
    # fig.add_trace(go.Scatter(x=df['sens_time'], y=df['temp5'], name="temp5", line=dict(color='red', width=4)))
    # fig = px.bar(df, x='sens_time', y='temp1', color='name')
     
    # Create graphJSON
    graphJSON = json.dumps(fig_comb, cls=plotly.utils.PlotlyJSONEncoder)
     
    # Use render_template to pass graphJSON to html
    return render_template("show_data.html",graphJSON=graphJSON)


if __name__ == "__main__":
    get_data()
    app.run(host='0.0.0.0')