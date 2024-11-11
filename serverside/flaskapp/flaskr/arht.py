from flask import Flask, render_template, Flask, jsonify
from flask_mysqldb import MySQL
import pandas as pd
import numpy as np
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go
from scipy.interpolate import Rbf

app = Flask(__name__)
app.config['MYSQL_HOST'] = '192.168.1.200'
app.config['MYSQL_USER'] = 'lurker'
app.config['MYSQL_PASSWORD'] = 'LurkPass1'
app.config['MYSQL_DB'] = 'arht_prod'
app.config["MYSQL_CUSTOM_OPTIONS"] = {"ssl_mode": 'DISABLED', "ssl":False}  # https://mysqlclient.readthedocs.io/user_guide.html#functions-and-attributes

mysql = MySQL(app)

def generate_heatmap_figure(M, points, temperatures):
    grid_x, grid_y = np.meshgrid(np.linspace(0, M-1, M), np.linspace(0, M-1, M))
    known_points = np.array(points)
    known_temperatures = np.array(temperatures)

    rbf = Rbf(known_points[:, 0], known_points[:, 1], known_temperatures, function='multiquadric')
    grid_temperatures = rbf(grid_x, grid_y)

    temperature_grid = grid_temperatures.reshape(M, M)
    figure = go.Figure(data=go.Heatmap(
        z=temperature_grid,
        colorscale='Turbo',
        colorbar=dict(title='Temperature (°C)', tickvals=[5, 30], ticktext=['5°C', '30°C']),
    ))

    figure.update_layout(
        title='Temperature Distribution',
        xaxis_title='X Coordinate',
        yaxis_title='Y Coordinate',
        coloraxis=dict(cmin=5, cmax=30)
    )

    return figure

def create_heatmap_data(M, points, temperatures):
    # Create an empty MxM grid
    grid_x, grid_y = np.meshgrid(np.arange(M), np.arange(M))
    grid_x = grid_x.flatten()
    grid_y = grid_y.flatten()

    # Known points and their temperatures
    known_points = np.array(points)
    known_temperatures = np.array(temperatures)

    # Perform interpolation (using 'cubic' for smooth gradients)
    grid_temperatures = griddata(known_points, known_temperatures, (grid_x, grid_y), method='cubic')

    # Reshape the output into the grid shape
    temperature_grid = grid_temperatures.reshape(M, M)

    # Prepare the data to be serialized into JSON
    data = {
        'M': M,
        'temperature_grid': temperature_grid.tolist(),  # Convert the numpy array to a list
        'points': points,
        'temperatures': temperatures
    }

    # Convert to JSON
    json_data = json.dumps(data)
    return json_data

with app.app_context():
    global temp_graphJSON, humidity_graphJSON, heatmap_data, df

    cur = mysql.connection.cursor()
    cur.execute('''select * from measurements where sens_time > "2024-10-28 00:00:00"''')
    data = cur.fetchall()
    cur.close()
    # df = pd.read_csv("study_1001.csv")
    # df['sens_time'] = pd.to_datetime(df['sens_time'])
    df = pd.DataFrame(data)
    df.columns = ['sens_time','room_name','id_study','temp_pin17','humidity_pin17','temp_pin19','humidity_pin19','temp_pin23','humidity_pin23','temp_pin32','humidity_pin32','temp_pin33','humidity_pin33']
    df['sens_time'] = df['sens_time'].dt.strftime('%Y-%m-%d %H:%M')
    df.drop(columns=['id_study'], inplace=True)
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

    M = 21  # Example for a 10x10 grid
    points = [(20,5),(20,15),(13,10),(20,10),(10,0),(0,5),(4,2),(6,10),(4,20),(1,13)]
    cols1 = ['time','20,5','20,15','13,10','20,10','10,0']
    cols2 = ['0,5','4,2','6,10','4,20','1,13']
    df1 = df[df['room_name']=="Bedroom"]
    df2 = df[df['room_name']!="Bedroom"]
    df1 = df1.drop(columns=['room_name','humidity_pin17','humidity_pin19','humidity_pin23','humidity_pin32','humidity_pin33'])
    df2 = df2.drop(columns=['sens_time','room_name','humidity_pin17','humidity_pin19','humidity_pin23','humidity_pin32','humidity_pin33'])
    # df = df.iloc[::15,:]
    df1.columns = cols1
    df2.columns = cols2
    df1.reset_index(inplace=True, drop=True)
    df2.reset_index(inplace=True, drop=True)
    # Assuming `df_test` contains the subset you want to display
    df_merged = pd.concat([df1, df2], axis=1, join='outer')
    df_test = df_merged.iloc[10]
    temperatures = list(df_test.iloc[1:])
    figure = generate_heatmap_figure(M, points, temperatures)  # M = 21 for grid size
    figure_json = plotly.io.to_json(figure, pretty=True)
    
    # # Create heatmap figures for each snapshot and serialize them to JSON
    # temperatures_data = []
    # for index, snap in df_test.iterrows():
    #     temperatures = list(snap.iloc[1:])
    #     figure = generate_heatmap_figure(M, points, temperatures)  # M = 21 for grid size
    #     figure_json = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)
    #     temperatures_data.append({
    #         'time': snap['time'],  # Include timestamp
    #         'graph': figure_json
    #     })

    heatmap_data = figure_json


