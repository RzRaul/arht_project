var temp_graph = {{temp_graphJSON | safe}};
var hum_graph = {{humidity_graphJSON | safe}};
var heatmap_data = {{heat_graphJSON | safe}};
var study_data = {{study_dataJSON | safe}};
var full_heatmap_data = heatmap_data;

Plotly.newPlot('temp-graph', temp_graph.data, temp_graph.layout);
Plotly.newPlot('hum-graph', hum_graph.data, hum_graph.layout);
Plotly.newPlot('heatmap-graph', heatmap_data.data, heatmap_data.layout);
document.getElementById('name_dash').innerText = `${study_info.owner}'s Dashboard`;

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

