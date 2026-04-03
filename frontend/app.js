document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const updateStatus = document.getElementById('update-status');
    const rankingList = document.getElementById('ranking-list');

    let currentData = null;
    let activeSubTab = 'strategy';
    let activeSeason = '전체';
    let viewDate = new Date(2026, 3, 1);

    const pastelPalette = ['#E0F2F1', '#E3F2FD', '#FCE4EC', '#F3E5F5', '#FFF3E0', '#FFF9C4', '#E8F5E9', '#F1F8E9'];
    const getPastelColor = (str) => {
        let hash = 0;
        for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
        return pastelPalette[Math.abs(hash) % pastelPalette.length];
    };

    // 툴팁
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip hidden';
    document.body.appendChild(tooltip);
    const showTooltip = (ev, data) => {
        tooltip.innerHTML = `<strong>${data.name}</strong><br>${(data.scheme || '정보 없음').replace(/\n/g, '<br>')}`;
        tooltip.classList.remove('hidden');
        tooltip.style.left = (ev.pageX + 15) + 'px';
        tooltip.style.top = (ev.pageY + 15) + 'px';
    };
    const hideTooltip = () => tooltip.classList.add('hidden');

    // 탭 이벤트
    const activateTab = (tabId) => {
        tabs.forEach(t => t.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        const targetBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
        const targetContent = document.getElementById(tabId);
        if (targetBtn) targetBtn.classList.add('active');
        if (targetContent) targetContent.classList.add('active');
        location.hash = tabId;
    };

    tabs.forEach(tab => {
        tab.addEventListener('click', () => activateTab(tab.dataset.tab));
    });

    const savedTab = location.hash.replace('#', '');
    if (savedTab && document.getElementById(savedTab)) {
        activateTab(savedTab);
    }

    document.getElementById('prev-month-btn')?.addEventListener('click', () => {
        viewDate.setMonth(viewDate.getMonth() - 1);
        renderCalendar();
    });
    document.getElementById('next-month-btn')?.addEventListener('click', () => {
        viewDate.setMonth(viewDate.getMonth() + 1);
        renderCalendar();
    });
    document.getElementById('today-btn')?.addEventListener('click', () => {
        viewDate = new Date();
        viewDate.setDate(1);
        renderCalendar();
    });

    async function loadData() {
        try {
            const res = await fetch(`data/current_data.json?v=${Date.now()}`);
            currentData = await res.json();
            if (updateStatus) updateStatus.textContent = `Update Status: ${currentData.last_updated}`;
            renderCalendar();
            renderEventDetails();
            renderRanking();
        } catch (e) { console.error('Data load error:', e); }
    }

    const parseDate = (str) => {
        if (!str) return null;
        if (str.includes('월')) {
            const [mPart, dPart] = str.split('월');
            const m = parseInt(mPart);
            const d = parseInt(dPart);
            if (!isNaN(m) && !isNaN(d)) return new Date(2026, m - 1, d);
        }
        const dotMatch = str.match(/(\d{4})[.\s]+(\d{1,2})[.\s]+(\d{1,2})/);
        if (dotMatch) return new Date(parseInt(dotMatch[1]), parseInt(dotMatch[2]) - 1, parseInt(dotMatch[3]));
        return null;
    };

    const toKey = (d) => `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    function renderCalendar() {
        const grid = document.getElementById('calendar-grid');
        const monthDisplay = document.getElementById('current-month-display');
        if (!grid || !monthDisplay) return;

        grid.innerHTML = '';
        const year = viewDate.getFullYear();
        const month = viewDate.getMonth();
        monthDisplay.textContent = `${year}년 ${month + 1}월`;

        const events = currentData?.events || [];
        const firstDay = new Date(year, month, 1).getDay();

        const parsedEvents = events.map(e => {
            const parts = e.schedule.split('~').map(p => p.trim());
            const start = parseDate(parts[0]);
            const end = parts[1] ? parseDate(parts[1]) : (start ? new Date(start) : null);
            return { ...e, start, end };
        }).filter(e => e.start && e.end);

        const deadlineMap = {};
        events.forEach(e => {
            if (!e.deadline) return;
            const d = parseDate(e.deadline.replace('마감: ', '').trim());
            if (!d) return;
            const k = toKey(d);
            if (!deadlineMap[k]) deadlineMap[k] = [];
            deadlineMap[k].push(e);
        });

        let cursor = new Date(year, month, 1 - firstDay);

        for (let w = 0; w < 6; w++) {
            const weekStart = new Date(cursor);
            const weekEnd = new Date(cursor);
            weekEnd.setDate(weekEnd.getDate() + 6);
            weekEnd.setHours(23, 59, 59);

            if (w >= 5 && weekStart.getMonth() !== month) break;

            const weekRow = document.createElement('div');
            weekRow.className = 'calendar-week';

            const cellCursor = new Date(cursor);
            for (let i = 0; i < 7; i++) {
                const cell = document.createElement('div');
                const isThisMonth = cellCursor.getMonth() === month;
                const isToday = toKey(cellCursor) === toKey(today);
                cell.className = 'calendar-day-cell' + (isThisMonth ? '' : ' other-month') + (isToday ? ' today' : '');

                const dayNum = document.createElement('div');
                dayNum.className = 'day-number' + (isToday ? ' today-num' : '');
                dayNum.textContent = cellCursor.getDate();
                cell.appendChild(dayNum);

                weekRow.appendChild(cell);
                cellCursor.setDate(cellCursor.getDate() + 1);
            }

            const layer = document.createElement('div');
            layer.className = 'week-events-layer';

            const weekEvents = parsedEvents.filter(e => e.start <= weekEnd && e.end >= weekStart);

            const deadlineBadges = [];
            for (let i = 0; i < 7; i++) {
                const d = new Date(cursor);
                d.setDate(d.getDate() + i);
                const k = toKey(d);
                if (deadlineMap[k] && d.getMonth() === month) {
                    deadlineMap[k].forEach(ev => {
                        deadlineBadges.push({ col: i + 1, name: ev.name });
                    });
                }
            }

            const deadlineCols = {};
            deadlineBadges.forEach(b => {
                if (!deadlineCols[b.col]) deadlineCols[b.col] = [];
                deadlineCols[b.col].push(b.name);
            });

            const maxDeadlineRows = Math.max(0, ...Object.values(deadlineCols).map(v => v.length));

            Object.entries(deadlineCols).forEach(([col, names]) => {
                names.forEach((name, idx) => {
                    const badge = document.createElement('div');
                    badge.className = 'deadline-badge';
                    badge.style.gridColumn = `${col} / span 1`;
                    badge.style.gridRow = idx + 1;
                    badge.textContent = `🚨 ${name}`;
                    layer.appendChild(badge);
                });
            });

            const barRowOffset = maxDeadlineRows;
            const tracks = [];

            weekEvents.forEach(e => {
                const eStart = e.start < weekStart ? weekStart : e.start;
                const eEnd = e.end > weekEnd ? weekEnd : e.end;
                const colStart = Math.round((eStart - weekStart) / 86400000) + 1;
                const colEnd = Math.round((eEnd - weekStart) / 86400000) + 1;
                const span = colEnd - colStart + 1;
                const isFirstWeek = e.start >= weekStart;

                let trackIdx = tracks.findIndex(t => t < colStart);
                if (trackIdx === -1) { tracks.push(colEnd); trackIdx = tracks.length - 1; }
                else tracks[trackIdx] = colEnd;

                const bar = document.createElement('div');
                bar.className = 'event-bar';
                bar.style.gridColumn = `${colStart} / span ${span}`;
                bar.style.gridRow = barRowOffset + trackIdx + 1;
                bar.style.backgroundColor = getPastelColor(e.name);
                bar.style.pointerEvents = 'auto';
                bar.textContent = isFirstWeek ? e.name : '';

                if (e.start < weekStart) bar.classList.add('continued-left');
                if (e.end > weekEnd) bar.classList.add('continued-right');

                bar.onmouseenter = (ev) => showTooltip(ev, e);
                bar.onmouseleave = hideTooltip;
                layer.appendChild(bar);
            });

            weekRow.appendChild(layer);
            grid.appendChild(weekRow);
            cursor.setDate(cursor.getDate() + 7);
        }
    }

    function renderEventDetails() {
        const container = document.getElementById('event-details');
        if (!container) return;
        container.innerHTML = '';

        const events = currentData?.events || [];

        const grouped = {};
        events.forEach(e => {
            const start = parseDate(e.schedule.split('~')[0].trim());
            const monthKey = start ? start.getMonth() + 1 : null;
            if (!monthKey) return;
            if (!grouped[monthKey]) grouped[monthKey] = [];
            grouped[monthKey].push(e);
        });

        const months = Object.keys(grouped).map(Number).sort((a, b) => a - b);
        if (months.length === 0) return;

        const currentMonth = new Date().getMonth() + 1;
        let activeIdx = months.includes(currentMonth)
            ? months.indexOf(currentMonth)
            : months.length - 1;

        const nav = document.createElement('div');
        nav.className = 'detail-month-nav';
        nav.innerHTML = `
            <button class="detail-month-arrow" id="detail-prev">◁</button>
            <span class="detail-month-label">📅 <strong id="detail-month-text">${months[activeIdx]}월</strong></span>
            <button class="detail-month-arrow" id="detail-next">▷</button>
        `;
        container.appendChild(nav);

        const cardArea = document.createElement('div');
        cardArea.id = 'detail-card-area';
        container.appendChild(cardArea);

        function renderMonthCards(idx) {
            const m = months[idx];
            document.getElementById('detail-month-text').textContent = `${m}월`;
            document.getElementById('detail-prev').disabled = idx === 0;
            document.getElementById('detail-next').disabled = idx === months.length - 1;

            cardArea.innerHTML = '';
            const grid = document.createElement('div');
            grid.className = 'detail-cards-grid';

            grouped[m].forEach(e => {
                const color = getPastelColor(e.name);
                const card = document.createElement('div');
                card.className = 'event-card';
                card.innerHTML = `
                    <div class="card-color-bar" style="background:${color};"></div>
                    <div class="card-body">
                        <span class="card-area">${e.area}</span>
                        <div class="card-title">${e.name}</div>
                        <div class="card-schedule">📅 ${e.schedule}</div>
                        <div class="scheme-box collapsed">${e.scheme.replace(/\n/g, '<br>')}</div>
                        <button class="scheme-toggle">더보기 ▾</button>
                        <p class="card-deadline">🚨 마감: ${e.deadline}</p>
                    </div>
                `;
                const schemeBox = card.querySelector('.scheme-box');
                const toggleBtn = card.querySelector('.scheme-toggle');
                toggleBtn.addEventListener('click', () => {
                    const isCollapsed = schemeBox.classList.toggle('collapsed');
                    toggleBtn.textContent = isCollapsed ? '더보기 ▾' : '접기 ▴';
                });
                grid.appendChild(card);
            });
            cardArea.appendChild(grid);
        }

        nav.querySelector('#detail-prev').addEventListener('click', () => {
            if (activeIdx > 0) { activeIdx--; renderMonthCards(activeIdx); }
        });
        nav.querySelector('#detail-next').addEventListener('click', () => {
            if (activeIdx < months.length - 1) { activeIdx++; renderMonthCards(activeIdx); }
        });

        renderMonthCards(activeIdx);
    }

    function renderRanking() {
        if (!currentData || !rankingList) return;
        rankingList.innerHTML = '';

        const rawItems = activeSubTab === 'strategy' ? (currentData.seasonal_ranking || []) : (currentData.niece_ranking || []);
        const items = rawItems.filter(r => {
            if (activeSeason === '전체') return true;
            const s = r.season || '봄/가을';
            return activeSeason === '봄/가을' ? ['봄', '가을', '봄/가을'].includes(s) : s === activeSeason;
        }).sort((a, b) => (parseInt(a.rank) || 999) - (parseInt(b.rank) || 999));

        const seasonMeta = {
            '봄/가을': { bg: '#FFF3E0', color: '#E65100' },
            '여름':    { bg: '#E3F2FD', color: '#1565C0' },
            '겨울':    { bg: '#EDE7F6', color: '#4527A0' },
            '사계절':  { bg: '#E8F5E9', color: '#2E7D32' },
            '기타':    { bg: '#F5F5F5', color: '#757575' },
        };

        const table = document.createElement('table');
        table.className = 'ranking-table';
        table.innerHTML = `
            <thead>
                <tr>
                    <th style="width:100px">순위</th>
                    <th style="width:80px">계절</th>
                    <th style="width:100px">상품코드</th>
                    <th style="width:500px">상품명</th>
                    <th style="width:300px">전략</th>
                </tr>
            </thead>
        `;
        const tbody = document.createElement('tbody');

        const allSorted = [...rawItems].sort((a, b) => (parseInt(a.rank) || 999) - (parseInt(b.rank) || 999));
        const top20 = allSorted.slice(0, 20);
        const seasonCount = {};
        const keywordCount = {};
        const keywords = ['세트', '원피스', '상하복', '구두', '슬립온', '패딩', '점퍼'];

        top20.forEach(p => {
            const s = p.season || '기타';
            seasonCount[s] = (seasonCount[s] || 0) + 1;
            keywords.forEach(k => { if (p.name.includes(k)) keywordCount[k] = (keywordCount[k] || 0) + 1; });
        });

        const topSeason = Object.entries(seasonCount).sort((a,b) => b[1]-a[1])[0]?.[0];
        const topKeyword = Object.entries(keywordCount).sort((a,b) => b[1]-a[1])[0]?.[0];

        const generateStrategy = (product) => {
            const tips = [];
            const myRank = parseInt(product.rank);
            const mySeason = product.season || '기타';
            const myName = product.name;

            if (topSeason && topSeason !== mySeason) {
                tips.push(`📌 상위권은 '${topSeason}' 상품이 ${seasonCount[topSeason]}개로 강세 — ${topSeason} 라인 보완 검토`);
            } else {
                tips.push(`✅ '${mySeason}' 계절 상품이 상위권에서 유리한 포지션`);
            }
            if (topKeyword && !myName.includes(topKeyword)) {
                tips.push(`🔑 상위권 키워드 '${topKeyword}' 상품이 ${keywordCount[topKeyword]}개 — 상품명/구성에 반영 검토`);
            }
            const above = top20.filter(p => parseInt(p.rank) < myRank);
            if (above.length > 0) {
                const aboveKeywords = keywords.filter(k => above.some(p => p.name.includes(k)) && !myName.includes(k));
                if (aboveKeywords.length > 0) {
                    tips.push(`⬆️ 앞순위 상품 키워드 '${aboveKeywords[0]}' 미포함 — 상품명 또는 구성 보완 시 순위 상승 가능`);
                }
            }
            return tips.slice(0, 3).join('\n');
        };

        items.forEach(r => {
            const s = r.season || '기타';
            const meta = seasonMeta[s] || seasonMeta['기타'];
            const strategy = generateStrategy(r);
            const diff = r.diff || '-';
            const weekDiff = r.week_diff || '-';
            const diffColor = diff.startsWith('+') ? '#27ae60' : diff.startsWith('-') ? '#e53935' : '#999';
            const weekDiffColor = weekDiff.startsWith('+') ? '#27ae60' : weekDiff.startsWith('-') ? '#e53935' : '#999';
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="rank-cell">
                    <div>${r.rank}</div>
                    <div style="font-size:11px; font-weight:600; margin-top:4px; color:${diffColor};">전일 ${diff}</div>
                    <div style="font-size:11px; font-weight:600; color:${weekDiffColor};">전주 ${weekDiff}</div>
                </td>
                <td><span class="season-chip" style="background:${meta.bg}; color:${meta.color}">${s}</span></td>
                <td class="code-cell">${r.product_code || '-'}</td>
                <td class="name-cell">${r.name}</td>
                <td class="strategy-cell">
                    <div class="strategy-result">${strategy.replace(/\n/g, '<br>')}</div>
                </td>
            `;
            tbody.appendChild(tr);
        });

        table.appendChild(tbody);
        rankingList.appendChild(table);
    }

    document.querySelector('.sub-tabs-container')?.addEventListener('click', (e) => {
        if (e.target.dataset.sub) {
            document.querySelectorAll('.sub-tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            activeSubTab = e.target.dataset.sub;
            renderRanking();
        }
    });

    document.getElementById('strategy-filter-tabs')?.addEventListener('click', (e) => {
        if (e.target.dataset.season) {
            document.querySelectorAll('.season-tab').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            activeSeason = e.target.dataset.season;
            renderRanking();
        }
    });

    document.addEventListener('click', async (e) => {
        if (e.target?.id === 'update-btn') {
            if (!confirm('최신 데이터를 업데이트하시겠습니까?')) return;

            const btn = document.getElementById('update-btn');
            const status = document.getElementById('update-status');
            btn.disabled = true;
            btn.textContent = '⏳ 업데이트 중...';
            status.textContent = '🔄 시작 중...';

            try {
                await fetch('/update', { method: 'POST' });
            } catch(e) {
                status.textContent = '❌ 서버 연결 실패';
                btn.disabled = false;
                btn.textContent = '🔄 업데이트';
                return;
            }

            let dots = 0;
            const loadingMsgs = ['📡 랭킹 데이터 수집 중', '🔍 상품 정보 분석 중', '💾 데이터 저장 중'];

            const poll = setInterval(async () => {
                try {
                    const res = await fetch('/update/status');
                    const data = await res.json();

                    if (data.logs.length > 0) {
                        status.textContent = data.logs[data.logs.length - 1];
                    } else {
                        dots = (dots + 1) % 4;
                        const msgIdx = Math.floor(Date.now() / 2000) % loadingMsgs.length;
                        status.textContent = loadingMsgs[msgIdx] + '.'.repeat(dots + 1);
                    }

                    if (!data.running) {
                        clearInterval(poll);
                        btn.disabled = false;
                        btn.textContent = '🔄 업데이트';
                        await loadData();
                        const now = new Date();
                        status.textContent = `✅ 완료 · ${now.toLocaleDateString('ko-KR')} ${now.toLocaleTimeString('ko-KR')}`;
                    }
                } catch(err) {
                    clearInterval(poll);
                    status.textContent = '❌ 상태 확인 실패';
                    btn.disabled = false;
                    btn.textContent = '🔄 업데이트';
                }
            }, 2000);
        }
    });

    loadData();
});