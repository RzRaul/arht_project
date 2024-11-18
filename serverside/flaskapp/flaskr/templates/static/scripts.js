var temp_graph = {{temp_graphJSON | safe}};
var hum_graph = {{humidity_graphJSON | safe}};
var heatmap_data = {{heat_graphJSON | safe}};
// var study_data = {{study_data | safe}};
var full_heatmap_data = heatmap_data;

function loadGraphOnHover(sectionId, graphDataUrl, graphElementId) {
    var section = document.getElementById(sectionId);
    var graphElement = document.getElementById(graphElementId);
    var dataLoaded = graphElement.getAttribute('data-loaded');

    // Load data on hover
    section.addEventListener('mouseenter', function() {
        if (dataLoaded === 'false') {
            // Fetch graph data from the API
            fetch(graphDataUrl)
                .then(response => response.json())
                .then(data => {
                    // Store the graph data in the element
                    graphElement.setAttribute('data-graph', JSON.stringify(data));
                    graphElement.setAttribute('data-loaded', 'true');
                })
                .catch(error => {
                    console.error('Error loading graph data:', error);
                });
        }
    });

    // Show the graph on click
    section.addEventListener('click', function() {
        if (dataLoaded === 'true') {
            var graphData = JSON.parse(graphElement.getAttribute('data-graph'));
            // Plot the graph
            Plotly.newPlot(graphElement, graphData.data, graphData.layout);
            // Make the chart visible after it is loaded
            graphElement.style.display = 'block';
        }
    });
}

    // Load graphs when hovering and click to show them
loadGraphOnHover("tempGraphSection", "/api/temp_graph", "temp-chart");
loadGraphOnHover("humidityGraphSection", "/api/humidity_graph", "humidity-chart");
loadGraphOnHover("heatmapGraphSection", "/api/heatmap_data", "heatmap-chart");

// Time Slider functionality
var slider = document.getElementById("time-slider");
var timeDisplay = document.getElementById("time-label");

// Function to update the heatmap for a given snapshot
function updateHeatmap(snapshot) {
    var tempGraphJSON = snapshot.graph;
    var heatmapData = JSON.parse(tempGraphJSON);
    heatmapData.layout.yaxis.autorange = 'reversed';
    Plotly.newPlot('heatmap_chart', heatmapData.data, heatmapData.layout);
}
function renderHeatmap(snapshot) {
    // Extract temperature grid and sensor positions from the snapshot
    const temperatureGrid = snapshot.temperature_grid;
    const sensorPositions = snapshot.sensor_positions;

    // Create the heatmap trace
    const heatmapTrace = {
        z: temperatureGrid,
        colorscale: 'Turbo',
        colorbar: {
            title: 'Temperature (°C)',
            tickvals: [10, 30],
            ticktext: ['10°C', '30°C']
        },
        zmin: 10,
        zmax: 30
    };

    // Create the sensor trace (red 'X' markers for sensor positions)
    const sensorTrace = {
        x: sensorPositions.map(pos => pos[0]),
        y: sensorPositions.map(pos => pos[1]),
        mode: 'markers',
        marker: {
            symbol: 'x',
            color: 'red',
            size: 10,
            line: { width: 2 }
        },
        name: 'Sensors'
    };

    // Define the layout for the plot
    const layout = {
        title: 'Temperature Heatmap',
        xaxis: { title: 'X Coordinate' },
        yaxis: { title: 'Y Coordinate', autorange: 'reversed' },  // Reverse Y axis for heatmap style
        showlegend: true
    };

    // Create the plot or update if it already exists
    if (Plotly.getPlotly('heatmap_chart')) {
        // Update the heatmap if already rendered
        Plotly.update('heatmap_chart', {
            z: [temperatureGrid]  // Update temperature grid
        });
    } else {
        // If it's the first render, create a new plot
        Plotly.newPlot('heatmap_chart', [heatmapTrace, sensorTrace], layout);
    }

    // Update the displayed time range
    const timeRange = `${snapshot.start_time} - ${snapshot.end_time}`;
    document.getElementById('time-range').innerText = `Time: ${timeRange}`;
}

// Initialize the first heatmap and display time
updateHeatmap(heatmap_data[0]);
timeDisplay.textContent = heatmap_data[0].time;

// Event listener for the slider to update the heatmap when the time changes
slider.addEventListener("input", function() {
    var index = slider.value;
    timeDisplay.textContent = heatmap_data[index].time;
    updateHeatmap(heatmap_data[index]);
});
    // Function to filter the heatmap data based on the date range
function filterDataByDate() {
    var fromDate = new Date(document.getElementById('from_date').value + 'T00:00:00'); // Set start time to 00:00:00
    var tillDate = new Date(document.getElementById('till_date').value + 'T23:59:59'); // Set end time to 23:59:59

    // Filter the heatmap data based on the date range
    var filteredData = full_heatmap_data.filter(function(item) {
        var snapshotDate = new Date(item.time); // Assuming 'time' is in a format that JavaScript can parse
        return snapshotDate >= fromDate && snapshotDate <= tillDate;
    });

    return filteredData;
}

// Function to update the slider range and heatmap based on filtered data
function updateSliderAndHeatmap() {
    var filteredData = filterDataByDate();

    // If there is filtered data, update the slider range and the first heatmap
    if (filteredData.length > 0) {
        // Update the slider range to match the filtered data
        slider.max = filteredData.length - 1;
        slider.value = 0;

        // Update the heatmap with the first snapshot of the filtered data
        updateHeatmap(filteredData[0]);
        heatmap_data = filteredData;
        timeDisplay.textContent = filteredData[0].time;
    }
}

// Add event listeners to the date inputs to update the heatmap when the date range changes
document.getElementById('from_date').addEventListener('change', updateSliderAndHeatmap);
document.getElementById('till_date').addEventListener('change', updateSliderAndHeatmap);

