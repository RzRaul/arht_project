import numpy as np
import pandas as pd
import plotly.express as px
from scipy.interpolate import Rbf

# Function to create a heatmap
def create_heatmap(M, points, temperatures):
    # Create an empty MxM grid
    grid_x, grid_y = np.meshgrid(np.arange(M), np.arange(M))
    grid_x = grid_x.flatten()
    grid_y = grid_y.flatten()

    # The known points and their temperatures
    grid_x, grid_y = np.meshgrid(np.linspace(0, M-1, M), np.linspace(0, M-1, M))
    known_points = np.array(points)
    known_temperatures = np.array(temperatures)

    # Perform Radial Basis Function (RBF) interpolation with a Gaussian function
    rbf = Rbf(known_points[:, 0], known_points[:, 1], known_temperatures, function='multiquadric')
    # rbf = Rbf(known_points[:, 0], known_points[:, 1], known_temperatures, function='gaussian')
    # rbf = Rbf(known_points[:, 0], known_points[:, 1], known_temperatures, function='linear')
    # rbf = Rbf(known_points[:, 0], known_points[:, 1], known_temperatures, function='cubic')
    # rbf = Rbf(known_points[:, 0], known_points[:, 1], known_temperatures, function='quintic')
    # rbf = Rbf(known_points[:, 0], known_points[:, 1], known_temperatures, function='thin_plate')
    grid_temperatures = rbf(grid_x, grid_y)

    # Reshape the output into a grid shape (M x M)
    temperature_grid = grid_temperatures.reshape(M, M)

    # Create a DataFrame for easier plotting
    df = pd.DataFrame(temperature_grid)

    # Define a fixed color range (min and max temperature values)
    fixed_min = 5  # Minimum temperature value for the color scale
    fixed_max = 30  # Maximum temperature value for the color scale

    # Plot the heatmap using Plotly Express
    fig = px.imshow(df, color_continuous_scale='Turbo', labels={'color': 'Temperature'})

    # Update the color scale to be fixed
    fig.update_traces(coloraxis='coloraxis', colorbar=dict(title='Temperature (°C)', tickvals=[fixed_min, fixed_max], ticktext=[f'{fixed_min}°C', f'{fixed_max}°C']))
    fig.update_layout(
        title='Temperature Distribution Heatmap',
        xaxis_title='X Coordinate',
        yaxis_title='Y Coordinate',
        coloraxis=dict(cmin=fixed_min, cmax=fixed_max)
    )
    
    # Show the figure
    fig.show()


df = pd.read_csv("minimal_test/study_1001.csv")
df['sens_time'] = pd.to_datetime(df['sens_time'])
# df = pd.DataFrame(data)
df.columns = ['sens_time','room_name','id_study','temperature_S1','humidity_S1','temperature_S2','humidity_S2','temperature_S3','humidity_S3','temperature_S4','humidity_S4','temperature_S5','humidity_S5']
df['sens_time'] = df['sens_time'].dt.strftime('%Y-%m-%d %H:%M')
df.drop(columns=['id_study'], inplace=True)
df = df.replace(0, np.nan)
# df.interpolate(method='linear', limit_direction='both', axis=0, inplace=True)
df_melted = df.melt(id_vars=['sens_time', 'room_name'], 
                    value_vars=['temperature_S1', 'temperature_S2', 'temperature_S3', 'temperature_S4', 'temperature_S5'],
                    var_name='sensor', value_name='temperature')


fig_temp = px.line(df_melted, 
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

fig_hum = px.line(df, x='sens_time', y=['humidity_S1', 'humidity_S2','humidity_S3','humidity_S4','humidity_S5'], color='room_name')

fig_temp.show()
# Define grid size (M x M)
# M = 21  # Example for a 10x10 grid
# points = [(20,5),(20,15),(13,10),(20,10),(10,0),(0,5),(4,2),(6,10),(4,20),(1,13)]
# cols1 = ['time','20,5','20,15','13,10','20,10','10,0']
# cols2 = ['0,5','4,2','6,10','4,20','1,13']
# df = pd.read_csv("minimal_test/study_1001.csv")
# df['sens_time'] = pd.to_datetime(df['sens_time'])
# df['sens_time'] = df['sens_time'].dt.strftime('%Y-%m-%d %H:%M')
# df = df.replace(0, np.nan)
# df1 = df[df['room_name']=="Bedroom"]
# df2 = df[df['room_name']!="Bedroom"]
# df1 = df1.drop(columns=['id_study','room_name','humidity_pin17','humidity_pin19','humidity_pin23','humidity_pin32','humidity_pin33'])
# df2 = df2.drop(columns=['sens_time','id_study','room_name','humidity_pin17','humidity_pin19','humidity_pin23','humidity_pin32','humidity_pin33'])
# # df = df.iloc[::15,:]
# df1.columns = cols1
# df2.columns = cols2
# df1.reset_index(inplace=True, drop=True)
# df2.reset_index(inplace=True, drop=True)
# print(df2.head())
# print(df1.head())
# df_merged = pd.concat([df1,df2], axis=1, join='outer')
# print(df_merged.head())
# df_merged = df_merged.iloc[::3,:]
# df_test = df_merged.head(6)
# # Known points and temperatures at those points (row, col, temperature)

# for index, snap in df_test.iterrows():
#     temperatures = list(snap.iloc[1:])
#     create_heatmap(M, points, temperatures)

# Call the function to create the heatmap
# create_heatmap(M, points, temperatures)
