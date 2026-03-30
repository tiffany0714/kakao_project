document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const updateStatus = document.getElementById('update-status');
    const rankingList = document.getElementById('ranking-list');

    let currentData = null;
    let activeSubTab = 'strategy';
    let activeSeason = '전체';
    let viewDate = new Date(2026, 2, 1); 

    const pastelPalette = ['#E0F2F1', '#E3F2FD', '#FCE4EC', '#F3E5F5', '#FFF3E0', '#FFF9C4', '#E8F5E9', '#F1F8E9'];

    const getPastelColor = (str) => {
        let hash = 0;
        for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
        return pastelPalette[Math.abs(hash) % pastelPalette.length];
    };

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.tab).classList.add('active');
        });
    });

    document.getElementById('prev-month-btn')?.addEventListener('click', () => {
        viewDate.setMonth(viewDate.getMonth() - 1);
        renderCalendar();
    });
    document.getElementById('next-month-btn')?.addEventListener('click', () => {
        viewDate.setMonth(viewDate.getMonth() + 1);
        renderCalendar();
    });

    async function loadData() {
        try {
            const response = await fetch(`data/current_data.json?v=${Date.now()}`);
            currentData = await response.json();
            if (updateStatus) updateStatus.textContent = `Update Status: ${currentData.last_updated}`;
            renderCalendar();
            renderEventDetails();
            renderRanking();
        } catch (error) { console.error('Data load error:', error); }
    }

    const parseDate = (str) => {
        if (!str || !str.includes('월')) return null;
        const mPart = str.split('월')[0];
        const dPart = str.split('월')[1]?.split('일')[0];
        return new Date(2026, parseInt(mPart) - 1, parseInt(dPart));
    };

    function renderCalendar() {
        const grid = document.getElementById('calendar-grid');
        const monthDisplay = document.getElementById('current-month-display');
        if (!grid || !monthDisplay) return;
        
        grid.innerHTML = '';
        const year = viewDate.getFullYear();
        const month = viewDate.getMonth();
        monthDisplay.textContent = `${year}년 ${month + 1}월`;

        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        
        // Prepare weeks
        const events = currentData?.events || [];
        const monthStart = new Date(year, month, 1);
        const monthEnd = new Date(year, month, daysInMonth);
        
        // Calculate weeks in month
        let currentDayPointer = new Date(year, month, 1 - firstDay);
        while (currentDayPointer <= monthEnd) {
            const weekRow = document.createElement('div');
            weekRow.className = 'calendar-week';
            
            // Render background cells for the week
            for (let i = 0; i < 7; i++) {
                const cell = document.createElement('div');
                cell.className = 'calendar-day-cell';
                if (currentDayPointer.getMonth() === month) {
                    cell.innerHTML = `<div class="day-number">${currentDayPointer.getDate()}</div>`;
                    
                    // Deadlines
                    const dateStr = `${currentDayPointer.getMonth() + 1}월 ${currentDayPointer.getDate()}일`;
                    events.filter(e => e.deadline && e.deadline.includes(dateStr)).forEach(d => {
                        const dp = document.createElement('div');
                        dp.className = 'deadline-pill';
                        dp.textContent = `🚩 마감: ${d.name}`;
                        cell.appendChild(dp);
                    });
                }
                weekRow.appendChild(cell);
                currentDayPointer.setDate(currentDayPointer.getDate() + 1);
            }

            // Render Events Layer for this week
            const weekEndPointer = new Date(currentDayPointer);
            weekEndPointer.setDate(weekEndPointer.getDate() - 1);
            const weekStartPointer = new Date(weekEndPointer);
            weekStartPointer.setDate(weekStartPointer.getDate() - 6);

            const eventLayer = document.createElement('div');
            eventLayer.className = 'week-events-layer';

            // Filter events that occur this week
            const weekEvents = events.filter(e => {
                const parts = (e.schedule || "").split('~').map(p => p.trim());
                const start = parseDate(parts[0]);
                const end = parts[1] ? parseDate(parts[1]) : start;
                return start && end && start <= weekEndPointer && end >= weekStartPointer;
            });

            // Tracking for stacking
            const tracks = [];

            weekEvents.forEach(e => {
                const parts = (e.schedule || "").split('~').map(p => p.trim());
                const start = parseDate(parts[0]);
                const end = parts[1] ? parseDate(parts[1]) : start;
                
                const effectiveStart = start < weekStartPointer ? weekStartPointer : start;
                const effectiveEnd = end > weekEndPointer ? weekEndPointer : end;
                
                const startCol = effectiveStart.getDay() + 1; // 1-indexed for grid
                const span = Math.round((effectiveEnd - effectiveStart) / (1000 * 60 * 60 * 24)) + 1;

                // Find first available track
                let trackIdx = tracks.findIndex(t => t < startCol);
                if (trackIdx === -1) {
                    tracks.push(startCol + span - 1);
                    trackIdx = tracks.length - 1;
                } else {
                    tracks[trackIdx] = startCol + span - 1;
                }

                const bar = document.createElement('div');
                bar.className = 'event-bar';
                bar.style.gridColumn = `${startCol} / span ${span}`;
                bar.style.gridRow = `${trackIdx + 1}`;
                bar.style.backgroundColor = getPastelColor(e.name);
                
                if (start < weekStartPointer) bar.classList.add('continued-left');
                if (end > weekEndPointer) bar.classList.add('continued-right');
                
                if (start >= weekStartPointer || start.getMonth() !== month) {
                    bar.textContent = e.name;
                }

                bar.addEventListener('mouseenter', (ev) => showTooltip(ev, e));
                bar.addEventListener('mouseleave', hideTooltip);
                eventLayer.appendChild(bar);
            });

            weekRow.appendChild(eventLayer);
            grid.appendChild(weekRow);
        }
    }

    function renderEventDetails() {
        const detailsGrid = document.getElementById('event-details');
        if (!detailsGrid) return;
        detailsGrid.innerHTML = '';
        (currentData?.events || []).forEach(e => {
            const card = document.createElement('div');
            card.className = 'event-card';
            card.innerHTML = `
                <span style="font-size:11px; color:#999; font-weight:800;">${e.area}</span>
                <div class="title-text">${e.name}</div>
                <div style="font-size:13px; margin-bottom:10px;"><strong>📅 일정:</strong> ${e.schedule}</div>
                <div class="scheme-box">${e.scheme.replace(/\n/g, '<br>')}</div>
                <p style="color:#E53935; font-size:13px; font-weight:800;">🏁 마감기한: ${e.deadline}</p>
            `;
            detailsGrid.appendChild(card);
        });
    }

    function renderRanking() {
        if (!currentData || !rankingList) return;
        rankingList.innerHTML = '';

        // 1. 비교할 날짜 설정 (어제, 7일 전)
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(today.getDate() - 1);
        const lastWeek = new Date(today);
        lastWeek.setDate(today.getDate() - 7);

        const formatDate = (d) => d.toISOString().split('T')[0];
        const yesterdayStr = formatDate(yesterday);
        const lastWeekStr = formatDate(lastWeek);

        // 2. 히스토리에서 과거 기록 찾기
        const history = currentData.history || [];
        const yesterdayData = history.find(h => h.date === yesterdayStr);
        const lastWeekData = history.find(h => h.date === lastWeekStr);

        // 3. 등수 차이 계산 함수
        const getDiffHtml = (currentRank, productCode, pastRecord) => {
            if (!pastRecord) return '<span style="color:#999">-</span>';
            
            const listName = activeSubTab === 'strategy' ? 'seasonal_ranking' : 'niece_ranking';
            const pastItem = pastRecord[listName]?.find(p => p.product_code === productCode);
            
            if (!pastItem) return '<span style="color:#ff9800">신규</span>';
            
            const diff = parseInt(pastItem.rank) - parseInt(currentRank);
            if (diff > 0) return `<span style="color:#e53935">▲${diff}</span>`;
            if (diff < 0) return `<span style="color:#1e88e5">▼${Math.abs(diff)}</span>`;
            return '<span style="color:#999">-</span>';
        };

        // 4. 아이템 필터링 및 화면 표시
        let items = [];
        if (activeSubTab === 'strategy') {
            items = (currentData.seasonal_ranking || []).filter(r => {
                if (activeSeason === '전체') return true;
                if (activeSeason === '봄/가을') return r.season === '봄' || r.season === '가을' || r.season === '봄/가을';
                return r.season === activeSeason;
            });
        } else {
            items = currentData.niece_ranking || [];
        }

        items.sort((a, b) => (parseInt(a.rank) || 999) - (parseInt(b.rank) || 999)).forEach(r => {
            const card = document.createElement('div');
            card.className = 'ranking-card';
            
            const dailyDiff = getDiffHtml(r.rank, r.product_code, yesterdayData);
            const weeklyDiff = getDiffHtml(r.rank, r.product_code, lastWeekData);

            card.innerHTML = `
                <div class="rank-num">${r.rank || '-'}</div>
                <div class="product-info">
                    <div style="font-size: 10px; color: #999; margin-bottom: 2px;">코드: ${r.product_code || '-'}</div>
                    <div class="name">${r.name}</div>
                    <div class="stats">
                        <span>어제대비 <b>${dailyDiff}</b></span>
                        <span style="margin-left:10px;">지난주대비 <b>${weeklyDiff}</b></span>
                    </div>
                </div>
                ${activeSubTab === 'strategy' ? `<div class="season-badge" style="background:${getPastelColor(r.season || '기타')}">${r.season || '기타'}</div>` : ''}
            `;
            rankingList.appendChild(card);
        });
    }


    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip hidden';
    document.body.appendChild(tooltip);

    function showTooltip(ev, data) {
    // 줄바꿈(\n)이 있다면 브라우저에서 보이도록 <br>로 바꿔서 넣어줍니다.
    const schemeText = data.scheme ? data.scheme.replace(/\n/g, '<br>') : "등록된 스킴 정보가 없습니다.";
    
    tooltip.innerHTML = schemeText; 
    tooltip.classList.remove('hidden');
    
    // 툴팁 위치 설정
    tooltip.style.left = (ev.pageX + 10) + 'px';
    tooltip.style.top = (ev.pageY + 10) + 'px';
    }
    function hideTooltip() { tooltip.classList.add('hidden'); }

    // Sub-tabs handling (Strategy / Niece)
    const subTabs = document.querySelector('.sub-tabs-container');
    if (subTabs) {
        subTabs.onclick = (e) => {
            if (e.target.dataset.sub) {
                document.querySelectorAll('.sub-tab-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                activeSubTab = e.target.dataset.sub;
                renderRanking();
            }
        };
    }

    // Season Filter handling (Strategy Tab Only)
    const strategyFilter = document.getElementById('strategy-filter-tabs');
    if (strategyFilter) {
        strategyFilter.onclick = (e) => {
            if (e.target.dataset.season) {
                document.querySelectorAll('.season-tab').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                activeSeason = e.target.dataset.season;
                renderRanking();
            }
        };
    }

    loadData();
});