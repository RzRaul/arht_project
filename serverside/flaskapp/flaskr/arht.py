from datetime import date
from flask import Flask, request, render_template, Flask, jsonify, url_for, redirect, session
from flask_mysqldb import MySQL
import pandas as pd
import numpy as np
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go
from scipy.interpolate import Rbf

app = Flask(__name__)
app.secret_key = 'esp32_project_arht'  # Used for session management
app.config['MYSQL_HOST'] = '192.168.1.200'
app.config['MYSQL_USER'] = 'lurker'
app.config['MYSQL_PASSWORD'] = 'LurkPass1'
app.config['MYSQL_DB'] = 'arht_prod'
app.config["MYSQL_CUSTOM_OPTIONS"] = {"ssl_mode": 'DISABLED', "ssl":False}  # https://mysqlclient.readthedocs.io/user_guide.html#functions-and-attributes
PLOT_COLOR = 'rgba(0,0,0,0)';
PLOT_PAPER_COLOR = 'rgba(0,0,0,0)';
mysql = MySQL(app)

cache = {}
heatmap_cache = {}
studies_info = {}
layout_cache = {}
graphs_cache = {}
M = 21

def get_data():
    global study_data
    cur = mysql.connection.cursor()
    cur.execute('''select * from measurements where sens_time > "2024-10-28 00:00:00" and id_study = 1001''')
    data = cur.fetchall()
    cur.close()
    df = pd.DataFrame(data)
    df.columns = ['sens_time','room_name','id_study','TS1','HS1','TS2','HS2','TS3','HS3','TS4','HS4','TS5','HS5']
    df['sens_time'] = df['sens_time'].dt.strftime('%Y-%m-%d %H:%M')
    df.drop(columns=['id_study'], inplace=True)
    study_data = df.replace(0, np.nan)
    return df.replace(0, np.nan)

def get_all_study_info():
    global studies_info
    cur = mysql.connection.cursor()
    cur.execute(f'''select * from studies LIMIT 10''')
    aux = cur.fetchall()
    for row in aux:
        studies_info.update({row[0]:row[1:]})
    cur.close()

def get_study_info(id_study):
    global studies_info
    if id_study not in studies_info:
        cur = mysql.connection.cursor()
        cur.execute(f'''select * from studies where id_study={id_study}''')
        aux = cur.fetchall()
        if aux != None:
            for row in aux:
                studies_info[str(row[0])] = {'start_date':row[1].strftime('%Y-%m-%d %H:%M'),'end_date':row[2].strftime('%Y-%m-%d %H:%M'),'owner':row[3], 'status':row[4], 'email':row[5]}
        
        cur.execute(f'''select room_name, sensor_1, sensor_2, sensor_3, sensor_4, sensor_5 from layouts where id_study={id_study}''')
        aux = cur.fetchall()
        layout_cache[id_study] = {}
        if aux != None:
            for row in aux:
                layout_cache[id_study][str(row[0])] = row[1:]

        cur.execute(f'''select * from measurements where id_study={id_study}''')
        aux = cur.fetchall()
        df = pd.DataFrame(aux)
        df.columns = ['sens_time','room_name','id_study','TS1','HS1','TS2','HS2','TS3','HS3','TS4','HS4','TS5','HS5']
        df['sens_time'] = df['sens_time'].dt.strftime('%Y-%m-%d %H:%M')
        df.drop(columns=['id_study'], inplace=True)
        df.replace(0, np.nan, inplace=True)
        cache.update({id_study:df.copy()})
        cur.close()

def generate_temp_graph(id_study):
    data = cache[id_study]
    if data is None:
        get_study_info(id_study)

    df_melted_temp = data.melt(id_vars=['sens_time', 'room_name'], 
                    value_vars=['TS1', 'TS2', 'TS3', 'TS4', 'TS5'],
                    var_name='sensor', value_name='temperature')

    fig_temp = px.line(df_melted_temp, 
                    x='sens_time', 
                    y='temperature', 
                    color='room_name',  # Color by room_name to separate rooms
                    symbol='sensor', # Separate lines by sensor for each room
                    markers=False,)
    fig_temp.update_traces(marker=dict(size=1, line=dict(width=1, color='DarkSlateGrey')), 
                       line=dict(width=3))  # Customize marker size, line width, etc.

    fig_temp.update_layout(
        legend_title='Room and Sensor',  # Custom title for the legend
        xaxis_title='Time',     # Label for the X-axis
        yaxis_title='Temperature (°C)',  # Label for the Y-axis
        legend=dict(
            title="Room and Sensor",     # Title for the legend
            traceorder='normal', # Ensures the order of the traces matches the color scale
            # yanchor="top",
            # y=0.99,
            # xanchor="right",
            # x=0.01
        ),
        margin=go.layout.Margin(
            l=0, #left margin
            r=0, #right margin
            b=0, #bottom margin
            t=0  #top margin
        ),
        paper_bgcolor=PLOT_PAPER_COLOR,
        plot_bgcolor=PLOT_COLOR,
    )
    fig_temp.update_xaxes(
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey'
    )
    fig_temp.update_yaxes(
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey'
    )

    return json.dumps(fig_temp, cls=plotly.utils.PlotlyJSONEncoder)

