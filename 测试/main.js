let animation = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化动画
    animation = new MitosisAnimation('animationCanvas', 'animal');
    animation.draw();
    
    // 初始化图表
    initializeChart();
    
    // 绑定事件
    bindEvents();
});

function bindEvents() {
    // 细胞类型切换
    const cellTypeButtons = document.querySelectorAll('.cell-type-selector .btn');
    cellTypeButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            cellTypeButtons.forEach(b => b.classList.remove('btn-active'));
            e.target.classList.add('btn-active');
            
            const cellType = e.target.dataset.type;
            if (animation) {
                animation.setCellType(cellType);
            }
        });
    });
    
    // 播放/暂停按钮
    document.getElementById('playBtn').addEventListener('click', () => {
        if (animation) {
            animation.play();
        }
    });
    
    document.getElementById('pauseBtn').addEventListener('click', () => {
        if (animation) {
            animation.pause();
        }
    });
    
    document.getElementById('resetBtn').addEventListener('click', () => {
        if (animation) {
            animation.reset();
            document.getElementById('progressSlider').value = 0;
            updatePhaseLabel();
        }
    });
    
    // 进度条
    const progressSlider = document.getElementById('progressSlider');
    progressSlider.addEventListener('input', (e) => {
        if (animation) {
            animation.pause(); // 拖动时停止播放
            const progress = parseFloat(e.target.value);
            animation.setProgress(progress);
            updatePhaseLabel();
            updateChartHighlight();
        }
    });
    
    // 使用RAF实时更新进度条和图表
    setInterval(() => {
        if (animation && animation.isPlaying) {
            progressSlider.value = animation.progress;
            updatePhaseLabel();
            updateChartHighlight();
        }
    }, 50);
}

function updatePhaseLabel() {
    if (!animation) return;
    
    const data = animation.getDataAtProgress();
    const phaseLabel = document.getElementById('phaseLabel');
    phaseLabel.textContent = data.phase;
    
    // 更新图表
    const phase = animation.getPhase();
    const phaseProgress = (animation.progress % (100/6)) / (100/6);
    updateChart(phase, phaseProgress);
}

function updateChartHighlight() {
    if (!animation || !chartInstance) return;
    
    const phase = animation.getPhase();
    
    // 更新所有数据集的点半径以突出显示当前阶段
    chartInstance.data.datasets.forEach(dataset => {
        dataset.pointRadius = chartInstance.data.labels.map((_, i) => 
            i === phase ? 8 : 6
        );
    });
    
    chartInstance.update('none');
}