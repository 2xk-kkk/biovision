/* ============================================================
   生物视界 · BioAgent —— 悬浮智能体宠物（当前阶段：仅图标）
   - 纯 CSS/SVG 生成 DNA 双螺旋，蓝色半透明玻璃小球
   - 可随意拖动，位置记忆在 localStorage
   - 后续阶段可在 window.BioAgent 上扩展对话/问答能力
   ============================================================ */
(function () {
  'use strict';

  var SIZE = 74;          // 必须与 agent.css 中 #bio-agent 的宽高一致
  var LS_KEY = 'biovision.bioagent.pos';

  var config = {
    tip: '生物智能体 · 开发中',
    onTap: null           // 后续接入点击行为（如弹出对话面板）
  };

  var svgNS = 'http://www.w3.org/2000/svg';

  function el(name, attrs, parent) {
    var node = document.createElement(name);
    for (var k in attrs) node.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(node);
    return node;
  }

  function svgEl(name, attrs, parent) {
    var node = document.createElementNS(svgNS, name);
    for (var k in attrs) node.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(node);
    return node;
  }

  /* ---------------- DNA 双螺旋几何 ---------------- */
  function buildHelix() {
    var BOX = 64, C = BOX / 2;     // 正方形 viewBox，整体倾斜后仍不被裁切
    var LEN = 50, AMP = 10;        // 轴向长度与振幅
    var TURNS = 1.5;               // 整圈数：两端收束干净，观感清爽
    var GAP = 1.6;                 // 碱基对中段氢键缺口半径
    var TILT = 22;                 // 倾斜角度(度)，让图标更有动势与科技感

    var rad = TILT * Math.PI / 180;
    var cosA = Math.cos(rad), sinA = Math.sin(rad);
    function rot(x, y) {   // 绕中心旋转
      return [
        C + (x - C) * cosA - (y - C) * sinA,
        C + (x - C) * sinA + (y - C) * cosA
      ];
    }

    // 沿竖直轴采样两条骨架后整体旋转（AMP 决定两链横向错开）
    var aPts = [], bPts = [], rungYs = [];
    for (var y = C - LEN / 2; y <= C + LEN / 2; y += 0.5) {
      var s = (y - (C - LEN / 2)) / LEN;
      var off = AMP * Math.sin(s * Math.PI * 2 * TURNS);
      aPts.push(rot(C - off, y));
      bPts.push(rot(C + off, y));
    }
    for (var ry = C - LEN / 2; ry <= C + LEN / 2; ry += 4) rungYs.push(ry);

    function path(pts) {
      var d = [];
      for (var i = 0; i < pts.length; i++) {
        d.push((i ? 'L' : 'M') + pts[i][0].toFixed(2) + ' ' + pts[i][1].toFixed(2));
      }
      return d.join(' ');
    }

    var svg = svgEl('svg', { viewBox: '0 0 ' + BOX + ' ' + BOX, 'aria-hidden': 'true' });
    var defs = svgEl('defs', {}, svg);
    svgEl('filter', { id: 'ba-glow', x: '-60%', y: '-60%', width: '220%', height: '220%' }, defs)
      .innerHTML = '<feGaussianBlur stdDeviation="1.1" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>';
    var g = svgEl('g', {}, svg);

    /* 1) 碱基对横档：细而透气，两侧断开留氢键缺口 */
    var rungD = [];
    for (var r = 0; r < rungYs.length; r++) {
      var yy = rungYs[r];
      var s2 = (yy - (C - LEN / 2)) / LEN;
      var o2 = AMP * Math.sin(s2 * Math.PI * 2 * TURNS);
      if (Math.abs(o2) < GAP + 0.4) continue;   // 靠近交叉点处跳过
      var q1 = rot(C - GAP, yy), q2 = rot(C + GAP, yy);
      var p1 = rot(C - o2, yy), p2 = rot(C + o2, yy);
      rungD.push('M' + p1[0].toFixed(2) + ' ' + p1[1].toFixed(2) + ' L' + q1[0].toFixed(2) + ' ' + q1[1].toFixed(2));
      rungD.push('M' + q2[0].toFixed(2) + ' ' + q2[1].toFixed(2) + ' L' + p2[0].toFixed(2) + ' ' + p2[1].toFixed(2));
    }
    svgEl('path', {
      d: rungD.join(' '), fill: 'none',
      stroke: 'rgba(125,211,252,0.5)', 'stroke-width': 1.2, 'stroke-linecap': 'round'
    }, g);

    /* 2) 两条骨架：外层宽幅低透明度 + 内芯亮线，形成霓虹光管质感 */
    function drawStrand(pts, outer, wOuter, inner, wInner) {
      svgEl('path', {
        d: path(pts), fill: 'none',
        stroke: outer, 'stroke-width': wOuter,
        'stroke-linecap': 'round', 'stroke-linejoin': 'round'
      }, g);
      svgEl('path', {
        d: path(pts), fill: 'none',
        stroke: inner, 'stroke-width': wInner,
        'stroke-linecap': 'round', 'stroke-linejoin': 'round'
      }, g);
    }
    drawStrand(bPts, 'rgba(59,130,246,0.10)', 6, 'rgba(255,255,255,0.6)', 2.2);   // 后链（半透明白，略暗以示前后）
    drawStrand(aPts, 'rgba(125,211,252,0.16)', 7, 'rgba(255,255,255,1)', 2.4);    // 前链（纯白带辉光）

    /* 3) 沿前链爬行的能量光点 */
    var dot = svgEl('circle', { r: 2.3, fill: '#ffffff', filter: 'url(#ba-glow)' }, svg);
    svgEl('animateMotion', {
      dur: '3.2s', repeatCount: 'indefinite', rotate: 'auto', path: path(aPts)
    }, dot);

    return svg;
  }

  /* ---------------- 初始化 ---------------- */
  function ensure() {
    var root = document.documentElement;
    if (root.querySelector('#bio-agent')) return;   // 防止重复注入

    var box = document.createElement('div');
    box.id = 'bio-agent';

    var halo = document.createElement('span');
    halo.className = 'ba-halo';

    var orb = document.createElement('button');
    orb.type = 'button';
    orb.className = 'ba-orb';
    orb.setAttribute('aria-label', '生物智能体');
    orb.appendChild(buildHelix());

    var tip = document.createElement('span');
    tip.className = 'ba-tip';
    tip.textContent = config.tip;
    orb.appendChild(tip);

    box.appendChild(halo);
    box.appendChild(orb);
    document.body.appendChild(box);

    return box;
  }

  function loadPos() {
    try {
      var raw = localStorage.getItem(LS_KEY);
      if (raw) return JSON.parse(raw);
    } catch (e) { /* 忽略隐私模式等场景 */ }
    return null;
  }

  function savePos(x, y) {
    try { localStorage.setItem(LS_KEY, JSON.stringify({ x: x, y: y })); } catch (e) { /* ignore */ }
  }

  function clamp(x, y, maxX, maxY) {
    return {
      x: Math.min(Math.max(x, 0), maxX),
      y: Math.min(Math.max(y, 0), maxY)
    };
  }

  function attachDrag(box, setPos) {
    var drag = false, moved = false, last = null;
    var orb = box.querySelector('.ba-orb');

    orb.addEventListener('pointerdown', function (e) {
      drag = true; moved = false;
      last = { px: e.clientX, py: e.clientY, ox: pos.x, oy: pos.y };
      box.classList.add('ba-dragging');
      if (orb.setPointerCapture) orb.setPointerCapture(e.pointerId);
      e.preventDefault();
    });

    orb.addEventListener('pointermove', function (e) {
      if (!drag || !last) return;
      var dx = e.clientX - last.px, dy = e.clientY - last.py;
      if (Math.abs(dx) + Math.abs(dy) > 2) moved = true;
      var p = clamp(last.ox + dx, last.oy + dy,
        (window.innerWidth || document.documentElement.clientWidth) - SIZE,
        (window.innerHeight || document.documentElement.clientHeight) - SIZE);
      setPos(p.x, p.y);
    });

    function end(e) {
      if (!drag) return;
      drag = false;
      box.classList.remove('ba-dragging');
      try { orb.releasePointerCapture(e.pointerId); } catch (err) { /* ignore */ }
      savePos(pos.x, pos.y);
      if (!moved && typeof config.onTap === 'function') config.onTap();
      last = null;
    }
    orb.addEventListener('pointerup', end);
    orb.addEventListener('pointercancel', end);
  }

  /* 图标工厂：供页面按需复用 DNA 螺旋图标（如 AI 对话页做头像） */
  window.BioAgentIcon = {
    create: function () { return buildHelix(); }
  };

  /* 图标-仅用模式：页面自行承载头像，跳过右下角可拖拽小球的注入 */
  if (document.documentElement.hasAttribute('data-bioagent-icon-only')) {
    return;
  }

  var box = ensure();
  if (!box) return;

  var pos = loadPos();
  var vw = window.innerWidth || document.documentElement.clientWidth;
  var vh = window.innerHeight || document.documentElement.clientHeight;
  if (!pos) {
    pos = { x: vw - SIZE - 26, y: vh - SIZE - 120 };   // 默认右下角
  } else {
    pos = clamp(pos.x, pos.y, vw - SIZE, vh - SIZE);
  }

  function setPos(x, y) {
    pos.x = x; pos.y = y;
    box.style.transform = 'translate(' + x + 'px,' + y + 'px)';
  }
  setPos(pos.x, pos.y);

  window.addEventListener('resize', function () {
    var p = clamp(pos.x, pos.y,
      (window.innerWidth || document.documentElement.clientWidth) - SIZE,
      (window.innerHeight || document.documentElement.clientHeight) - SIZE);
    if (p.x !== pos.x || p.y !== pos.y) setPos(p.x, p.y);
  });

  attachDrag(box, setPos);

  /* ---------------- 暴露 API（供后续智能体功能扩展） ---------------- */
  window.BioAgent = {
    config: config,
    el: box,
    setPosition: setPos,
    getPosition: function () { return { x: pos.x, y: pos.y }; },
    hide: function () { box.style.display = 'none'; },
    show: function () { box.style.display = ''; }
  };
})();