def generate_hum_graph(id_study):
    data = cache[id_study]
    if data is None:
        get_study_info(id_study)
       
    df_melted_hum = data.melt(id_vars=['sens_time', 'room_name'], 
                    value_vars=['HS1', 'HS2', 'HS3', 'HS4', 'HS5'],
                    var_name='sensor', value_name='humidity')

    fig_hum = px.line(df_melted_hum, 
                    x='sens_time', 
                    y='humidity', 
                    color='room_name',  # Color by room_name to separate rooms
                    symbol='sensor', # Separate lines by sensor for each room
                    markers=False,)
    fig_hum.update_traces(marker=dict(size=1, line=dict(width=1, color='DarkSlateGrey')), 
                       line=dict(width=3))  # Customize marker size, line width, etc.

    fig_hum.update_layout(
        legend_title='Room and Sensor',  # Custom title for the legend
        xaxis_title='Time',     # Label for the X-axis
        yaxis_title='Humidity (%)',  # Label for the Y-axis
        legend=dict(
            title="Room and Sensor",     # Title for the legend
            traceorder='normal', # Ensures the order of the traces matches the color scale 
            # yanchor="top",
            # y=0.99,
            # xanchor="right",
            # x=0.01
        ),
        margin=go.layout.Margin(
            l=0, #left margin
            r=0, #right margin
            b=0, #bottom margin
            t=0  #top margin
        ),
        paper_bgcolor=PLOT_PAPER_COLOR,
        plot_bgcolor=PLOT_COLOR,
    )
    fig_hum.update_xaxes(
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey'
    )
    fig_hum.update_yaxes(
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey'
    )

    return json.dumps(fig_hum, cls=plotly.utils.PlotlyJSONEncoder)
    
def generate_heatmap_data(M, points, temperatures):
    grid_x, grid_y = np.meshgrid(np.linspace(0, M-1, M), np.linspace(0, M-1, M))
    known_points = np.array(points)
    known_temperatures = np.array(temperatures)
    rbf = Rbf(known_points[:, 0], known_points[:, 1], known_temperatures, function='multiquadric')
    grid_temperatures = rbf(grid_x, grid_y)
    temperature_grid = grid_temperatures.reshape(M, M)
    return temperature_grid

def generate_temp_graph_range(id_study, start_datetime, end_datetime):
    cur = mysql.connection.cursor()
    cur.execute(f'''SELECT sens_time, room_name, temp_pin17, temp_pin19, temp_pin23, temp_pin32, temp_pin33 from measurements where id_study={id_study} and sens_time BETWEEN "{start_datetime}" and "{end_datetime}" ;''')
    aux = cur.fetchall()
    df = pd.DataFrame(aux)
    cur.close()
    df.columns = ['sens_time','room_name','TS1','TS2','TS3','TS4','TS5']
    df['sens_time'] = df['sens_time'].dt.strftime('%Y-%m-%d %H:%M')
    df.replace(0, np.nan, inplace=True)
    # cache.update({id_study:df.copy()})
    
    
    df_melted_temp = df.melt(id_vars=['sens_time', 'room_name'], 
                    value_vars=['TS1', 'TS2', 'TS3', 'TS4', 'TS5'],
                    var_name='sensor', value_name='temperature')

    fig_temp = px.line(df_melted_temp, 
                    x='sens_time', 
                    y='temperature', 
                    color='room_name',  # Color by room_name to separate rooms
                    symbol='sensor', # Separate lines by sensor for each room
                    markers=False,)
    fig_temp.update_traces(marker=dict(size=1, line=dict(width=1, color='DarkSlateGrey')), 
                       line=dict(width=3))  # Customize marker size, line width, etc.

    fig_temp.update_layout(
        legend_title='Room and Sensor',  # Custom title for the legend
        xaxis_title='Time',     # Label for the X-axis
        yaxis_title='Temperature (°C)',  # Label for the Y-axis
        legend=dict(
            title="Room and Sensor",     # Title for the legend
            traceorder='normal', # Ensures the order of the traces matches the color scale
            # yanchor="top",
            # y=0.99,
            # xanchor="right",
            # x=0.01
        ),
        margin=go.layout.Margin(
            l=0, #left margin
            r=0, #right margin
            b=0, #bottom margin
            t=0  #top margin
        ),
        paper_bgcolor=PLOT_PAPER_COLOR,
        plot_bgcolor=PLOT_COLOR,
    )
    fig_temp.update_xaxes(
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey'
    )
    fig_temp.update_yaxes(
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey'
    )

    return json.dumps(fig_temp, cls=plotly.utils.PlotlyJSONEncoder)

