let chartInstance = null;

function initializeChart() {
    const ctx = document.getElementById('myChart').getContext('2d');
    
    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['间期', '前期', '中期', '后期', '末期', '细胞质分裂'],
            datasets: [
                {
                    label: 'DNA分子数',
                    data: [8, 8, 8, 8, 4, 4],
                    borderColor: '#FF6384',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 6,
                    pointBackgroundColor: '#FF6384',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverRadius: 8,
                    segment: {
                        borderDash: [0]
                    }
                },
                {
                    label: '姐妹染色单体数',
                    data: [0, 4, 4, 0, 0, 0],
                    borderColor: '#36A2EB',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 6,
                    pointBackgroundColor: '#36A2EB',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverRadius: 8,
                    segment: {
                        borderDash: [0]
                    }
                },
                {
                    label: '染色体数',
                    data: [4, 4, 4, 4, 8, 4],
                    borderColor: '#FFCE56',
                    backgroundColor: 'rgba(255, 206, 86, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 6,
                    pointBackgroundColor: '#FFCE56',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverRadius: 8,
                    segment: {
                        borderDash: [0]
                    }
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 13
                    },
                    borderColor: '#ddd',
                    borderWidth: 1,
                    cornerRadius: 4
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10,
                    ticks: {
                        stepSize: 2,
                        font: {
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                        drawBorder: true
                    },
                    title: {
                        display: true,
                        text: '数量',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    }
                },
                x: {
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        font: {
                            size: 12
                        }
                    }
                }
            },
            animation: {
                duration: 0
            }
        }
    });
}

function updateChart(phaseIndex, progress) {
    if (!chartInstance) return;
    
    // 根据进度更新数据点
    const allData = [
        { phase: [8, 0, 4], label: '间期' },
        { phase: [8, 4, 4], label: '前期' },
        { phase: [8, 4, 4], label: '中期' },
        { phase: [8, 4, 4], label: '后期' },
        { phase: [4, 0, 8], label: '末期' },
        { phase: [4, 0, 4], label: '细胞质分裂' }
    ];
    
    // 插值计算当前值
    let currentData = allData[phaseIndex].phase;
    
    if (phaseIndex < 5 && progress < 1) {
        const nextData = allData[phaseIndex + 1].phase;
        currentData = [
            currentData[0] + (nextData[0] - currentData[0]) * progress,
            currentData[1] + (nextData[1] - currentData[1]) * progress,
            currentData[2] + (nextData[2] - currentData[2]) * progress
        ];
    }
    
    // 添加强调点
    chartInstance.data.datasets[0].pointRadius = chartInstance.data.labels.map((_, i) => 
        i === phaseIndex ? 8 : 6
    );
    chartInstance.data.datasets[1].pointRadius = chartInstance.data.labels.map((_, i) => 
        i === phaseIndex ? 8 : 6
    );
    chartInstance.data.datasets[2].pointRadius = chartInstance.data.labels.map((_, i) => 
        i === phaseIndex ? 8 : 6
    );
    
    chartInstance.update('none');
}