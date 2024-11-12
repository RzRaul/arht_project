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

    # Perform Radial Basis Function (RBF) interpolation with a Multiquadratic function
    rbf = Rbf(known_points[:, 0], known_points[:, 1], known_temperatures, function='multiquadric')
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

# Define grid size (M x M)
M = 21  # Example for a 10x10 grid
points = [(20,5),(20,15),(13,10),(20,10),(10,0),(0,5),(4,2),(6,10),(4,20),(1,13)]
cols1 = ['time','20,5','20,15','13,10','20,10','10,0']
cols2 = ['0,5','4,2','6,10','4,20','1,13']
df = pd.read_csv("minimal_test/study_1001.csv")
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
print(df2.head())
print(df1.head())
df_merged = pd.concat([df1,df2], axis=1, join='outer')
print(df_merged.head())
df_merged = df_merged.iloc[::3,:]
df_test = df_merged.head(6)
# Known points and temperatures at those points (row, col, temperature)

for index, snap in df_test.iterrows():
    temperatures = list(snap.iloc[1:])
    create_heatmap(M, points, temperatures)

# <!-- 
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Temperature Heatmap by Time of Day</title>
#     <script src="https://cdn.jsdelivr.net/npm/plotly.js-dist@2.17.1"></script>
#     <style>
#         body {
#             font-family: Arial, sans-serif;
#         }
#         #heatmap {
#             height: 600px;
#         }
#         .slider-container {
#             width: 80%;
#             margin: 20px auto;
#             text-align: center;
#         }
#         .slider-label {
#             font-size: 18px;
#         }
#     </style>
# </head>
# <body>
#     <h1>Temperature Heatmap - Time of Day</h1>
#     <div id="heatmap"></div>

#     <div class="slider-container">
#         <label for="time-slider" class="slider-label">Time of Day: <span id="time-label">0</span> hrs</label><br>
#         <input type="range" id="time-slider" min="0" max="23" value="0" step="1">
#     </div>

#     <script>
#         // Parse the temperature data passed from Flask to JavaScript
#         const temperatureData = {{ temperature_data | tojson }};
#         const M = {{ M }};

#         // Define a fixed range for the color scale
#         const fixedMin = 0;   // Minimum temperature (e.g., 0°C)
#         const fixedMax = 50;  // Maximum temperature (e.g., 50°C)

#         // Initial time selection (hour)
#         let currentTime = 0;

#         // Function to update the heatmap based on the selected time
#         function updateHeatmap(hour) {
#             // Get the temperatures for the selected hour
#             const hourData = temperatureData[hour];
            
#             // Create a grid of temperatures (for simplicity, we're using random data for this example)
#             const gridTemperatures = Array(M).fill().map(() => Array(M).fill(0)); // Replace this with actual interpolation logic

#             // Assign the known temperatures to the grid points
#             for (let i = 0; i < hourData.length; i++) {
#                 const [x, y] = [Math.floor(Math.random() * M), Math.floor(Math.random() * M)];  // Randomly placing known points on the grid
#                 gridTemperatures[x][y] = hourData[i];
#             }

#             // Plotly data for the heatmap
#             const trace = {
#                 z: gridTemperatures,
#                 type: 'heatmap',
#                 colorscale: 'Viridis',  // You can change this to any colorscale you prefer
#                 colorbar: {
#                     title: 'Temperature (°C)',
#                     tickvals: [fixedMin, fixedMax],  // Optional: Set the range for the color bar ticks
#                     ticktext: [`${fixedMin}°C`, `${fixedMax}°C`]
#                 },
#                 zmin: fixedMin,  // Set the fixed min temperature
#                 zmax: fixedMax   // Set the fixed max temperature
#             };

#             const layout = {
#                 title: `Temperature Distribution at ${hour} hrs`,
#                 xaxis: { title: 'X Coordinate' },
#                 yaxis: { title: 'Y Coordinate' }
#             };

#             // Update the heatmap
#             Plotly.react('heatmap', [trace], layout);
#         }

#         // Event listener for the slider to update the time and heatmap
#         document.getElementById('time-slider').addEventListener('input', function (event) {
#             currentTime = event.target.value;
#             document.getElementById('time-label').textContent = currentTime;
#             updateHeatmap(currentTime);
#         });

#         // Initial heatmap plot (at hour 0)
#         updateHeatmap(currentTime);
#     </script>
# </body>
# </html>


# -->

// var temperaturesData = {{ temperatures_data | safe }};
    // var slider = document.getElementById("time-slider");
    // var timeDisplay = document.getElementById("time-display");

    // // Function to update the heatmap for a given snapshot
    // function updateHeatmap(snapshot) {
    //     var tempGraphJSON = snapshot.graph;
    //     var heatmapData = JSON.parse(tempGraphJSON);
        
    //     // Plot the heatmap using Plotly
    //     Plotly.newPlot('heatmap', heatmapData.data, heatmapData.layout);
    // }

    // // Initialize the first heatmap and display time
    // updateHeatmap(temperaturesData[0]);
    // timeDisplay.textContent = temperaturesData[0].time;

    // // Event listener for the slider to update the heatmap when the time changes
    // slider.addEventListener("input", function() {
    //     var index = slider.value;
    //     timeDisplay.textContent = temperaturesData[index].time;
    //     updateHeatmap(temperaturesData[index]);
    // });