def generate_hum_graph_range(id_study, start_datetime, end_datetime):
    cur = mysql.connection.cursor()
    cur.execute(f'''SELECT sens_time,room_name, humidity_pin17, humidity_pin19, humidity_pin23, humidity_pin32, humidity_pin33 from measurements where id_study={id_study} and sens_time BETWEEN "{start_datetime}" and "{end_datetime}" ;''')
    aux = cur.fetchall()
    df = pd.DataFrame(aux)
    cur.close()
    df.columns = ['sens_time','room_name','HS1', 'HS2', 'HS3', 'HS4', 'HS5']
    df['sens_time'] = df['sens_time'].dt.strftime('%Y-%m-%d %H:%M')
    df.replace(0, np.nan, inplace=True)
    # cache.update({id_study:df.copy()})_day+" 23:59:59")]
    
    df_melted_hum = df.melt(id_vars=['sens_time', 'room_name'], 
                    value_vars=['HS1', 'HS2', 'HS3', 'HS4', 'HS5'],
                    var_name='sensor', value_name='humidity')

    fig_hum = px.line(df_melted_hum, 
                    x='sens_time', 
                    y='humidity', 
                    color='room_name',  # Color by room_name to separate rooms
                    symbol='sensor', # Separate lines by sensor for each room
                    markers=False,)
    fig_hum.update_traces(marker=dict(size=1, line=dict(width=1, color='DarkSlateGrey')), 
                       line=dict(width=3))  # Customize marker size, line width, etc.

    fig_hum.update_layout(
        legend_title='Room and Sensor',  # Custom title for the legend
        xaxis_title='Time',     # Label for the X-axis
        yaxis_title='Humidity (%)',  # Label for the Y-axis
        legend=dict(
            title="Room and Sensor",     # Title for the legend
            traceorder='normal', # Ensures the order of the traces matches the color scale 
            # yanchor="top",
            # y=0.99,
            # xanchor="right",
            # x=0.01
        ),
        margin=go.layout.Margin(
            l=0, #left margin
            r=0, #right margin
            b=0, #bottom margin
            t=0  #top margin
        ),
        paper_bgcolor=PLOT_PAPER_COLOR,
        plot_bgcolor=PLOT_COLOR,
    )
    fig_hum.update_xaxes(
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey'
    )
    fig_hum.update_yaxes(
        mirror=True,
        ticks='outside',
        showline=True,
        linecolor='black',
        gridcolor='lightgrey'
    )

    return json.dumps(fig_hum, cls=plotly.utils.PlotlyJSONEncoder)

