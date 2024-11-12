from flask import Flask, request, render_template, Flask, jsonify
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

@app.route('/api/temp_graph')
def get_temp_graph():
    # This should fetch temperature data from your database
    temp_graph_data = {
        "data": [
            {"x": [1, 2, 3], "y": [10, 11, 12], "type": "scatter", "mode": "lines+markers"}
        ],
        "layout": {"title": "Temperature Graph"}
    }
    return jsonify(temp_graph_data)

@app.route('/api/humidity_graph')
def get_humidity_graph():
    # Fetch humidity data from the database
    humidity_graph_data = {
        "data": [
            {"x": [1, 2, 3], "y": [50, 60, 70], "type": "scatter", "mode": "lines+markers"}
        ],
        "layout": {"title": "Humidity Graph"}
    }
    return jsonify(humidity_graph_data)

@app.route('/api/heatmap_data')
def get_heatmap_data():
    # Fetch heatmap data from the database
    heatmap_data = {
        "data": [
            {"z": [[1, 2], [3, 4]], "type": "heatmap"}
        ],
        "layout": {"title": "Heatmap", "yaxis": {"autorange": "reversed"}}
    }
    return jsonify(heatmap_data)

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
        colorbar=dict(title='Temperature (°C)', tickvals=[8, 30], ticktext=['8°C', '30°C']),
    ))

    figure.update_layout(
        title='Temperature Distribution',
        xaxis_title='X Coordinate',
        yaxis_title='Y Coordinate',
        coloraxis=dict(cmin=8, cmax=30)
    )

    return figure

with app.app_context():
    global temp_graphJSON, humidity_graphJSON, heatmap_data, df

    cur = mysql.connection.cursor()
    cur.execute('''select * from measurements where sens_time > "2024-10-28 00:00:00"''')
    data = cur.fetchall()
    cur.close()
    # df = pd.read_csv("study_1001.csv")
    # df['sens_time'] = pd.to_datetime(df['sens_time'])
    df = pd.DataFrame(data)
    df.columns = ['sens_time','room_name','id_study','temperature_S1','humidity_S1','temperature_S2','humidity_S2','temperature_S3','humidity_S3','temperature_S4','humidity_S4','temperature_S5','humidity_S5']
    df['sens_time'] = df['sens_time'].dt.strftime('%Y-%m-%d %H:%M')
    df.drop(columns=['id_study'], inplace=True)
    df = df.replace(0, np.nan)
    df_melted_temp = df.melt(id_vars=['sens_time', 'room_name'], 
                    value_vars=['temperature_S1', 'temperature_S2', 'temperature_S3', 'temperature_S4', 'temperature_S5'],
                    var_name='sensor', value_name='temperature')
    
    df_melted_hum = df.melt(id_vars=['sens_time', 'room_name'], 
                    value_vars=['humidity_S1', 'humidity_S2', 'humidity_S3', 'humidity_S4', 'humidity_S5'],
                    var_name='sensor', value_name='humidity')

    fig_temp = px.line(df_melted_temp, 
                    x='sens_time', 
                    y='temperature', 
                    color='room_name',  # Color by room_name to separate rooms
                    symbol='sensor', # Separate lines by sensor for each room
                        markers=False,
                    title='Temperature Over Time')

    fig_temp.update_layout(
        legend_title='Room and Sensor',  # Custom title for the legend
        xaxis_title='Time',     # Label for the X-axis
        yaxis_title='Temperature (°C)',  # Label for the Y-axis
        legend=dict(
            title="Room and Sensor",     # Title for the legend
            traceorder='normal', # Ensures the order of the traces matches the color scale
            
        )
    )
    
    fig_hum = px.line(df_melted_hum, 
                    x='sens_time', 
                    y='humidity', 
                    color='room_name',  # Color by room_name to separate rooms
                    symbol='sensor', # Separate lines by sensor for each room
                    markers=False,
                    title='Humidity Over Time')
    
    fig_hum.update_layout(
        legend_title='Room and Sensor',  # Custom title for the legend
        xaxis_title='Time',     # Label for the X-axis
        yaxis_title='Humidity (%)',  # Label for the Y-axis
        legend=dict(
            title="Room and Sensor",     # Title for the legend
            traceorder='normal', # Ensures the order of the traces matches the color scale
            
        )
    )

    temps = fig_temp.data
    hums =  fig_hum.data
    # temps = fig_temp17.data + fig_temp19.data + fig_temp23.data + fig_temp32.data + fig_temp33.data
    # hums =  fig_hum17.data + fig_hum19.data + fig_hum23.data +  fig_hum32.data + fig_hum33.data

    temp_graphJSON = json.dumps(go.Figure(data=temps), cls=plotly.utils.PlotlyJSONEncoder)
    humidity_graphJSON = json.dumps(go.Figure(data=hums), cls=plotly.utils.PlotlyJSONEncoder)

    M = 21  # Example for a 10x10 grid
    points = [(20,5),(20,15),(13,10),(20,10),(10,0),(0,5),(4,2),(6,10),(4,20),(1,13)]
    cols1 = ["time","20,5","20,15","13,10","20,10","10,0"]
    cols2 = ["0,5","4,2","6,10","4,20","1,13"]
    cols1 = ['time','20,5','20,15','13,10','20,10','10,0']
    cols2 = ['0,5','4,2','6,10','4,20','1,13']
    df1 = df[df['room_name']=="Bedroom"]
    df2 = df[df['room_name']!="Bedroom"]
    df1 = df1.drop(columns=['room_name','humidity_S1','humidity_S2','humidity_S3','humidity_S4','humidity_S5'])
    df2 = df2.drop(columns=['sens_time','room_name','humidity_S1','humidity_S2','humidity_S3','humidity_S4','humidity_S5'])
    # df = df.iloc[::15,:]
    df1.columns = cols1
    df2.columns = cols2
    df1.reset_index(inplace=True, drop=True)
    df2.reset_index(inplace=True, drop=True)
    # Assuming `df_test` contains the subset you want to display
    df_merged = pd.concat([df1, df2], axis=1, join='outer')
    df_merged.interpolate(method='linear', limit_direction='forward', axis=0, inplace=True)
    df_test = df_merged
    # # Create heatmap figures for each snapshot and serialize them to JSON
    temperatures_data = []
    for index, snap in df_test.iterrows():
        temperatures = list(snap.iloc[1:])
        figure = generate_heatmap_figure(M, points, temperatures)  # M = 21 for grid size
        figure_json = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)
        temperatures_data.append({
            'time': snap['time'],  # Include timestamp
            'graph': figure_json
        })

    heatmap_data = temperatures_data


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
    
    df.columns = ['sens_time','room_name','id_study','temperature_S1','humidity_S1','temperature_S2','humidity_S2','temperature_S3','humidity_S3','temperature_S4','humidity_S4','temperature_S5','humidity_S5']
    df['sens_time'] = df['sens_time'].dt.strftime('%Y-%m-%d %H:%M')
    df.drop(columns=['id_study'], inplace=True)
    df = df.replace(0, np.nan)
    print(df.head(20))
    fig_temp = px.line(df, x='sens_time', y=['temperature_S1','temperature_S2','temperature_S3','temperature_S4','temperature_S5']
                         , color='room_name'
                         ,)
    fig_hum = px.line(df, x='sens_time', y=['humidity_S1', 'humidity_S2','humidity_S3','humidity_S4','humidity_S5'], color='room_name', symbols=['humidity_S1', 'humidity_S2','humidity_S3','humidity_S4','humidity_S5'])
    temps = fig_temp.data
    hums =  fig_hum.data

    temp_graphJSON = json.dumps(go.Figure(data=temps), cls=plotly.utils.PlotlyJSONEncoder)
    humidity_graphJSON = json.dumps(go.Figure(data=hums), cls=plotly.utils.PlotlyJSONEncoder)
    
    return render_template("show_data.html",temp_graphJSON=temp_graphJSON, humidity_graphJSON=humidity_graphJSON)

