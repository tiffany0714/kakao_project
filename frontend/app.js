document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const rankingList = document.getElementById('ranking-list');
    const updateStatus = document.getElementById('update-status');

    let currentData = null;
    let activeSubTab = localStorage.getItem('activeSubTab') || 'strategy';
    let activeSeason = '전체';
    let viewDate = new Date(2026, 2, 1); 

    const pastelPalette = [
        '#D1E9FF', '#D1F2E1', '#FAD1E6', '#FFF9C4', '#E1D1F2', '#FFE4D1', '#E0F2F1', '#F1F8E9'
    ];

    const getPastelColor = (str) => {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
        }
        return pastelPalette[Math.abs(hash) % pastelPalette.length];
    };

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.tab).classList.add('active');
            localStorage.setItem('activeTab', tab.dataset.tab);
        });
    });

    const savedTab = localStorage.getItem('activeTab') || 'tab1';
    document.querySelector(`[data-tab="${savedTab}"]`)?.click();

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
        } catch (error) {
            console.error('Data load error:', error);
        }
    }

    const parseDate = (str) => {
        if (!str || !str.includes('월')) return null;
        const mPart = str.split('월')[0];
        const dPart = str.split('월')[1]?.split('일')[0];
        if (!mPart || !dPart) return null;
        return new Date(2026, parseInt(mPart) - 1, parseInt(dPart));
    };

    function renderCalendar() {
        const calendarDays = document.getElementById('calendar-days');
        const monthDisplay = document.getElementById('current-month-display');
        if (!calendarDays || !monthDisplay) return;
        
        calendarDays.innerHTML = '';
        const year = viewDate.getFullYear();
        const month = viewDate.getMonth();
        monthDisplay.textContent = `${year}년 ${month + 1}월`;

        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();

        for (let i = 0; i < firstDay; i++) {
            const empty = document.createElement('div');
            empty.className = 'calendar-day empty';
            calendarDays.appendChild(empty);
        }

        const events = currentData?.events || [];
        
        for (let day = 1; day <= daysInMonth; day++) {
            const current = new Date(year, month, day);
            const dateStr = `${month + 1}월 ${day}일`;
            
            const dayEvents = events.filter(e => {
                const schedule = e.schedule || "";
                if (schedule.includes('~')) {
                    const parts = schedule.split('~').map(p => p.trim());
                    const start = parseDate(parts[0]);
                    const end = parseDate(parts[1]);
                    return start && end && current >= start && current <= end;
                }
                return schedule.includes(dateStr);
            });

            const cell = document.createElement('div');
            cell.className = 'calendar-day';
            cell.innerHTML = `<div class="day-num">${day}</div>`;
            const eventWrapper = document.createElement('div');
            eventWrapper.className = 'event-wrapper';

            // 마감 표시
            events.filter(e => e.deadline && e.deadline.includes(dateStr)).forEach(d => {
                const bar = document.createElement('div');
                bar.className = 'deadline-bar';
                bar.textContent = `🚩 마감: ${d.name}`;
                eventWrapper.appendChild(bar);
            });

            // 이벤트 바 (Google 스타일 Spanning logic)
            dayEvents.forEach(e => {
                const bar = document.createElement('div');
                bar.className = 'event-bar';
                bar.style.backgroundColor = getPastelColor(e.name);
                
                if (e.schedule.includes('~')) {
                    const parts = e.schedule.split('~').map(p => p.trim());
                    const start = parseDate(parts[0]);
                    const end = parseDate(parts[1]);
                    
                    const isStart = current.getTime() === start?.getTime();
                    const isEnd = current.getTime() === end?.getTime();
                    
                    bar.classList.add('continued');
                    if (isStart) {
                        bar.classList.add('start');
                        bar.textContent = e.name;
                    }
                    if (isEnd) bar.classList.add('end');
                } else {
                    bar.textContent = e.name;
                    bar.classList.add('start', 'end'); // 단일 일정도 시작/끝 패딩/코너 적용
                }

                bar.addEventListener('mouseenter', (ev) => showTooltip(ev, e));
                bar.addEventListener('mouseleave', hideTooltip);
                eventWrapper.appendChild(bar);
            });

            cell.appendChild(eventWrapper);
            calendarDays.appendChild(cell);
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
                <div class="event-area">${e.area}</div>
                <div class="event-title">${e.name}</div>
                <p><strong>📅 일정:</strong> ${e.schedule}</p>
                <div class="scheme-box">
                    ${e.scheme.replace(/\n/g, '<br>')}
                </div>
                <div class="deadline-pill">⏰ 마감: ${e.deadline}</div>
            `;
            detailsGrid.appendChild(card);
        });
    }

    function renderRanking() {
        if (!currentData || !rankingList) return;
        rankingList.innerHTML = '';

        const getDiffHtml = (diff) => {
            if (!diff || diff === 0) return '<span class="stay">-</span>';
            return diff > 0 ? `<span class="up">▲${diff}</span>` : `<span class="down">▼${Math.abs(diff)}</span>`;
        };

        let items = [];
        if (activeSubTab === 'strategy') {
            document.getElementById('strategy-filter-tabs').style.display = 'flex';
            items = (currentData.seasonal_ranking || []).filter(r => {
                if (activeSeason === '전체') return true;
                if (activeSeason === '봄/가을') return r.season === '봄' || r.season === '가을' || r.season === '봄/가을';
                return r.season === activeSeason;
            });
        } else {
            document.getElementById('strategy-filter-tabs').style.display = 'none';
            items = currentData.niece_ranking || [];
        }

        items.sort((a,b) => (a.rank || 999) - (b.rank || 999)).forEach(r => {
            const card = document.createElement('div');
            card.className = 'ranking-card';
            card.innerHTML = `
                <div class="rank-badge">${r.rank === 999 ? '-' : r.rank}</div>
                <div class="ranking-details">
                    <span class="season-badge" style="background:${getPastelColor(r.season || '기타')}">${r.season || '기타'}</span>
                    <div class="product-info">
                        <div class="product-name">${r.name}</div>
                        <div class="product-code">#${r.code || '000000'}</div>
                    </div>
                    <div class="rank-stats">
                        <div class="stat-box">
                            <span class="stat-label">DAILY DIFF</span>
                            <span class="stat-val">${getDiffHtml(r.diff)}</span>
                        </div>
                        <div class="stat-box">
                            <span class="stat-label">WEEKLY DIFF</span>
                            <span class="stat-val">${getDiffHtml(r.week_diff || 0)}</span>
                        </div>
                    </div>
                </div>
            `;
            rankingList.appendChild(card);
        });
    }

    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip hidden';
    document.body.appendChild(tooltip);

    function showTooltip(ev, data) {
        tooltip.innerHTML = `<strong>${data.name}</strong><br><small>${data.schedule}</small>`;
        tooltip.classList.remove('hidden');
        tooltip.style.left = (ev.pageX + 10) + 'px';
        tooltip.style.top = (ev.pageY + 10) + 'px';
    }
    function hideTooltip() { tooltip.classList.add('hidden'); }

    // Sub-tabs handling
    document.querySelector('.sub-tabs-container').onclick = (e) => {
        if (e.target.dataset.sub) {
            document.querySelectorAll('.sub-tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            activeSubTab = e.target.dataset.sub;
            renderRanking();
        }
    };
    document.getElementById('strategy-filter-tabs').onclick = (e) => {
        if (e.target.dataset.season) {
            document.querySelectorAll('.season-tab').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            activeSeason = e.target.dataset.season;
            renderRanking();
        }
    };

    loadData();
});