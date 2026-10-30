/* LeSunshine 顧問 — 讀 data/today.json，畫出四個分頁。沒有框架、沒有建置步驟。 */
(function () {
  'use strict';

  var params = new URLSearchParams(location.search);
  var TABS = ['today', 'week', 'rivals', 'roster'];
  var TITLES = { today: '今天', week: '本週', rivals: '宿敵', roster: '陣容' };
  var dataFile = params.get('data');
  if (!dataFile || !/^[\w.-]+\.json$/.test(dataFile)) dataFile = 'today.json';
  var DATA_URL = 'data/' + dataFile;
  // ?now=2026-10-31T10:00+08:00 可以模擬現在時間（測試用）
  var NOW_OFFSET = 0;
  (function () { var t = Date.parse(params.get('now') || ''); if (isFinite(t)) NOW_OFFSET = t - Date.now(); })();
  function now() { return Date.now() + NOW_OFFSET; }

  var state = {
    tab: TABS.indexOf(params.get('tab')) >= 0 ? params.get('tab') : (sget('tab') || 'today'),
    league: clampInt(params.get('league'), 0, 1, +(sget('league') || 0)),
    data: null, offline: false, loading: false, error: null
  };
  if (TABS.indexOf(state.tab) < 0) state.tab = 'today';

  var main = document.getElementById('main');
  var fresh = document.getElementById('freshLabel');
  var refreshBtn = document.getElementById('refreshBtn');

  // ---------- 小工具 ----------
  function sget(k) { try { return sessionStorage.getItem('fa:' + k); } catch (e) { return null; } }
  function sset(k, v) { try { sessionStorage.setItem('fa:' + k, v); } catch (e) {} }
  function isDone(id) { try { return localStorage.getItem('done:' + id) === '1'; } catch (e) { return false; } }
  function setDone(id, on) {
    try { if (on) localStorage.setItem('done:' + id, '1'); else localStorage.removeItem('done:' + id); } catch (e) {}
  }
  function clampInt(v, lo, hi, dflt) { var n = parseInt(v, 10); return isNaN(n) ? dflt : Math.max(lo, Math.min(hi, n)); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function isNum(v) { return typeof v === 'number' && isFinite(v); }
  function val(v) { return (v == null || v === '' || (typeof v === 'number' && !isFinite(v))) ? '—' : esc(v); }
  function pct(p) {
    if (!isNum(p)) return '—';
    if (p >= 1) return '100%';
    if (p <= 0) return '0%';
    return Math.max(1, Math.min(99, Math.round(p * 100))) + '%';
  }
  function arr(a) { return Array.isArray(a) ? a : []; }
  function probColor(p) { return !isNum(p) ? 'var(--punt)' : p >= 0.7 ? 'var(--lead)' : p >= 0.4 ? 'var(--swing)' : 'var(--behind)'; }

  var leagueIndex = {};
  function lgClass(key) { return 'lg-' + ((leagueIndex[key] != null ? leagueIndex[key] : 0) % 2); }
  function lgBadge(key, name) { return '<span class="lg ' + lgClass(key) + '"><span>' + esc(name || key) + '</span></span>'; }

  var ROLE = { start: '上先發', bench: '下板凳', add: '簽', drop: '放', il_in: '移入 IL', il_out: '移出 IL' };
  var TYPE = { lineup: '排先發', add: '簽人', il: '傷兵名單', trade: '交易', check: '確認' };
  var STATUS = { lead: '穩贏', swing: '搖擺', behind: '落後', punt: '放棄' };
  var ESPN_CODE = { GSW: 'gs', NOP: 'no', NYK: 'ny', SAS: 'sa', UTA: 'utah', WAS: 'wsh' };
  var AV_COLORS = ['#F2641A', '#4F5BFF', '#11965A', '#D98A00', '#C2417A', '#2E8FB8', '#7B4FE0', '#5B6475'];

  function initials(name) {
    var parts = String(name || '?').replace(/[^A-Za-zÀ-ɏ一-鿿' -]/g, '').split(/[\s-]+/).filter(Boolean);
    if (!parts.length) return '?';
    if (/[一-鿿]/.test(parts[0])) return parts[0].slice(0, 1);
    var f = parts[0][0], l = parts.length > 1 ? parts[parts.length - 1][0] : '';
    if (parts.length > 2 && /^(jr|sr|ii|iii|iv)\.?$/i.test(parts[parts.length - 1])) l = parts[parts.length - 2][0];
    return (f + l).toUpperCase();
  }
  function hash(s) { var h = 0; s = String(s || ''); for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return Math.abs(h); }

  // 頭貼：先畫縮寫底圖，圖片載入失敗就移除 <img>（不會出現破圖）
  function avatar(p, size) {
    size = size || 44;
    var bg = AV_COLORS[hash(p && p.name) % AV_COLORS.length];
    var img = (p && typeof p.headshot === 'string' && /^https?:\/\//.test(p.headshot))
      ? '<img class="hs" src="' + esc(p.headshot) + '" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer">' : '';
    return '<span class="av" style="width:' + size + 'px;height:' + size + 'px;--avbg:' + bg + ';--avs:' + size + 'px">' +
      '<span class="ini" aria-hidden="true">' + esc(initials(p && p.name)) + '</span>' + img + '</span>';
  }
  function teamLogo(team) {
    if (!team || !/^[A-Z]{2,4}$/.test(team)) return '';
    var code = ESPN_CODE[team] || team.toLowerCase();
    return '<span class="logo"><img class="tl" src="https://a.espncdn.com/i/teamlogos/nba/500/' + code + '.png" alt="" loading="lazy" referrerpolicy="no-referrer"></span>';
  }
  document.addEventListener('error', function (e) {
    var t = e.target;
    if (!t || t.tagName !== 'IMG') return;
    if (t.classList.contains('hs')) t.remove();
    else if (t.classList.contains('tl')) { var w = t.parentNode; if (w && w.parentNode) w.parentNode.removeChild(w); }
  }, true);

  function ringSVG(p, size, stroke, color, track) {
    var r = (size - stroke) / 2, c = 2 * Math.PI * r, f = isNum(p) ? Math.max(0, Math.min(1, p)) : 0;
    return '<svg viewBox="0 0 ' + size + ' ' + size + '" aria-hidden="true">' +
      '<circle cx="' + size / 2 + '" cy="' + size / 2 + '" r="' + r + '" fill="none" stroke="' + track + '" stroke-width="' + stroke + '"/>' +
      (f > 0 ? '<circle cx="' + size / 2 + '" cy="' + size / 2 + '" r="' + r + '" fill="none" stroke="' + color + '" stroke-width="' + stroke +
        '" stroke-linecap="round" stroke-dasharray="' + (c * f).toFixed(2) + ' ' + c.toFixed(2) + '"/>' : '') + '</svg>';
  }
  function gaugeSVG(p, color) {
    // 半圓儀表：中心 (60,60)、半徑 50
    var f = isNum(p) ? Math.max(0, Math.min(1, p)) : 0, len = Math.PI * 50;
    var d = 'M10 60 A50 50 0 0 1 110 60';
    return '<svg viewBox="0 0 120 68" aria-hidden="true">' +
      '<path d="' + d + '" fill="none" stroke="var(--track)" stroke-width="11" stroke-linecap="round"/>' +
      (f > 0 ? '<path d="' + d + '" fill="none" stroke="' + color + '" stroke-width="11" stroke-linecap="round" stroke-dasharray="' +
        (len * f).toFixed(2) + ' ' + len.toFixed(2) + '"/>' : '') + '</svg>';
  }
  function pips(used, total) {
    if (!isNum(total) || total <= 0 || total > 20) return '';
    var s = '<span class="pips" aria-hidden="true">';
    for (var i = 0; i < total; i++) s += '<i class="' + (isNum(used) && i < used ? 'on' : '') + '"></i>';
    return s + '</span>';
  }
  function wlt(o) {
    if (!o) return '—';
    return '<span class="num">' + val(o.w) + '<span class="sep">-</span>' + val(o.l) + '<span class="sep">-</span>' + val(o.t) + '</span>';
  }
  function wltPlain(o) { return o ? val(o.w) + '-' + val(o.l) + '-' + val(o.t) : '—'; }

  function countdown(iso) {
    var t = Date.parse(iso);
    if (!isFinite(t)) return '';
    var diff = t - now();
    if (diff <= 0) return '<span class="countdown past">已過截止</span>';
    var h = diff / 3600000;
    if (h > 48) return '';
    if (h < 1) return '<span class="countdown">剩 ' + Math.max(1, Math.round(diff / 60000)) + ' 分鐘</span>';
    return '<span class="countdown">還有 ' + Math.floor(h) + ' 小時</span>';
  }

  var WD = ['日', '一', '二', '三', '四', '五', '六'];
  function twTime(iso) {
    var t = Date.parse(iso);
    if (!isFinite(t)) return '';
    var d = new Date(t + 8 * 3600000); // 台北 UTC+8，用 UTC 欄位讀
    var hh = ('0' + d.getUTCHours()).slice(-2), mm = ('0' + d.getUTCMinutes()).slice(-2);
    return (d.getUTCMonth() + 1) + '/' + d.getUTCDate() + '（' + WD[d.getUTCDay()] + '）' + hh + ':' + mm;
  }

  var IC = {
    clock: '<svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2.4"/><path d="M12 7v5.2l3.2 2" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    hourglass: '<svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 3h11M6.5 21h11M7.5 3c0 4.5 4.5 6 4.5 9s-4.5 4.5-4.5 9M16.5 3c0 4.5-4.5 6-4.5 9s4.5 4.5 4.5 9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    up: '<svg width="14" height="14" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 16.5 10 10.5l3.5 3.5L20 7.5M14.5 7.5H20V13" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    check: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12.5 4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    chev: '<svg class="chev" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    danger: '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.5 2.8 19.5h18.4L12 3.5Z" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"/><path d="M12 10v4.2" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><circle cx="12" cy="17" r="1.3" fill="currentColor"/></svg>',
    warning: '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2.2"/><path d="M12 7.2v5.6" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><circle cx="12" cy="16.4" r="1.3" fill="currentColor"/></svg>',
    info: '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2.2"/><path d="M12 11v5.6" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><circle cx="12" cy="7.6" r="1.3" fill="currentColor"/></svg>',
    success: '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2.2"/><path d="m8 12.3 2.8 2.8L16.2 9.6" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    trophy: '<svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4h10v5a5 5 0 0 1-10 0V4ZM7 6H4v1.5A3.5 3.5 0 0 0 7.5 11M17 6h3v1.5a3.5 3.5 0 0 1-3.5 3.5M12 14v3.5M8.5 20.5h7M9.5 17.5h5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    refresh: '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 12a8 8 0 1 1-2.34-5.66" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M20 4v4.5h-4.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  };
  // 品牌插圖：太陽籃球
  function sunBall(cls) {
    var rays = '';
    for (var i = 0; i < 12; i++) {
      var a = (i + 0.5) * Math.PI / 6, c = Math.cos(a), s = Math.sin(a);
      rays += '<line x1="' + (50 + 32 * c).toFixed(1) + '" y1="' + (50 + 32 * s).toFixed(1) + '" x2="' + (50 + 41 * c).toFixed(1) + '" y2="' + (50 + 41 * s).toFixed(1) + '"/>';
    }
    return '<svg class="' + cls + '" viewBox="0 0 100 100" aria-hidden="true">' +
      '<defs><linearGradient id="sb" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFA247"/><stop offset="1" stop-color="#EE5A17"/></linearGradient>' +
      '<clipPath id="sbc"><circle cx="50" cy="50" r="24"/></clipPath></defs>' +
      '<g stroke="#FFC23D" stroke-width="4.4" stroke-linecap="round">' + rays + '</g>' +
      '<circle cx="50" cy="50" r="25" fill="url(#sb)" stroke="#0F1A3F" stroke-width="2"/>' +
      '<g clip-path="url(#sbc)" fill="none" stroke="#0F1A3F" stroke-width="2"><path d="M50 25v50M25 50h50"/><circle cx="93" cy="50" r="31"/><circle cx="7" cy="50" r="31"/></g></svg>';
  }

  // ---------- 今天 ----------
  function actionCard(a, done, kind) {
    kind = kind || '';
    var players = arr(a.players).map(function (p) {
      return '<span class="chip">' + avatar(p, 28) + '<span class="chip-name">' + esc(p.name) + '</span>' +
        (ROLE[p.role] ? '<span class="role role-' + esc(p.role) + '">' + ROLE[p.role] + '</span>' : '') + '</span>';
    }).join('');
    var impact = a.impact && a.impact.label ? '<div class="impact">' + IC.up + '<span>' + esc(a.impact.label) + '</span></div>' : '';
    var quiet = a.type === 'check';
    var later = kind === 'later', expired = kind === 'expired';
    var wait = later ? '<div class="wait">' + IC.hourglass + '<div><b>' + esc(twTime(a.earliest) || '') + ' 後才能做</b>' +
        (a.earliest_label && a.earliest ? '<span>' + esc(String(a.earliest_label).replace(/\s*[・（(]\s*約.*$/, '')) + '</span>' : (a.earliest_label ? '<span>' + esc(a.earliest_label) + '</span>' : '')) + '</div></div>'
      : (a.earliest_label && !done ? '<div class="earliest">' + IC.hourglass + '<span>最早：<b>' + esc(a.earliest_label) + '</b></span></div>' : '');
    return '<article class="card act' + (done ? ' done' : '') + (quiet ? ' quiet' : '') + (later ? ' later' : '') + (expired ? ' expired' : '') + '" data-id="' + esc(a.id) + '">' +
      '<button class="check" type="button" role="checkbox" aria-checked="' + (done ? 'true' : 'false') + '" aria-label="標記完成：' + esc(a.title) + '"><i>' + IC.check + '</i></button>' +
      '<div class="act-body">' +
        '<div class="act-meta">' + lgBadge(a.league, a.league_name) +
          (TYPE[a.type] ? '<span class="tag">' + TYPE[a.type] + '</span>' : '') +
          (a.priority === 'high' && !done && !quiet && !expired ? '<span class="tag hot">重要</span>' : '') + '</div>' +
        '<h3 class="act-title">' + esc(a.title) + '</h3>' +
        (later ? wait : '') +
        (a.deadline_label ? '<div class="deadline"><span class="dl">' + IC.clock + '<span>' + (later ? '截止 ' : '') + esc(a.deadline_label) + '</span></span>' + countdown(a.deadline) + '</div>' : '') +
        (later ? '' : wait) +
        (a.detail ? '<p class="detail">' + esc(a.detail) + '</p>' : '') +
        (players ? '<div class="chips">' + players + '</div>' : '') + impact +
      '</div></article>';
  }

  function sortActions(list) {
    return list.map(function (a, i) { return { a: a, i: i, t: Date.parse(a.deadline) }; })
      .sort(function (x, y) {
        var tx = isFinite(x.t) ? x.t : Infinity, ty = isFinite(y.t) ? y.t : Infinity;
        return tx - ty || x.i - y.i;
      }).map(function (x) { return x.a; });
  }

  function leagueSummary(L, idx) {
    var f = L.forecast || {}, p = f.win_prob;
    return '<button type="button" class="card lsum" data-goleague="' + idx + '">' +
      '<div class="lsum-top">' + lgBadge(L.key, L.name) + IC.chev + '</div>' +
      '<div class="lsum-main"><div class="lsum-score">' +
        '<div class="vs">對手 <b>' + esc(L.opponent || '—') + '</b></div>' +
        '<div class="score-big">' + wlt(L.score) + '</div>' +
        '<div class="score-sub">目前・' + esc((L.score && L.score.source_label) || '—') + '</div></div>' +
        '<div class="ring-col"><div class="ring">' + ringSVG(p, 78, 7, probColor(p), 'var(--track)') +
          '<div class="ring-num num">' + pct(p) + '<small>做完後勝率</small></div></div>' +
          (isNum(f.win_prob_no_action) ? '<div class="ring-cap num">不動：' + pct(f.win_prob_no_action) + '</div>' : '') + '</div></div>' +
      '<div class="lsum-foot"><span>預測結算 <b class="num">' + wltPlain(L.forecast) + '</b></span>' +
        '<span class="adds">' + pips(L.adds && L.adds.used, L.adds && L.adds.total) + 'Adds <b class="num">&nbsp;' + val(L.adds && L.adds.used) + '/' + val(L.adds && L.adds.total) + '</b></span></div>' +
      '</button>';
  }

  function alertsHTML(list) {
    return arr(list).map(function (al) {
      var lv = IC[al.level] ? al.level : 'info';
      return '<div class="card alert al-' + lv + '"><span class="alert-ic">' + IC[lv] + '</span><div class="alert-body">' +
        (al.league_name || al.league ? lgBadge(al.league, al.league_name) : '') +
        '<p class="alert-text">' + esc(al.text) + '</p></div></div>';
    }).join('');
  }

  function renderToday(d) {
    var acts = sortActions(arr(d.actions)), t0 = now();
    var open = [], later = [], expired = [], done = [];
    acts.forEach(function (a) {
      if (isDone(a.id)) return done.push(a);
      var dl = Date.parse(a.deadline), er = Date.parse(a.earliest);
      if (isFinite(dl) && dl <= t0) return expired.push(a);
      if (isFinite(er) && er > t0) return later.push(a);
      open.push(a);
    });
    later.sort(function (x, y) { return (Date.parse(x.earliest) || 0) - (Date.parse(y.earliest) || 0); });
    var total = acts.length, base = open.length + done.length;
    var h = '<section class="page">' +
      '<div class="page-head"><div class="eyebrow">' + esc(d.nba_day_label || d.nba_day || '') + '</div>' +
      '<h1 class="page-title">' + (open.length ? '今天要做的事' : '今天') + '</h1></div>';

    if (!open.length && !done.length) {
      var nLater = later.length;
      h += '<div class="hero calm"><div class="hero-row"><div class="hero-text">' +
        '<div class="hero-kicker">' + (nLater ? '比賽還沒打完' : '兩個聯盟都排好了') + '</div><div class="hero-big">' + (nLater ? '現在不用動' : '今天不用動') + ' <em>☀︎</em></div>' +
        '<div class="hero-kicker" style="margin-top:6px;font-weight:500">' +
        (nLater ? '有 ' + nLater + ' 件要等比賽打完才能做。' : '安心看球，有新狀況會再提醒你。') + '</div></div>' +
        sunBall('hero-sun') + '</div>' +
        (nLater && later[0].earliest ? '<div class="hero-next">' + IC.hourglass + '<span>下一件 <b>' + esc(twTime(later[0].earliest)) + ' 後</b></span></div>' : '') +
        '</div>';
    } else {
      var next = open.filter(function (a) { return Date.parse(a.deadline) > t0; })[0];
      h += '<div class="hero"><div class="hero-row"><div class="hero-text">' +
        (open.length ? '<div class="hero-kicker">現在還有</div><div class="hero-big"><em class="num">' + open.length + '</em> 件事要做</div>'
                     : '<div class="hero-kicker">現在能做的都做完了</div><div class="hero-big">做完了 <em>✓</em></div>') +
        '</div><div class="hero-ring">' + ringSVG(done.length / base, 76, 8, '#FFB22E', 'rgba(255,255,255,.14)') +
        '<div class="ring-num num">' + done.length + '/' + base + '<small>完成</small></div></div></div>' +
        (next && next.deadline_label ? '<div class="hero-next">' + IC.clock + '<span>最近截止 <b>' + esc(next.deadline_label) + '</b></span></div>'
          : (!open.length && later.length && later[0].earliest ? '<div class="hero-next">' + IC.hourglass + '<span>下一件 <b>' + esc(twTime(later[0].earliest)) + ' 後</b></span></div>' : '')) +
        '</div>';
    }
    if (open.length) {
      h += '<div class="section-h"><h2>待辦</h2><span class="aside">依截止時間排序</span></div>';
      h += open.map(function (a) { return actionCard(a, false); }).join('');
    }
    if (later.length) {
      h += '<div class="section-h"><h2>之後再做</h2><span class="aside">時間到才能動</span></div>';
      h += later.map(function (a) { return actionCard(a, false, 'later'); }).join('');
    }
    if (expired.length) {
      h += '<div class="done-h">已過截止 ' + expired.length + ' 件</div>';
      h += expired.map(function (a) { return actionCard(a, false, 'expired'); }).join('');
    }
    if (done.length) {
      h += '<div class="done-h">已完成 ' + done.length + ' 件</div>';
      h += done.map(function (a) { return actionCard(a, true); }).join('');
    }

    var leagues = arr(d.leagues);
    if (leagues.length) {
      h += '<div class="section-h"><h2>本週戰況</h2><span class="aside">點卡片看細節</span></div>';
      h += leagues.map(leagueSummary).join('');
    }
    if (arr(d.alerts).length) {
      h += '<div class="section-h"><h2>提醒</h2></div>' + alertsHTML(d.alerts);
    }
    return h + '</section>';
  }

  // ---------- 分段控制 ----------
  function segHTML(leagues) {
    return '<div class="seg" role="tablist" style="--n:' + leagues.length + '">' +
      '<span class="thumb" style="transform:translateX(' + (state.league * 100) + '%)"></span>' +
      leagues.map(function (L, i) {
        return '<button type="button" role="tab" aria-selected="' + (i === state.league) + '" class="' + (i === state.league ? 'on' : '') + '" data-league="' + i + '">' + esc(L.name || L.key) + '</button>';
      }).join('') + '</div>';
  }
  function curLeague(d) {
    var ls = arr(d.leagues);
    if (state.league >= ls.length) state.league = 0;
    return ls[state.league];
  }

  // ---------- 本週 ----------
  function catRow(c) {
    var st = STATUS[c.status] ? c.status : 'swing';
    var p = c.win_prob, mineWins = isNum(p) ? p >= 0.5 : null;
    return '<div class="cat s-' + st + '">' +
      '<div class="cat-name"><span class="cat-dot"></span><div class="cat-lbl"><b>' + esc(c.label || c.cat) + '</b>' +
        '<small>' + esc(c.cat) + '<span class="st">' + STATUS[st] + '</span></small></div></div>' +
      '<div class="pair now num"><div>' + val(c.mine) + '</div><div>' + val(c.opp) + '</div></div>' +
      '<div class="pair num"><div class="' + (mineWins === true ? 'w' : '') + '">' + val(c.mine_final) + '</div><div class="' + (mineWins === false ? 'w' : '') + '">' + val(c.opp_final) + '</div></div>' +
      '<div class="prob"><div class="prob-num num">' + pct(p) + '</div><div class="bar"><i style="width:' + (isNum(p) ? Math.round(p * 100) : 0) + '%"></i></div></div>' +
      '</div>';
  }
  function dayCell(dy, today) {
    var lbl = String(dy.label || ''), m = lbl.match(/^(週.)\s*(.*)$/);
    var wd = m ? m[1] : lbl, dt = m ? m[2] : (dy.date ? dy.date.slice(5).replace('-', '/') : '');
    var cls = dy.date === today ? ' today' : (dy.date && today && dy.date < today ? ' past' : '');
    var f = isNum(dy.playing) && isNum(dy.slots) && dy.slots > 0 ? Math.min(1, dy.playing / dy.slots) : 0;
    var openN = isNum(dy.open) ? dy.open : null;
    return '<div class="day' + cls + '">' +
      '<div class="day-wd">' + esc(dy.date === today ? '即將開打' : wd) + '</div><div class="day-dt num">' + esc(dt) + '</div>' +
      '<div class="day-meter"><i style="height:' + Math.round(f * 100) + '%"></i></div>' +
      '<div class="day-n num">' + val(dy.playing) + '<small>/' + val(dy.slots) + '</small></div>' +
      (cls === ' past' ? '' : openN ? '<span class="day-open num">空 ' + openN + '</span>' : '<span class="day-open zero">滿</span>') +
      '</div>';
  }
  function renderWeek(d) {
    var ls = arr(d.leagues);
    var h = '<section class="page"><div class="page-head"><div class="eyebrow">' + esc((curLeague(d) || {}).week_label || '') + '</div><h1 class="page-title">本週對戰</h1></div>';
    if (!ls.length) return h + emptyCard('還沒有本週資料') + '</section>';
    var L = curLeague(d), f = L.forecast || {}, sc = L.score || {};
    h += segHTML(ls);
    var src = sc.source === 'yahoo' ? ' yahoo' : '';
    h += '<div class="card match"><div class="match-teams">' +
      '<div class="team"><div class="team-badge me">我</div><div class="team-name">' + esc(L.team_name || '我的隊伍') + '</div></div>' +
      '<div><div class="match-score">' + wlt(sc) + '</div><div class="match-legend"><span>勝</span><span>敗</span><span>平</span></div></div>' +
      '<div class="team"><div class="team-badge op">' + esc(initials(L.opponent)) + '</div><div class="team-name">' + esc(L.opponent || '—') + '</div></div></div>' +
      (sc.source_label ? '<div class="src' + src + '"><i></i>' + esc(sc.source_label) + '</div>' : '') +
      '<div class="fc"><div class="fc-row"><span class="fc-label">預測結算<b class="num">' + wltPlain(f) + '</b></span><span class="fc-pct num" style="color:' + probColor(f.win_prob) + '">' + pct(f.win_prob) + '</span></div>' +
      '<div class="bar"><i style="width:' + (isNum(f.win_prob) ? Math.round(f.win_prob * 100) : 0) + '%;--bc:' + probColor(f.win_prob) + '"></i></div>' +
      '<div class="fc-note">本週勝率' + (isNum(f.win_prob_no_action) ? '・如果都不動：' + pct(f.win_prob_no_action) : '') + '</div></div></div>';

    var gl = L.games_left || {}, ad = L.adds || {};
    h += '<div class="kv"><div class="card"><div class="kv-l">剩餘出賽</div><div class="kv-v num">' + val(gl.mine) + ' <small>vs ' + val(gl.opp) + ' 場</small></div></div>' +
      '<div class="card"><div class="kv-l">Adds 已用</div><div class="kv-v num">' + val(ad.used) + '<small>/' + val(ad.total) + '</small> ' + pips(ad.used, ad.total) + '</div></div></div>';

    var cats = arr(L.categories);
    if (cats.length) {
      h += '<div class="section-h"><h2>比項</h2><span class="aside">上：我　下：對手</span></div>';
      h += '<div class="card cats"><div class="cat-h"><span>比項</span><span>目前</span><span>預測</span><span style="text-align:right">贏面</span></div>' +
        cats.map(catRow).join('') +
        '<div class="legend">' + ['lead', 'swing', 'behind', 'punt'].map(function (s) { return '<span class="s-' + s + '"><i></i>' + STATUS[s] + '</span>'; }).join('') + '</div></div>';
    }
    var days = arr(L.days);
    if (days.length) {
      h += '<div class="section-h"><h2>每天出賽</h2><span class="aside">有比賽人數 / 先發位</span></div>';
      h += '<div class="card"><div class="days">' + days.map(function (x) { return dayCell(x, d.nba_day); }).join('') + '</div>' +
        '<p class="days-note">「空」是先發位沒人可以上，簽人時優先補這些天。</p></div>';
    }
    return h + '</section>';
  }

  // ---------- 宿敵 ----------
  function renderRivals(d) {
    var rs = arr(d.rivals);
    var h = '<section class="page"><div class="page-head"><div class="eyebrow">季末目標</div><h1 class="page-title">宿敵追蹤</h1></div>';
    h += '<div class="card goal"><span class="goal-ic">' + IC.trophy + '</span><p><b>終極目標：</b>兩個聯盟的季末名次，都排在宿敵前面。</p></div>';
    if (!rs.length) return h + '<div style="margin-top:10px">' + emptyCard('還沒有宿敵模擬資料') + '</div></section>';
    h += '<div style="margin-top:12px">' + rs.map(function (r) {
      var p = r.beat_prob;
      return '<article class="card rival"><div class="rival-top">' + lgBadge(r.league, r.league_name) +
        (r.updated_label ? '<span class="upd">' + esc(r.updated_label) + '</span>' : '') + '</div>' +
        '<div class="rival-main"><div class="rival-name"><small>宿敵</small><b>' + esc(r.rival) + '</b>' +
        (r.beat_label && r.beat_label.indexOf(pct(p).replace('%', '')) < 0 ? '<p>' + esc(r.beat_label) + '</p>' : '<p>季末名次排在他前面的機率</p>') + '</div>' +
        '<div class="gauge">' + gaugeSVG(p, probColor(p)) + '<div class="gauge-num num" style="color:' + probColor(p) + '">' + pct(p) + '<small>贏他機率</small></div></div></div>' +
        (arr(r.notes).length ? '<ul class="notes">' + r.notes.map(function (n) { return '<li>' + esc(n) + '</li>'; }).join('') + '</ul>' : '') +
        '</article>';
    }).join('') + '</div>';
    return h + '</section>';
  }

  // ---------- 陣容 ----------
  function playerRow(p) {
    var inj = p.injury_label || p.injury;
    var dtd = /day|觀察|questionable|probable|成疑/i.test(String(p.injury || '') + String(p.injury_label || ''));
    var short = '', more = '';
    if (inj) {
      var m = String(inj).match(/^([^（(]+)[（(](.+)[）)]$/);
      short = m ? m[1].trim() : String(inj);
      more = m ? m[2].trim() : '';
      if (short.length > 6) { more = short; short = dtd ? '觀察' : '傷'; }
    }
    var meta = [p.team_zh || p.team, p.pos].filter(Boolean).map(esc).join(' · ');
    var gl = p.games_left, il = p.slot === 'il';
    return '<div class="pl"><span class="av-wrap">' + avatar(p, 44) + teamLogo(p.team) + '</span>' +
      '<div class="pl-info"><div class="pl-name"><b>' + esc(p.name) + '</b>' + (short ? '<span class="inj' + (dtd ? ' dtd' : '') + '">' + esc(short) + '</span>' : '') + '</div>' +
      '<div class="pl-meta">' + (meta || '—') + '</div>' +
      (isNum(p.rank) ? '<div class="pl-rank">聯盟價值排名 <b class="num">' + p.rank + '</b></div>' : '') +
      (more ? '<div class="inj-line' + (dtd ? ' dtd' : '') + '">' + esc(more) + '</div>' : '') + '</div>' +
      '<div class="gl' + (il || !isNum(gl) || gl === 0 ? ' zero' : '') + '"><b class="num">' + (il ? '—' : val(gl)) + '</b><small>本週剩</small></div></div>';
  }
  function renderRoster(d) {
    var ls = arr(d.leagues);
    var h = '<section class="page"><div class="page-head"><div class="eyebrow">' + esc((curLeague(d) || {}).week_label || '') + '</div><h1 class="page-title">我的陣容</h1></div>';
    if (!ls.length) return h + emptyCard('還沒有陣容資料') + '</section>';
    var L = curLeague(d);
    h += segHTML(ls);
    var ro = arr(L.roster), act = ro.filter(function (p) { return p.slot !== 'il'; }), il = ro.filter(function (p) { return p.slot === 'il'; });
    var sum = act.reduce(function (s, p) { return s + (isNum(p.games_left) ? p.games_left : 0); }, 0);
    h += '<div class="rsum"><span>球員 <b class="num">' + act.length + '</b> 人</span><span>本週還有 <b class="num">' + sum + '</b> 場</span></div>';
    h += act.length ? '<div class="card plist">' + act.map(playerRow).join('') + '</div>' : emptyCard('陣容是空的');
    if (il.length) {
      h += '<div class="section-h"><h2>傷兵名單 IL</h2><span class="aside">' + il.length + ' 人</span></div>';
      h += '<div class="card plist">' + il.map(playerRow).join('') + '</div>';
    }
    return h + '</section>';
  }

  function emptyCard(msg) { return '<div class="card empty-card"><b>' + esc(msg) + '</b><p>下次資料更新後就會出現。</p></div>'; }

  // ---------- 載入／錯誤 ----------
  function renderLoading() {
    main.innerHTML = '<section class="page" aria-busy="true"><div class="page-head"><div class="skel" style="width:46%;height:14px"></div>' +
      '<div class="skel" style="width:62%;height:30px;margin-top:10px"></div></div>' +
      '<div class="skel" style="height:128px;border-radius:22px"></div>' +
      '<div class="skel" style="height:150px;margin-top:22px;border-radius:18px"></div>' +
      '<div class="skel" style="height:150px;margin-top:10px;border-radius:18px"></div></section>';
  }
  function renderError() {
    main.innerHTML = '<section class="page state">' +
      '<svg class="state-art" viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="40" fill="var(--brand-soft)"/>' +
      '<path d="M26 50a34 34 0 0 1 48 0" fill="none" stroke="var(--brand)" stroke-width="5" stroke-linecap="round"/>' +
      '<path d="M36 60a20 20 0 0 1 28 0" fill="none" stroke="var(--brand)" stroke-width="5" stroke-linecap="round"/>' +
      '<circle cx="50" cy="69" r="4.5" fill="var(--brand)"/><path d="M30 30l40 40" stroke="var(--ink-3)" stroke-width="5" stroke-linecap="round"/></svg>' +
      '<h2>讀不到今天的資料</h2><p>可能是網路不穩，或資料正在更新。<br>稍等一下再試一次。</p>' +
      '<button class="btn" type="button" id="retryBtn">' + IC.refresh + '再試一次</button></section>';
    document.getElementById('retryBtn').addEventListener('click', function () { load(true); });
    fresh.textContent = '';
  }

  function render() {
    var d = state.data;
    document.querySelectorAll('.tabbar button').forEach(function (b) {
      var on = b.getAttribute('data-tab') === state.tab;
      b.classList.toggle('on', on);
      if (on) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current');
    });
    document.title = TITLES[state.tab] + '・LeSunshine 顧問';
    if (!d) return;
    leagueIndex = {};
    arr(d.leagues).forEach(function (L, i) { leagueIndex[L.key] = i; });
    var fn = { today: renderToday, week: renderWeek, rivals: renderRivals, roster: renderRoster }[state.tab];
    main.innerHTML = fn(d);
    var age = (now() - Date.parse(d.generated_at)) / 3600000;
    var stale = isFinite(age) && age > 6;
    var ageTxt = age >= 48 ? Math.floor(age / 24) + ' 天前更新' : Math.floor(age) + ' 小時前更新';
    fresh.textContent = (state.offline ? '離線・' : '') + (stale ? ageTxt : (d.generated_label || ''));
    fresh.title = d.generated_label || '';
    fresh.classList.toggle('offline', state.offline);
    fresh.classList.toggle('stale', stale && !state.offline);
  }

  var toastEl = null, toastTimer = null;
  function toast(msg) {
    if (!toastEl) { toastEl = document.createElement('div'); toastEl.className = 'toast'; toastEl.setAttribute('role', 'status'); document.body.appendChild(toastEl); }
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('show'); }, 2200);
  }

  function load(manual) {
    manual = manual === true;
    if (state.loading) return;
    var prevGen = state.data && state.data.generated_at;
    state.loading = true;
    refreshBtn.classList.add('spin');
    if (!state.data) renderLoading();
    fetch(DATA_URL, { cache: 'no-store' })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        state.offline = r.headers.get('X-From-Cache') === '1';
        return r.json();
      })
      .then(function (d) {
        if (!d || typeof d !== 'object') throw new Error('bad data');
        state.data = d; state.error = null; render();
        if (manual) toast(state.offline ? '離線中，顯示上次資料' : (prevGen && prevGen === d.generated_at ? '已是最新' : '已更新'));
      })
      .catch(function (e) {
        state.error = e;
        if (!state.data) renderError();
        else if (manual) toast('更新失敗，顯示上次資料');
      })
      .then(function () {
        state.loading = false;
        setTimeout(function () { refreshBtn.classList.remove('spin'); }, 300);
      });
  }

  function setTab(t) {
    if (TABS.indexOf(t) < 0) return;
    state.tab = t; sset('tab', t);
    render();
    window.scrollTo(0, 0);
    if (!state.data && !state.loading) load();
  }

  // ---------- 事件 ----------
  document.getElementById('tabbar').addEventListener('click', function (e) {
    var b = e.target.closest('button[data-tab]');
    if (b) setTab(b.getAttribute('data-tab'));
  });
  refreshBtn.addEventListener('click', function () { load(true); });
  main.addEventListener('click', function (e) {
    var chk = e.target.closest('.check');
    if (chk) {
      var card = chk.closest('.act'), id = card.getAttribute('data-id');
      var on = !isDone(id);
      setDone(id, on);
      card.classList.toggle('done', on);
      chk.setAttribute('aria-checked', String(on));
      setTimeout(function () { var y = window.scrollY; render(); window.scrollTo(0, y); }, 380);
      return;
    }
    var seg = e.target.closest('[data-league]');
    if (seg) { state.league = +seg.getAttribute('data-league'); sset('league', state.league); render(); return; }
    var go = e.target.closest('[data-goleague]');
    if (go) { state.league = +go.getAttribute('data-goleague'); sset('league', state.league); setTab('week'); }
  });
  var topbar = document.getElementById('topbar');
  window.addEventListener('scroll', function () { topbar.classList.toggle('scrolled', window.scrollY > 4); }, { passive: true });
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible' && state.data) load(); });

  render();
  load();

  if ('serviceWorker' in navigator && location.protocol !== 'file:' && params.get('nosw') !== '1') {
    window.addEventListener('load', function () { navigator.serviceWorker.register('sw.js').catch(function () {}); });
  }
})();
