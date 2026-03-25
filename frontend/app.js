document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const rankingList = document.getElementById('ranking-list');
    const updateStatus = document.getElementById('update-status');

    let currentData = null;
    let activeSubTab = localStorage.getItem('activeSubTab') || 'strategy';
    let activeSeason = '전체';
    
    // 캘린더 날짜 상태
    let viewDate = new Date(2026, 2, 1); 

    // 탭 전환
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

    // 네비게이션
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
            if (updateStatus) updateStatus.textContent = `마지막 업데이트: ${currentData.last_updated}`;
            renderCalendar();
            renderEventDetails();
            renderRanking();
        } catch (error) {
            console.error('Data load error:', error);
        }
    }

    const parseDate = (str) => {
        if (!str) return null;
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

            events.filter(e => e.deadline && e.deadline.includes(dateStr)).forEach(d => {
                const bar = document.createElement('div');
                bar.className = 'deadline-bar';
                bar.textContent = `🚩 마감: ${d.name}`;
                eventWrapper.appendChild(bar);
            });

            dayEvents.forEach(e => {
                const bar = document.createElement('div');
                bar.className = 'event-bar';
                bar.textContent = e.name;
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
                <strong>${e.area} - ${e.name}</strong>
                <p>일정: ${e.schedule}</p>
                <div style="background:#F9F9F9; padding:10px; font-size:12px; margin-top:10px;">
                    ${e.scheme.replace(/\n/g, '<br>')}
                </div>
                <p style="color:#E74C3C; font-weight:bold; margin-top:10px;">마감기한: ${e.deadline}</p>
            `;
            detailsGrid.appendChild(card);
        });
    }

    function renderRanking() {
        if (!currentData || !rankingList) return;
        rankingList.innerHTML = '';

        const getDiffHtml = (diff) => {
            if (!diff || diff === 0) return '<span>-</span>';
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
                <div class="rank-badge">${r.rank === 999 ? '권외' : r.rank}</div>
                <div class="ranking-details">
                    <span class="product-code">#${r.code}</span>
                    <span class="season-badge ${r.season || 'default'}">${r.season || '기타'}</span>
                    <div class="product-name">${r.name}</div>
                    <div class="rank-fluctuations">
                        <span>어제대비 ${getDiffHtml(r.diff)}</span>
                        <span>지난주대비 ${getDiffHtml(r.week_diff || 0)}</span>
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
        tooltip.innerHTML = `<strong>${data.name}</strong><br>${data.schedule}`;
        tooltip.classList.remove('hidden');
        tooltip.style.left = (ev.pageX + 10) + 'px';
        tooltip.style.top = (ev.pageY + 10) + 'px';
    }
    function hideTooltip() { tooltip.classList.add('hidden'); }

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