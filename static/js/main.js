// Establish a socket connection using Socket.IO
var socket = io();

socket.on('mqtt_timestamp_update', function(data) {
  console.log('MQTT update received, reloading page');
  if (data.timestamp) {
    document.getElementById("lastTimestamp").innerText = data.timestamp;
  }
});

socket.on('mqtt_switch_update', function (data) {
    var switchElement = document.getElementById("toggle");

    switchElement.checked = data.switch === 1;
    document.getElementById("switchState").innerText = switchElement.checked ? "On" : "Off";

  });

// Update the switch label dynamically
document.getElementById("toggle").addEventListener("change", function() {
  document.getElementById("switchState").innerText = this.checked ? "On" : "Off";
});

// Retrieve historical data from the global window object set in the HTML template
var tempHistory = window.data.tempHistory;
var humHistory = window.data.humHistory;
var presHistory = window.data.presHistory;

// Default number of points to display
var n = 10;

// Utility function: Returns the last n values of an array, padding with NaN if necessary.
function getLastNValues(arr, n) {
  let result = arr.slice(-n);
  while (result.length < n) {
    result.unshift(NaN);
  }
  return result;
}

// Create charts with initial data using Chart.js
const ctxTemp = document.getElementById('tempChart').getContext('2d');
const ctxHum = document.getElementById('humChart').getContext('2d');
const ctxPres = document.getElementById('presChart').getContext('2d');

const tempChart = new Chart(ctxTemp, {
    type: 'line',
    data: {
        labels: Array.from({ length: n }, (_, i) => i + 1),
        datasets: [{
            label: 'Temperature (°C)',
            data: getLastNValues(tempHistory, n),
            borderColor: 'coral',
            fill: false,
            tension: 0.1,
            pointRadius: 2
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: { display: false },
            y: {
                min: -10,
                max: 50,
                ticks: { color: '#f0f0f0' }
            }
        }
    }
});

const humChart = new Chart(ctxHum, {
    type: 'line',
    data: {
        labels: Array.from({ length: n }, (_, i) => i + 1),
        datasets: [{
            label: 'Humidity (%)',
            data: getLastNValues(humHistory, n),
            borderColor: 'darkcyan',
            fill: false,
            tension: 0.1,
            pointRadius: 2
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: { display: false },
            y: {
                min: 0,
                max: 100,
                ticks: { color: '#f0f0f0' }
            }
        }
    }
});

const presChart = new Chart(ctxPres, {
    type: 'line',
    data: {
        labels: Array.from({ length: n }, (_, i) => i + 1),
        datasets: [{
            label: 'Pressure (hPa)',
            data: getLastNValues(presHistory, n),
            borderColor: 'MediumSeaGreen',
            fill: false,
            tension: 0.1,
            pointRadius: 2
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: { display: false },
            y: {
                min: 900,
                max: 1100,
                ticks: { color: '#f0f0f0' }
            }
        }
    }
});

// Function to update charts when the slider changes
function updateCharts(newN) {
  n = newN;
  let newLabels = Array.from({length: n}, (_, i) => i + 1);
  tempChart.data.labels = newLabels;
  tempChart.data.datasets[0].data = getLastNValues(tempHistory, n);
  tempChart.update();

  humChart.data.labels = newLabels;
  humChart.data.datasets[0].data = getLastNValues(humHistory, n);
  humChart.update();

  presChart.data.labels = newLabels;
  presChart.data.datasets[0].data = getLastNValues(presHistory, n);
  presChart.update();
}

// Function to update the displayed slider value and charts when the slider is moved
function updateHistoryValue(val) {
  document.getElementById("historyValue").innerText = val;
  updateCharts(parseInt(val));
}