def generate_last_heatmap_from_cache(id_study, json_format=True):
    if id_study not in studies_info:
        return None
    known_points = np.array(get_points_from_layouts(layout_cache[id_study]))
    temperatures = heatmap_cache[id_study]
    temperatures = temperatures[-1]
    temperature_grid = temperatures['temp_grid']
    figure = go.Figure(data=go.Heatmap(
        z=temperature_grid,
        colorscale='Turbo',
        colorbar=dict(title='Temperature (°C)', tickvals=[8, 30], ticktext=['8°C', '30°C']),
        zmin=8,  # Set minimum value for color scale
        zmax=30,  # Set maximum value for color scale
    ))
    sensor_x = known_points[:, 0]  # X-coordinates of sensor positions
    sensor_y = known_points[:, 1]  # Y-coordinates of sensor positions
    
    # Create a scatter trace for sensor positions
    sensor_trace = go.Scatter(
        x=sensor_x,
        y=sensor_y,
        mode='markers',
        marker=dict(
            symbol='x',         # 'x' symbol for the marker
            color='red',        # Marker color
            size=10,            # Marker size
            line=dict(width=1)  # Line width around the marker
        ),
        name='Sensors'  # Optional: name for the trace
    )

    # Add the sensor trace to the figure
    figure.add_trace(sensor_trace)

    figure.update_layout(
        title='Temperature Distribution',
        xaxis_title='X Coordinate',
        yaxis_title='Y Coordinate',
        coloraxis=dict(cmin=10, cmax=30),
        margin=go.layout.Margin(
            l=0, #left margin
            r=0, #right margin
            b=0, #bottom margin
            t=0  #top margin
        ),
        paper_bgcolor=PLOT_PAPER_COLOR,
        plot_bgcolor=PLOT_COLOR,
    )
    if json_format:
        return json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        return figure

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
        zmin=8,  # Set minimum value for color scale
        zmax=30,  # Set maximum value for color scale
    ))
    sensor_x = known_points[:, 0]  # X-coordinates of sensor positions
    sensor_y = known_points[:, 1]  # Y-coordinates of sensor positions
    
    # Create a scatter trace for sensor positions
    sensor_trace = go.Scatter(
        x=sensor_x,
        y=sensor_y,
        mode='markers',
        marker=dict(
            symbol='x',         # 'x' symbol for the marker
            color='red',        # Marker color
            size=10,            # Marker size
            line=dict(width=2)  # Line width around the marker
        ),
        name='Sensors'  # Optional: name for the trace
    )

    # Add the sensor trace to the figure
    figure.add_trace(sensor_trace)

    figure.update_layout(
        title='Temperature Distribution',
        xaxis_title='X Coordinate',
        yaxis_title='Y Coordinate',
        coloraxis=dict(cmin=10, cmax=30),
        paper_bgcolor=PLOT_PAPER_COLOR,
        plot_bgcolor=PLOT_COLOR,
    )


    return figure

def get_points_from_layouts(layouts):
    if layouts is None:
        return None
    points = []
    for layout in layouts:
        for point in layouts[layout]:
            points.append(tuple(int(x) for x in point.split(',')))
        
    return points

def generate_heatmap_sequence(id_study):
    if id_study in studies_info:
        data = cache[id_study]
        info = studies_info[id_study]
        layouts = layout_cache[id_study]
        points = get_points_from_layouts(layouts)
        dfs = []

        df = data.copy()
        drop_time = False
        new_cols = ['time']
        for layout in layouts:
            for col in layouts[layout]:
                new_cols.append(col)
            df_aux = df[df['room_name'] == layout]
            #drops humidity because we just care about temperature
            if not drop_time:
                df_aux.drop(columns=['room_name','HS1','HS2','HS3','HS4','HS5'], inplace=True)
                #After first layout, drop time to not duplicate
                drop_time = True
            else:
                df_aux.drop(columns=['sens_time','room_name','HS1','HS2','HS3','HS4','HS5'], inplace=True)
            df_aux.reset_index(inplace=True, drop=True)
            dfs.append(df_aux.copy())

        # Assuming `df_test` contains the subset you want to display
        df_merged = pd.concat(dfs, axis=1, join='outer')
        df_merged.columns= new_cols
        df_merged.interpolate(method='linear', limit_direction='forward', axis=0, inplace=True)
        df_test = df_merged
        # # Create heatmap figures for each snapshot and serialize them to JSON
        temperatures_data = []
        for index, snap in df_test.iterrows():
            temperatures = list(snap.iloc[1:])
            temps = generate_heatmap_data(M, points, temperatures)  # M = 21 for grid size
            temperatures_data.append({
                'time': snap['time'],  # Include timestamp
                'temp_grid': temps,
            })

        return temperatures_data

def load_cache(id_study, force_load=False):
    loaded = False
    if id_study not in studies_info:
        get_study_info(id_study)

    if id_study in studies_info:
        if id_study not in graphs_cache or force_load:
            graphs_cache.update({id_study:{}})
            graphs_cache[id_study].update({'temp': generate_temp_graph(id_study)})
            graphs_cache[id_study].update({'hum': generate_hum_graph(id_study)})
        if id_study not in heatmap_cache or force_load:
            heatmap_cache.update({id_study:generate_heatmap_sequence(id_study)})
        loaded = True

    return loaded
    
with app.app_context():
    pass