@app.route("/debug_data")
def get_data_cached():
       return render_template("show_data.html",temp_graphJSON=temp_graphJSON, humidity_graphJSON=humidity_graphJSON)


@app.route("/heatmap")
def heatmap_site():
    
    return render_template("show_data.html",temp_graphJSON=temp_graphJSON, humidity_graphJSON=humidity_graphJSON, heat_graphJSON=heatmap_data)

@app.route("/graphs")
def show_all_graphs():
    
    return render_template("show_graphs.html",temp_graphJSON=temp_graphJSON, humidity_graphJSON=humidity_graphJSON, heat_graphJSON=heatmap_data)


@app.route("/temperature")
def get_temp_by():
    get_by = request.args.get("get_by")
    from_date = request.args.get("from")
    till_date = request.args.get("till")
    study_id = request.args.get("study_id")
    print(f"get->{get_by}  from->{from_date} till->{till_date}")
    cur = mysql.connection.cursor()
    cur.execute(f'''select room_name from measurements where id_study={int(study_id)};''')
    data = cur.fetchall()

    if (get_by == "sensor"):
        cur.execute('''select * from measurements where sens_time > "2024-10-28 00:00:00"''')

    data = cur.fetchall()
    cur.close()
    return render_template("index.html") 
# @app.route('/heatmap_data')
# def heatmap_data_func():
#     M = 21  # Example for a 10x10 grid
#     points = [(20,5),(20,15),(13,10),(20,10),(10,0),(0,5),(4,2),(6,10),(4,20),(1,13)]
#     cols1 = ['time','20,5','20,15','13,10','20,10','10,0']
#     cols2 = ['0,5','4,2','6,10','4,20','1,13']
#     # df = pd.read_csv("study_1001.csv")
#     df['sens_time'] = pd.to_datetime(df['sens_time'])
#     df['sens_time'] = df['sens_time'].dt.strftime('%Y-%m-%d %H:%M')
#     df = df.replace(0, np.nan)
#     df1 = df[df['room_name']=="Bedroom"]
#     df2 = df[df['room_name']!="Bedroom"]
#     df1 = df1.drop(columns=['id_study','room_name','humidity_S1','humidity_S2','humidity_S3','humidity_S4','humidity_S5'])
#     df2 = df2.drop(columns=['sens_time','id_study','room_name','humidity_S1','humidity_S2','humidity_S3','humidity_S4','humidity_S5'])
#     # df = df.iloc[::15,:]
#     df1.columns = cols1
#     df2.columns = cols2
#     df1.reset_index(inplace=True, drop=True)
#     df2.reset_index(inplace=True, drop=True)
#     # Assuming `df_test` contains the subset you want to display
#     df_merged = pd.concat([df1, df2], axis=1, join='outer')
#     df_test = df_merged.iloc[::2,:]
    
#     # For each time snapshot, get the temperature data
#     temperatures_data = []
#     for index, snap in df_test.iterrows():
#         temperatures = list(snap.iloc[1:])
#         heatmap = generate_heatmap_figure(M, points, temperatures)  # M = 21 for grid size
#         temperatures_data.append({
#             'time': snap['time'],  # Include timestamp
#             'data': heatmap
#         })
    
#     return render_template("show_data.html",temp_graphJSON=temp_graphJSON, humidity_graphJSON=humidity_graphJSON, heat_graphJSON=temperatures_data)

if __name__ == "__main__":
    app.run(host='0.0.0.0')