@app.route("/")
def index():
    return render_template("index.html")

#debug data
@app.route("/debug_data_custom")
def raw_data():
    cur = mysql.connection.cursor()
    cur.execute('''select * from measurements where sens_time > "2024-10-28 00:00:00"''')
    data = cur.fetchall()
    cur.close()
    df = pd.DataFrame(data)
    
    df.columns = ['sens_time','room_name','id_study','temp_pin17','humidity_pin17','temp_pin19','humidity_pin19','temp_pin23','humidity_pin23','temp_pin32','humidity_pin32','temp_pin33','humidity_pin33']
    df['sens_time'] = df['sens_time'].dt.strftime('%Y-%m-%d %H:%M')
    df.drop(columns=['id_study'], inplace=True)
    df = df.replace(0, np.nan)
    print(df.head(20))
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

@app.route("/debug_data")
def get_data_cached():
       return render_template("show_data.html",temp_graphJSON=temp_graphJSON, humidity_graphJSON=humidity_graphJSON)


@app.route("/heatmap")
def heatmap_site():
    
    return render_template("show_data.html", heat_graphJSON=heatmap_data)

@app.route('/heatmap_data')
def heatmap_data():
    M = 21  # Example for a 10x10 grid
    points = [(20,5),(20,15),(13,10),(20,10),(10,0),(0,5),(4,2),(6,10),(4,20),(1,13)]
    cols1 = ['time','20,5','20,15','13,10','20,10','10,0']
    cols2 = ['0,5','4,2','6,10','4,20','1,13']
    df = pd.read_csv("study_1001.csv")
    df['sens_time'] = pd.to_datetime(df['sens_time'])
    df['sens_time'] = df['sens_time'].dt.strftime('%Y-%m-%d %H:%M')
    df = df.replace(0, np.nan)
    df1 = df[df['room_name']=="Bedroom"]
    df2 = df[df['room_name']!="Bedroom"]
    df1 = df1.drop(columns=['id_study','room_name','humidity_pin17','humidity_pin19','humidity_pin23','humidity_pin32','humidity_pin33'])
    df2 = df2.drop(columns=['sens_time','id_study','room_name','humidity_pin17','humidity_pin19','humidity_pin23','humidity_pin32','humidity_pin33'])
    # df = df.iloc[::15,:]
    df1.columns = cols1
    df2.columns = cols2
    df1.reset_index(inplace=True, drop=True)
    df2.reset_index(inplace=True, drop=True)
    # Assuming `df_test` contains the subset you want to display
    df_merged = pd.concat([df1, df2], axis=1, join='outer')
    df_test = df_merged.iloc[::2,:]
    
    # For each time snapshot, get the temperature data
    temperatures_data = []
    for index, snap in df_test.iterrows():
        temperatures = list(snap.iloc[1:])
        heatmap = generate_heatmap_figure(M, points, temperatures)  # M = 21 for grid size
        temperatures_data.append({
            'time': snap['time'],  # Include timestamp
            'data': heatmap
        })
    
    return render_template("show_data.html",temp_graphJSON=temp_graphJSON, humidity_graphJSON=humidity_graphJSON, heat_graphJSON=temperatures_data)

if __name__ == "__main__":
    app.run(host='0.0.0.0')