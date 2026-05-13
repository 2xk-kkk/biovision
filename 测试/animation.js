class MitosisAnimation {
    constructor(canvasId, cellType = 'animal') {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.cellType = cellType;
        this.progress = 0; // 0-100
        this.isPlaying = false;
        this.animationFrameId = null;
        this.startTime = null;
        this.duration = 8000; // 8 seconds for full cycle
        
        // 细胞参数
        this.cellRadius = 80;
        this.chromosomeCount = 4; // 2对染色体 (为了演示简化)
        
        // 初始化坐标
        this.centerX = this.canvas.width / 2;
        this.centerY = this.canvas.height / 2;
        
        // 数据收集
        this.data = this.initializeData();
    }
    
    initializeData() {
        return {
            phases: ['间期', '前期', '中期', '后期', '末期', '细胞质分裂'],
            dna: [8, 8, 8, 8, 4, 4],
            sisters: [0, 4, 4, 0, 0, 0],
            chromosomes: [4, 4, 4, 4, 8, 4]
        };
    }
    
    update(progress) {
        this.progress = Math.min(progress, 100);
        this.draw();
        return this.getDataAtProgress();
    }
    
    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 绘制背景和标题
        this.drawBackground();
        
        // 根据进度绘制不同的有丝分裂阶段
        const phase = this.getPhase();
        this.drawPhase(phase);
        
        // 绘制阶段标签
        this.drawPhaseLabel(phase);
    }
    
    drawBackground() {
        // 绘制细胞质
        this.ctx.fillStyle = this.cellType === 'animal' ? '#fff5e6' : '#e8f5e9';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 绘制细胞膜/细胞壁
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 2;
        if (this.cellType === 'animal') {
            this.ctx.beginPath();
            this.ctx.arc(this.centerX, this.centerY, this.cellRadius + 50, 0, Math.PI * 2);
            this.ctx.stroke();
        } else {
            // 植物细胞（矩形）
            this.ctx.strokeRect(
                this.centerX - this.cellRadius - 50,
                this.centerY - this.cellRadius - 50,
                (this.cellRadius + 50) * 2,
                (this.cellRadius + 50) * 2
            );
        }
    }
    
    getPhase() {
        const phase = Math.floor((this.progress / 100) * 6);
        return Math.min(phase, 5);
    }
    
    drawPhase(phase) {
        switch(phase) {
            case 0: this.drawInterphase(); break;
            case 1: this.drawProphase(); break;
            case 2: this.drawMetaphase(); break;
            case 3: this.drawAnaphase(); break;
            case 4: this.drawTelophase(); break;
            case 5: this.drawCytokinesis(); break;
        }
    }
    
    drawInterphase() {
        // 间期：核膜完整，染色质分散
        this.drawNucleus();
        
        // 绘制分散的染色质
        this.ctx.fillStyle = 'rgba(100, 100, 200, 0.6)';
        for (let i = 0; i < 8; i++) {
            const angle = (i / 8) * Math.PI * 2;
            const x = this.centerX + Math.cos(angle) * 30;
            const y = this.centerY + Math.sin(angle) * 30;
            this.ctx.beginPath();
            this.ctx.arc(x, y, 4, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        // 绘制中心粒
        this.drawCentrioles(this.centerX, this.centerY);
    }
    
    drawProphase() {
        const progress = (this.progress % (100/6)) / (100/6);
        
        // 核膜消失
        const nucleusAlpha = Math.max(0, 1 - progress * 2);
        this.ctx.globalAlpha = nucleusAlpha;
        this.drawNucleus();
        this.ctx.globalAlpha = 1;
        
        // 染色体凝聚
        this.drawCondensedChromosomes(progress);
        
        // 纺锤体开始形成
        this.drawSpindle(progress);
        
        // 中心粒移动到两极
        const centrioleDistance = progress * 60;
        this.drawCentrioles(this.centerX - centrioleDistance, this.centerY - this.cellRadius * 0.5);
        this.drawCentrioles(this.centerX + centrioleDistance, this.centerY + this.cellRadius * 0.5);
    }
    
    drawMetaphase() {
        const progress = (this.progress % (100/6)) / (100/6);
        
        // 染色体在中赤道板排列
        this.drawAlignedChromosomes();
        
        // 纺锤体
        this.drawSpindle(1);
        
        // 中心粒在两极
        this.drawCentrioles(this.centerX - 60, this.centerY - this.cellRadius * 0.5);
        this.drawCentrioles(this.centerX + 60, this.centerY + this.cellRadius * 0.5);
    }
    
    drawAnaphase() {
        const progress = (this.progress % (100/6)) / (100/6);
        
        // 姐妹染色单体分离
        this.drawSeparatingChromosomes(progress);
        
        // 纺锤体
        this.drawSpindle(1);
        
        // 中心粒在两极
        this.drawCentrioles(this.centerX - 60, this.centerY - this.cellRadius * 0.5);
        this.drawCentrioles(this.centerX + 60, this.centerY + this.cellRadius * 0.5);
    }
    
    drawTelophase() {
        const progress = (this.progress % (100/6)) / (100/6);
        
        // 核膜重新形成
        const nucleusAlpha = progress;
        this.ctx.globalAlpha = nucleusAlpha;
        
        // 左核
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.arc(this.centerX - 50, this.centerY, 40, 0, Math.PI * 2);
        this.ctx.stroke();
        
        // 右核
        this.ctx.beginPath();
        this.ctx.arc(this.centerX + 50, this.centerY, 40, 0, Math.PI * 2);
        this.ctx.stroke();
        
        this.ctx.globalAlpha = 1;
        
        // 分离的染色体
        this.drawSeparatingChromosomes(1);
        
        // 纺锤体消失
        this.ctx.globalAlpha = Math.max(0, 1 - progress);
        this.drawSpindle(1);
        this.ctx.globalAlpha = 1;
    }
    
    drawCytokinesis() {
        const progress = (this.progress % (100/6)) / (100/6);
        
        // 左核
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.arc(this.centerX - 50, this.centerY, 40, 0, Math.PI * 2);
        this.ctx.stroke();
        
        // 右核
        this.ctx.beginPath();
        this.ctx.arc(this.centerX + 50, this.centerY, 40, 0, Math.PI * 2);
        this.ctx.stroke();
        
        if (this.cellType === 'animal') {
            // 动物细胞：缢裂
            const inchValue = 50 * progress;
            this.ctx.strokeStyle = 'rgba(200, 100, 100, 0.7)';
            this.ctx.lineWidth = 3;
            this.ctx.beginPath();
            this.ctx.arc(this.centerX, this.centerY, inchValue, 0, Math.PI * 2);
            this.ctx.stroke();
        } else {
            // 植物细胞：细胞板形成
            this.ctx.fillStyle = 'rgba(100, 200, 100, 0.5)';
            const cellPlateHeight = 3;
            this.ctx.fillRect(
                this.centerX - 60,
                this.centerY - cellPlateHeight / 2,
                120,
                cellPlateHeight
            );
        }
    }
    
    drawNucleus() {
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.arc(this.centerX, this.centerY, this.cellRadius, 0, Math.PI * 2);
        this.ctx.stroke();
        
        // 绘制核膜和核仁
        this.ctx.fillStyle = 'rgba(200, 200, 100, 0.3)';
        this.ctx.beginPath();
        this.ctx.arc(this.centerX, this.centerY, this.cellRadius, 0, Math.PI * 2);
        this.ctx.fill();
        
        // 核仁
        this.ctx.fillStyle = 'rgba(150, 150, 100, 0.6)';
        this.ctx.beginPath();
        this.ctx.arc(this.centerX, this.centerY, 15, 0, Math.PI * 2);
        this.ctx.fill();
    }
    
    drawCondensedChromosomes(progress) {
        const condensationProgress = progress;
        this.ctx.fillStyle = `rgba(100, 100, 200, ${0.4 + condensationProgress * 0.4})`;
        
        for (let i = 0; i < 4; i++) {
            const angle = (i / 4) * Math.PI * 2;
            const baseDistance = 30;
            const distance = baseDistance + (1 - condensationProgress) * 20;
            
            const x = this.centerX + Math.cos(angle) * distance;
            const y = this.centerY + Math.sin(angle) * distance;
            
            // 绘制X形染色体（由姐妹染色单体组成）
            const sisterDistance = condensationProgress * 8;
            
            // 左姐妹染色单体
            this.ctx.beginPath();
            this.ctx.ellipse(x - sisterDistance, y, 6 + condensationProgress * 4, 10 + condensationProgress * 5, angle, 0, Math.PI * 2);
            this.ctx.fill();
            
            // 右姐妹染色单体
            this.ctx.beginPath();
            this.ctx.ellipse(x + sisterDistance, y, 6 + condensationProgress * 4, 10 + condensationProgress * 5, angle, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }
    
    drawAlignedChromosomes() {
        this.ctx.fillStyle = 'rgba(100, 100, 200, 0.8)';
        
        for (let i = 0; i < 4; i++) {
            const y = this.centerY - 30 + (i * 20);
            
            // 左姐妹染色单体
            this.ctx.beginPath();
            this.ctx.ellipse(this.centerX - 8, y, 6, 10, 0, 0, Math.PI * 2);
            this.ctx.fill();
            
            // 右姐妹染色单体
            this.ctx.beginPath();
            this.ctx.ellipse(this.centerX + 8, y, 6, 10, 0, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }
    
    drawSeparatingChromosomes(progress) {
        this.ctx.fillStyle = 'rgba(100, 100, 200, 0.8)';
        
        // 上方4条染色体
        for (let i = 0; i < 4; i++) {
            const startY = this.centerY - 30 + (i * 20);
            const endY = this.centerY - this.cellRadius * 0.5 - 20;
            const y = startY + (endY - startY) * progress;
            
            this.ctx.beginPath();
            this.ctx.ellipse(this.centerX - 20, y, 5, 8, 0, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        // 下方4条染色体
        for (let i = 0; i < 4; i++) {
            const startY = this.centerY - 30 + (i * 20);
            const endY = this.centerY + this.cellRadius * 0.5 + 20;
            const y = startY + (endY - startY) * progress;
            
            this.ctx.beginPath();
            this.ctx.ellipse(this.centerX + 20, y, 5, 8, 0, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }
    
    drawSpindle(progress) {
        const spindle1X = this.centerX - 60;
        const spindle1Y = this.centerY - this.cellRadius * 0.5;
        const spindle2X = this.centerX + 60;
        const spindle2Y = this.centerY + this.cellRadius * 0.5;
        
        this.ctx.strokeStyle = `rgba(200, 100, 200, ${0.3 * progress})`;
        this.ctx.lineWidth = 1;
        
        // 纺锤体纤维
        for (let i = 0; i < 20; i++) {
            const angle = (i / 20) * Math.PI * 2;
            
            const x1 = spindle1X + Math.cos(angle) * 60;
            const y1 = spindle1Y + Math.sin(angle) * 60;
            const x2 = spindle2X + Math.cos(angle + Math.PI) * 60;
            const y2 = spindle2Y + Math.sin(angle + Math.PI) * 60;
            
            this.ctx.beginPath();
            this.ctx.moveTo(x1, y1);
            this.ctx.lineTo(x2, y2);
            this.ctx.stroke();
        }
    }
    
    drawCentrioles(x, y) {
        if (this.cellType === 'animal') {
            // 动物细胞有中心粒
            this.ctx.strokeStyle = 'rgba(200, 100, 100, 0.6)';
            this.ctx.lineWidth = 2;
            
            // 两个中心粒
            this.ctx.beginPath();
            this.ctx.arc(x - 5, y, 8, 0, Math.PI * 2);
            this.ctx.stroke();
            
            this.ctx.beginPath();
            this.ctx.arc(x + 5, y, 8, 0, Math.PI * 2);
            this.ctx.stroke();
        }
    }
    
    drawPhaseLabel(phase) {
        const labels = ['间期', '前期', '中期', '后期', '末期', '细胞质分裂'];
        const label = labels[phase];
        
        this.ctx.fillStyle = '#333';
        this.ctx.font = 'bold 16px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(label, this.canvas.width / 2, 30);
    }
    
    getDataAtProgress() {
        const phase = this.getPhase();
        const phaseProgress = (this.progress % (100/6)) / (100/6);
        
        let dnaCount = this.data.dna[phase];
        let sisterhood = this.data.sisters[phase];
        let chromosomeCount = this.data.chromosomes[phase];
        
        // 过渡动画
        if (phase < 5) {
            const nextPhase = phase + 1;
            dnaCount = this.data.dna[phase] + (this.data.dna[nextPhase] - this.data.dna[phase]) * phaseProgress;
            sisterhood = this.data.sisters[phase] + (this.data.sisters[nextPhase] - this.data.sisters[phase]) * phaseProgress;
            chromosomeCount = this.data.chromosomes[phase] + (this.data.chromosomes[nextPhase] - this.data.chromosomes[phase]) * phaseProgress;
        }
        
        return {
            phase: this.data.phases[phase],
            dna: Math.round(dnaCount),
            sisters: Math.round(sisterhood),
            chromosomes: Math.round(chromosomeCount)
        };
    }
    
    setCellType(cellType) {
        this.cellType = cellType;
        this.draw();
    }
    
    play() {
        if (this.isPlaying) return;
        this.isPlaying = true;
        this.startTime = Date.now() - (this.progress / 100) * this.duration;
        this.animate();
    }
    
    pause() {
        this.isPlaying = false;
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
        }
    }
    
    reset() {
        this.progress = 0;
        this.isPlaying = false;
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
        }
        this.draw();
    }
    
    animate() {
        if (!this.isPlaying) return;
        
        const elapsed = Date.now() - this.startTime;
        this.progress = (elapsed / this.duration) * 100;
        
        if (this.progress >= 100) {
            this.progress = 100;
            this.isPlaying = false;
        }
        
        this.draw();
        
        if (this.isPlaying) {
            this.animationFrameId = requestAnimationFrame(() => this.animate());
        }
    }
    
    setProgress(value) {
        this.progress = Math.max(0, Math.min(value, 100));
        this.draw();
    }
}