@app.route('/')
def login():
    return render_template('login.html')

@app.route('/authenticate_hover', methods=['POST'])
def authenticate_hover():
    # Get the study code sent in the request body
    id_study = request.json.get('study_code')
    
    if load_cache(id_study):
        return jsonify({"status": "success", "data": id_study})
    else:
        return jsonify({"status": "error", "message": "Invalid study code"}), 400


@app.route('/authenticate', methods=['POST'])
def authenticate():
    id_study = request.form.get('study_code')
    if load_cache(id_study):
        session['id_study'] = id_study
        return redirect(url_for('study_dashboard'))
    else:
        # Invalid code
        return render_template('login.html', error="Invalid study code")

@app.route('/study_dashboard')
def study_dashboard():
    if 'id_study' not in session:
        return redirect(url_for('login'))
    
    # Get study code from session
    id_study = session['id_study']
    
    # If the study data is not in cache, load it (for demo purposes, we're simulating this)
    if id_study not in cache:
        # Here you would load the study data (e.g., from a database or external API)
        print("Not in cache ->\n")
        # load_cache(id_study, force_load=True)

    today = date.today().strftime("%Y-%m-%d")
    temp_today = generate_temp_graph_range(id_study, (today + ' 00:00:00'),(today + ' 23:59:00'))
    hum_today = generate_hum_graph_range(id_study, (today + ' 00:00:00'),(today + ' 23:59:00'))
    info = json.dumps(studies_info[id_study])
    layout = layout_cache[id_study]
    heatmap_last = generate_last_heatmap_from_cache(id_study, json_format=True)
    # Pass the data to the study dashboard template
    study_data = studies_info[id_study]
    return render_template('study_dashboard.html', study_dataJSON=info, heat_graphJSON=heatmap_last, humidity_graphJSON=hum_today, temp_graphJSON=temp_today)

@app.route('/logout')
def logout():
    session.pop('study_code', None)
    return redirect(url_for('login'))

@app.route('/api/temp_graph')
def get_temp_graph():
    from_date = request.args.get("from")
    till_date = request.args.get("till")
    id_study = request.args.get("id_study")
    print(f" from->{from_date} till->{till_date} study->{id_study}")
    # This should fetch temperature data from your database

    cur = mysql.connection.cursor()
    cur.execute('''select * from measurements where sens_time > "2024-10-28 00:00:00"''')
    data = cur.fetchall()
    cur.close()
    # df = pd.read_csv("study_1001.csv")
    # df['sens_time'] = pd.to_datetime(df['sens_time'])
    df = pd.DataFrame(data)
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
    cur = mysql.connection.cursor()
    cur.execute('''select * from measurements where sens_time > "2024-10-28 00:00:00"''')
    data = cur.fetchall()
    cur.close()
    # df = pd.read_csv("study_1001.csv")
    # df['sens_time'] = pd.to_datetime(df['sens_time'])
    df = pd.DataFrame(data)
    return jsonify(heatmap_data)

#debug data
@app.route("/debug_data_custom")
def raw_data():
    cur = mysql.connection.cursor()
    cur.execute('''select * from measurements where sens_time > "2024-10-28 00:00:00"''')
    data = cur.fetchall()
    cur.close()
    df = pd.DataFrame(data)
    
    df.columns = ['sens_time','room_name','id_study','TS1','HS1','TS2','HS2','TS3','HS3','TS4','HS4','TS5','HS5']
    df['sens_time'] = df['sens_time'].dt.strftime('%Y-%m-%d %H:%M')
    df.drop(columns=['id_study'], inplace=True)
    df = df.replace(0, np.nan)
    fig_temp = px.line(df, x='sens_time', y=['TS1','TS2','TS3','TS4','TS5']
                         , color='room_name'
                         ,)
    fig_hum = px.line(df, x='sens_time', y=['HS1', 'HS2','HS3','HS4','HS5'], color='room_name', symbols=['HS1', 'HS2','HS3','HS4','HS5'])
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
    id_study = request.args.get("id_study")
    print(f"get->{get_by}  from->{from_date} till->{till_date}")
    cur = mysql.connection.cursor()
    cur.execute(f'''select room_name from measurements where id_study={int(id_study)};''')
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
#     df1 = df1.drop(columns=['id_study','room_name','HS1','HS2','HS3','HS4','HS5'])
#     df2 = df2.drop(columns=['sens_time','id_study','room_name','HS1','HS2','HS3','HS4','HS5'])
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