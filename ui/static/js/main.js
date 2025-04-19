/**
 * Main JavaScript file for Chain of Agents stock analysis system
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const stockForm = document.getElementById('stockForm');
    const stockSymbolInput = document.getElementById('stockSymbol');
    const timePeriodSelect = document.getElementById('timePeriod');
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    const agent1Status = document.getElementById('agent1Status');
    const agent2Status = document.getElementById('agent2Status');
    const agent3Status = document.getElementById('agent3Status');
    
    const loadingChart = document.getElementById('loadingChart');
    const stockChart = document.getElementById('stockChart');
    const chartTitle = document.getElementById('chartTitle');
    
    const recommendationCard = document.getElementById('recommendationCard');
    const recommendationContent = document.getElementById('recommendationContent');
    
    const analysisCard = document.getElementById('analysisCard');
    const analysisContent = document.getElementById('analysisContent');
    
    const insightsCard = document.getElementById('insightsCard');
    const insightsContent = document.getElementById('insightsContent');
    
    // Form submission
    stockForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const symbol = stockSymbolInput.value.trim().toUpperCase();
        const period = timePeriodSelect.value;
        
        if (!symbol) {
            alert('Please enter a stock symbol');
            return;
        }
        
        // Reset UI
        resetUI();
        
        // Show loading state
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Analyzing...';
        loadingChart.innerHTML = '<div class="d-flex justify-content-center align-items-center h-100"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="ms-3 mb-0">Fetching data for ' + symbol + '...</p></div>';
        loadingChart.style.display = 'block';
        
        // Set the first agent to Processing immediately
        updateAgentStatus(agent1Status, 'Processing', 50);
        
        // Call API
        fetchStockAnalysis(symbol, period);
    });
    
    // Reset UI elements
    function resetUI() {
        // Reset agent statuses
        updateAgentStatus(agent1Status, 'Idle', 0);
        updateAgentStatus(agent2Status, 'Idle', 0);
        updateAgentStatus(agent3Status, 'Idle', 0);
        
        // Hide results cards
        recommendationCard.style.display = 'none';
        analysisCard.style.display = 'none';
        insightsCard.style.display = 'none';
        
        // Reset chart
        stockChart.style.display = 'none';
        loadingChart.style.display = 'block';
        chartTitle.textContent = 'Stock Chart';
    }
    
    // Update agent status in UI
    function updateAgentStatus(agentElement, status, progress) {
        const statusLabel = agentElement.querySelector('.status-label');
        const progressBar = agentElement.querySelector('.progress-bar');
        
        statusLabel.textContent = status;
        progressBar.style.width = progress + '%';
        
        // Update status color
        statusLabel.className = 'status-label';
        if (status === 'Running') {
            statusLabel.classList.add('status-running');
        } else if (status === 'Processing') {
            statusLabel.classList.add('status-processing');
        } else if (status === 'Completed') {
            statusLabel.classList.add('status-completed');
        } else if (status === 'Error') {
            statusLabel.classList.add('status-error');
        }
    }
    
    // Fetch stock analysis from API
    function fetchStockAnalysis(symbol, period) {
        // Start a polling mechanism to show realistic agent states during processing
        const startPolling = new Date().getTime();
        const pollingInterval = setInterval(() => {
            const currentTime = new Date().getTime();
            const elapsedSeconds = (currentTime - startPolling) / 1000;
            
            // After 3 seconds, show Analysis Agent as processing if Data Collector still shows processing
            if (elapsedSeconds > 3 && 
                agent1Status.querySelector('.status-label').textContent === 'Processing' && 
                agent2Status.querySelector('.status-label').textContent === 'Idle') {
                updateAgentStatus(agent1Status, 'Completed', 100);
                updateAgentStatus(agent2Status, 'Processing', 50);
            }
            
            // After 6 seconds, show Visualization Agent as processing if Analysis Agent still shows processing
            if (elapsedSeconds > 6 && 
                agent2Status.querySelector('.status-label').textContent === 'Processing' && 
                agent3Status.querySelector('.status-label').textContent === 'Idle') {
                updateAgentStatus(agent2Status, 'Completed', 100);
                updateAgentStatus(agent3Status, 'Processing', 50);
            }
            
            // Stop polling after 20 seconds to avoid endless loop if the server doesn't respond
            if (elapsedSeconds > 20) {
                clearInterval(pollingInterval);
            }
        }, 1000);
        
        fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symbol: symbol,
                period: period
            })
        })
        .then(response => {
            // Clear the polling interval once we get a response
            clearInterval(pollingInterval);
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Enable button
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analyze Stock';
            
            if (!data.success) {
                throw new Error(data.error || 'Unknown error');
            }
            
            // Update pipeline status
            updatePipelineStatus(data.pipeline_status);
            
            // Display results
            displayResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analyze Stock';
            loadingChart.innerHTML = '<div class="alert alert-danger m-3" role="alert">' + error.message + '</div>';
        });
    }
    
    // Update the pipeline status from API response
    function updatePipelineStatus(pipelineStatus) {
        if (!pipelineStatus) return;
        
        // Update data collection status
        if (pipelineStatus.data_collection) {
            const status = pipelineStatus.data_collection.status;
            let displayStatus = status.charAt(0).toUpperCase() + status.slice(1); // Capitalize
            let progress = 0;
            
            if (status === 'completed') {
                progress = 100;
            } else if (status === 'running') {
                displayStatus = 'Processing'; // Show as "Processing" instead of "Running"
                progress = 50;
            }
            
            updateAgentStatus(agent1Status, displayStatus, progress);
        }
        
        // Update analysis status
        if (pipelineStatus.analysis) {
            const status = pipelineStatus.analysis.status;
            let displayStatus = status.charAt(0).toUpperCase() + status.slice(1);
            let progress = 0;
            
            if (status === 'completed') {
                progress = 100;
            } else if (status === 'running') {
                displayStatus = 'Processing';
                progress = 50;
            }
            
            updateAgentStatus(agent2Status, displayStatus, progress);
        }
        
        // Update visualization status
        if (pipelineStatus.visualization) {
            const status = pipelineStatus.visualization.status;
            let displayStatus = status.charAt(0).toUpperCase() + status.slice(1);
            let progress = 0;
            
            if (status === 'completed') {
                progress = 100;
            } else if (status === 'running') {
                displayStatus = 'Processing';
                progress = 50;
            }
            
            updateAgentStatus(agent3Status, displayStatus, progress);
        }
    }
    
    // Display results in UI
    function displayResults(data) {
        // Update chart title
        chartTitle.textContent = `${data.symbol} - ${data.period_description}`;
        
        // Show recommendation
        recommendationCard.style.display = 'block';
        recommendationContent.innerHTML = createRecommendationHTML(data.recommendation, data.confidence);
        
        // Show analysis if available
        if (data.analysis) {
            analysisCard.style.display = 'block';
            analysisContent.innerHTML = formatAnalysisText(data.analysis);
        }
        
        // Show visualization insights if available
        if (data.visualization_insights) {
            insightsCard.style.display = 'block';
            insightsContent.innerHTML = '<p>' + data.visualization_insights + '</p>';
        }
        
        // Create chart with chart configuration
        createStockChart(data.chart_config);
    }
    
    // Create HTML for recommendation display
    function createRecommendationHTML(recommendation, confidence) {
        let recommendationClass = '';
        if (recommendation === 'BUY') {
            recommendationClass = 'buy-recommendation';
        } else if (recommendation === 'SELL') {
            recommendationClass = 'sell-recommendation';
        } else {
            recommendationClass = 'hold-recommendation';
        }
        
        let confidenceClass = '';
        if (confidence === 'HIGH') {
            confidenceClass = 'confidence-high';
        } else if (confidence === 'MEDIUM') {
            confidenceClass = 'confidence-medium';
        } else {
            confidenceClass = 'confidence-low';
        }
        
        return `
            <div class="text-center mb-3">
                <h2 class="${recommendationClass}">${recommendation}</h2>
                <p class="${confidenceClass}">Confidence: ${confidence}</p>
            </div>
        `;
    }
    
    // Format analysis text for display
    function formatAnalysisText(analysisText) {
        // Split the text by newlines and wrap in <p> tags
        const paragraphs = analysisText.split('\n\n');
        return paragraphs.map(p => {
            // Skip empty paragraphs
            if (!p.trim()) return '';
            
            // Check if this is a heading (starts with numbers followed by period)
            if (/^\d+\.\s+/.test(p)) {
                return '<h6>' + p + '</h6>';
            }
            
            // Normal paragraph
            return '<p>' + p + '</p>';
        }).join('');
    }
    
    // Create stock chart with Plotly
    function createStockChart(chartConfig) {
        if (!chartConfig || !chartConfig.data) {
            loadingChart.innerHTML = '<div class="alert alert-warning" role="alert">No chart data available</div>';
            return;
        }
        
        // Hide loading, show chart
        loadingChart.style.display = 'none';
        stockChart.style.display = 'block';
        
        const dates = chartConfig.data.dates;
        const prices = chartConfig.data.prices;
        const volumes = chartConfig.data.volumes;
        
        // Price trace
        const priceTrace = {
            x: dates,
            y: prices,
            type: 'scatter',
            mode: 'lines',
            name: 'Price',
            line: {
                color: '#2c3e50',
                width: 2
            }
        };
        
        // Create array of traces
        const traces = [priceTrace];
        
        // Add moving averages if available
        if (chartConfig.data.has_ma20) {
            traces.push({
                x: dates,
                y: chartConfig.data.ma20,
                type: 'scatter',
                mode: 'lines',
                name: '20-Day MA',
                line: {
                    color: '#3498db',
                    width: 1.5
                }
            });
        }
        
        if (chartConfig.data.has_ma50) {
            traces.push({
                x: dates,
                y: chartConfig.data.ma50,
                type: 'scatter',
                mode: 'lines',
                name: '50-Day MA',
                line: {
                    color: '#e74c3c',
                    width: 1.5
                }
            });
        }
        
        // Volume trace for subplot
        const volumeTrace = {
            x: dates,
            y: volumes,
            type: 'bar',
            name: 'Volume',
            marker: {
                color: '#34495e',
                opacity: 0.4
            },
            yaxis: 'y2'
        };
        
        traces.push(volumeTrace);
        
        // Create layout
        const layout = {
            title: {
                text: chartConfig.symbol + ' ' + chartConfig.period,
                font: {
                    size: 16
                }
            },
            xaxis: {
                title: 'Date',
                rangeslider: {
                    visible: true,
                    thickness: 0.05
                }
            },
            yaxis: {
                title: 'Price',
                side: 'left',
                showgrid: true,
                zeroline: true
            },
            yaxis2: {
                title: 'Volume',
                side: 'right',
                overlaying: 'y',
                showgrid: false,
                rangemode: 'nonnegative'
            },
            legend: {
                orientation: 'h',
                y: 1.1
            },
            height: 500,
            margin: {
                l: 50,
                r: 50,
                b: 50,
                t: 50,
                pad: 4
            },
            showlegend: true,
            hovermode: 'closest'
        };
        
        // Add a shape to highlight recommendation
        const recommendationColor = chartConfig.recommendation === 'BUY' ? '#27ae60' : 
                                   (chartConfig.recommendation === 'SELL' ? '#c0392b' : '#f39c12');
        
        layout.shapes = [{
            type: 'line',
            x0: dates[dates.length - 1],
            y0: prices[prices.length - 1],
            x1: dates[dates.length - 1],
            y1: prices[prices.length - 1] * 1.02,
            line: {
                color: recommendationColor,
                width: 3,
                dash: 'solid'
            }
        }];
        
        // Add annotation for recommendation
        layout.annotations = [{
            x: dates[dates.length - 1],
            y: prices[prices.length - 1] * 1.03,
            xref: 'x',
            yref: 'y',
            text: chartConfig.recommendation,
            showarrow: true,
            arrowhead: 2,
            arrowsize: 1,
            arrowwidth: 2,
            arrowcolor: recommendationColor,
            font: {
                color: recommendationColor,
                size: 12,
                weight: 'bold'
            },
            align: 'center',
            bgcolor: 'rgba(255, 255, 255, 0.8)',
            bordercolor: recommendationColor,
            borderwidth: 2,
            borderpad: 4,
            opacity: 0.8
        }];
        
        // Plot chart
        Plotly.newPlot('stockChart', traces, layout);
    }
});
