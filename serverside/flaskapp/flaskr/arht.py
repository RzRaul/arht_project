from flask import Flask, render_template, Flask, jsonify
from flask_mysqldb import MySQL
import pandas as pd
import numpy as np
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go

app = Flask(__name__)
app.config['MYSQL_HOST'] = '192.168.1.200'
app.config['MYSQL_USER'] = 'lurker'
app.config['MYSQL_PASSWORD'] = 'LurkPass1'
app.config['MYSQL_DB'] = 'arht_test'
app.config["MYSQL_CUSTOM_OPTIONS"] = {"ssl_mode": 'DISABLED', "ssl":False}  # https://mysqlclient.readthedocs.io/user_guide.html#functions-and-attributes

mysql = MySQL(app)

def get_data():
    cur = mysql.connection.cursor()
    cur.execute('''select * from study_1 where sens_time > "2024-10-28 00:00:00"''')
    data = cur.fetchall()
    cur.close()
    df = pd.DataFrame(data)


@app.route("/")
def index():
    return render_template("index.html")

#debug data
@app.route("/debug_data")
def raw_data():
    cur = mysql.connection.cursor()
    cur.execute('''select * from study_1 where sens_time > "2024-10-28 00:00:00"''')
    data = cur.fetchall()
    cur.close()
    df = pd.DataFrame(data)
    df.columns = ['sens_time','temp_pin17','humidity_pin17','temp_pin19','humidity_pin19','temp_pin23','humidity_pin23','temp_pin32','humidity_pin32','temp_pin33','humidity_pin33','room_name']
    df['sens_time'] = df['sens_time'].dt.strftime('%Y-%m-%d %H:%M')
    df = df.replace(0, np.nan)
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
    temps = fig_temp17.data + fig_temp19.data + fig_temp23.data + fig_temp32.data + fig_temp33.data
    hums =  fig_hum17.data + fig_hum19.data + fig_hum23.data +  fig_hum32.data + fig_hum33.data

    temp_graphJSON = json.dumps(go.Figure(data=temps), cls=plotly.utils.PlotlyJSONEncoder)
    humidity_graphJSON = json.dumps(go.Figure(data=hums), cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template("show_data.html",temp_graphJSON=temp_graphJSON, humidity_graphJSON=humidity_graphJSON)

if __name__ == "__main__":
    app.run(host='0.0.0.0')