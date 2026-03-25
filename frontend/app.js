document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const calendarDays = document.getElementById('calendar-days');
    const currentMonthLabel = document.getElementById('current-month');
    const eventDetailsContainer = document.getElementById('event-details');
    const rankingList = document.getElementById('ranking-list');
    const updateStatus = document.getElementById('update-status');
    const tooltip = document.getElementById('tooltip');
    const seasonFilterContainer = document.getElementById('strategy-filter-tabs'); // Fixed selector

    let currentData = null;
    let currentDate = new Date(); // Use actual current date
    
    let activeTab = localStorage.getItem('activeTab') || 'tab1'; 
    let activeSubTab = localStorage.getItem('activeSubTab') || 'strategy';
    let activeSeason = '전체';

    const parseDate = (str, y) => {
        if (!str) return null;
        const koMatch = str.match(/(\d+)월\s*(\d+)일/);
        if (koMatch) return new Date(y, parseInt(koMatch[1]) - 1, parseInt(koMatch[2]));
        return null;
    };

    function initUI() {
        tabs.forEach(t => {
            const isSel = t.dataset.tab === activeTab;
            t.classList.toggle('active', isSel);
            document.getElementById(t.dataset.tab)?.classList.toggle('active', isSel);
        });
        document.querySelectorAll('.sub-tab-btn').forEach(b => b.classList.toggle('active', b.dataset.sub === activeSubTab));
        toggleFilter();
    }

    function toggleFilter() {
        if (activeTab === 'tab3' && activeSubTab === 'strategy') {
            document.getElementById('strategy-filter-tabs')?.classList.remove('hidden');
        } else {
            document.getElementById('strategy-filter-tabs')?.classList.add('hidden');
        }
    }

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            activeTab = tab.dataset.tab;
            localStorage.setItem('activeTab', activeTab);
            initUI();
            if (activeTab === 'tab3') renderRanking();
        });
    });

    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('sub-tab-btn')) {
            activeSubTab = e.target.dataset.sub;
            localStorage.setItem('activeSubTab', activeSubTab);
            initUI();
            toggleFilter(); // NEW: Ensure filter visibility is updated
            renderRanking();
        }
    });

    document.querySelectorAll('.season-tab').forEach(b => {
        b.addEventListener('click', () => {
            activeSeason = b.dataset.season;
            document.querySelectorAll('.season-tab').forEach(btn => btn.classList.toggle('active', btn.dataset.season === activeSeason));
            renderRanking();
        });
    });


    // --- [복구] 캘린더 연속 바 렌더링 로직 ---
    function renderCalendar() {
        if (!currentData || !calendarDays) return;
        calendarDays.innerHTML = '';
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();
        currentMonthLabel.innerText = `${year}년 ${month + 1}월`;

        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const prevMonthLastDay = new Date(year, month, 0).getDate();

        for (let i = firstDay; i > 0; i--) {
            const div = document.createElement('div');
            div.className = 'day other-month';
            div.innerHTML = `<div class="day-num">${prevMonthLastDay - i + 1}</div>`;
            calendarDays.appendChild(div);
        }

        const monthEvents = (currentData.events || []).flatMap((ev, idx) => {
            const results = [];
            if (ev.schedule) {
                const pts = ev.schedule.split(/~|-/);
                if (pts.length === 2) {
                    const start = parseDate(pts[0], year);
                    const end = parseDate(pts[1], year);
                    if (start && end && start <= new Date(year, month + 1, 0) && end >= new Date(year, month, 1)) {
                        results.push({ ...ev, start, end, id: idx, type: 'event' });
                    }
                }
            }
            if (ev.deadline) {
                const dDate = parseDate(ev.deadline, year);
                if (dDate && dDate.getMonth() === month) {
                    results.push({ ...ev, name: `🚩마감: ${ev.name}`, start: dDate, end: dDate, id: idx, type: 'deadline' });
                }
            }
            return results;
        }).filter(e => e);

        const slots = Array.from({ length: daysInMonth + 1 }, () => []);
        monthEvents.forEach(ev => {
            const sDay = ev.start.getMonth() === month ? ev.start.getDate() : 1;
            const eDay = ev.end.getMonth() === month ? ev.end.getDate() : daysInMonth;
            ev.rs = sDay; ev.re = eDay;
            let slot = 0;
            while (true) {
                let ok = true;
                for (let d = sDay; d <= eDay; d++) if (slots[d][slot]) { ok = false; break; }
                if (ok) break; slot++;
            }
            for (let d = sDay; d <= eDay; d++) slots[d][slot] = ev;
            ev.slot = slot;
        });

        const maxS = Math.max(-1, ...slots.map(s => s.length - 1));
        for (let i = 1; i <= daysInMonth; i++) {
            const dayDiv = document.createElement('div');
            dayDiv.className = 'day';
            const isToday = new Date().toDateString() === new Date(year, month, i).toDateString();
            if (isToday) dayDiv.classList.add('today');
            
            dayDiv.innerHTML = `<div class="day-num">${i}</div>`;
            const evCont = document.createElement('div');
            evCont.className = 'day-events';
            for (let s = 0; s <= maxS; s++) {
                const ev = slots[i][s];
                const bar = document.createElement('div');
                if (ev) {
                    bar.className = `event-bar color-${ev.id % 5}`;
                    if (ev.type === 'deadline') bar.classList.add('deadline');
                    
                    if (i === ev.rs) { 
                        bar.classList.add('start-bar'); 
                        bar.innerText = ev.name; 
                    }
                    if (i === ev.re) bar.classList.add('end-bar');
                    if (i > ev.rs && i < ev.re) bar.classList.add('mid-bar');
                    
                    bar.onmouseenter = (e) => {
                        tooltip.innerHTML = `<strong>${ev.name}</strong><br><br>${(ev.scheme || '').replace(/\n/g, '<br>')}`; 
                        tooltip.classList.remove('hidden');
                        tooltip.style.left = e.clientX + 10 + 'px'; tooltip.style.top = e.clientY + 10 + 'px';
                    };
                    bar.onmousemove = (e) => {
                        tooltip.style.left = e.clientX + 10 + 'px'; tooltip.style.top = e.clientY + 10 + 'px';
                    };
                    bar.onmouseleave = () => tooltip.classList.add('hidden');
                } else { bar.className = 'event-bar empty'; }
                evCont.appendChild(bar);
            }
            dayDiv.appendChild(evCont); calendarDays.appendChild(dayDiv);
        }
    }

    // --- [원복] 어제 만족하셨던 행사 상세 내용 디자인 ---
    function renderDetails() {
        if (!currentData || !eventDetailsContainer) return;
        const today = new Date();
        const sortedEvents = [...currentData.events].sort((a, b) => {
            const dateA = parseDate(a.schedule ? a.schedule.split('~')[0] : '', currentDate.getFullYear());
            const dateB = parseDate(b.schedule ? b.schedule.split('~')[0] : '', currentDate.getFullYear());
            return (dateA || new Date(9999,0,1)) - (dateB || new Date(9999,0,1));
        });

        eventDetailsContainer.innerHTML = sortedEvents.map(event => {
            let isEnded = false;
            if (event.schedule) {
                const parts = event.schedule.split(/~|-/);
                if (parts.length === 2) {
                    const endDate = parseDate(parts[1], currentDate.getFullYear());
                    if (endDate) { endDate.setHours(23, 59, 59); if (today > endDate) isEnded = true; }
                }
            }
            const displayName = isEnded ? `${event.name} <span style="color:red; font-size:14px;">(종료)</span>` : event.name;
            return `
            <div class="event-card">
                <h3>${displayName}</h3>
                <p><span class="label">일정:</span> ${event.schedule}</p>
                <p><span class="label">마감일:</span> ${event.deadline}</p>
                <div class="scheme"><strong>행사 스킴:</strong><div class="scheme-lines">${(event.scheme || '').split('\n').map(line => `<div class="scheme-line">${line}</div>`).join('')}</div></div>
            </div>`;
        }).join('');
    }

    // --- [복구] 랭킹 분석 카드형 디자인 ---
    function renderRanking() {
        if (!currentData || !rankingList) return;
        let html = '<div class="ranking-list">';
        
        const diffSpan = (diff) => {
            if (diff > 0) return `<span class="up">▲${diff}</span>`;
            if (diff < 0) return `<span class="down">▼${Math.abs(diff)}</span>`;
            return `<span class="stay">-</span>`;
        };

        if (activeSubTab === 'strategy') {
            const filtered = (currentData.seasonal_ranking || []).filter(r => {
                if (activeSeason === '전체') return true;
                if (activeSeason === '봄/가을') return r.season === '봄' || r.season === '가을' || r.season === '봄/가을';
                if (activeSeason === '사계절') return r.season === '사계절';
                return r.season === activeSeason;
            });
            if (filtered.length === 0) {
                html += '<div class="no-data">해당 계절의 상품 데이터가 없습니다.</div>';
            }
            filtered.forEach(r => {
                html += `
                <div class="ranking-item">
                    <div class="rank-badge">${r.rank === 999 ? '권외' : r.rank}</div>
                    <div class="ranking-details">
                        <div class="product-header">
                            <span class="season-badge ${r.season.replace('/', '')}">${r.season}</span>
                            <span class="product-code">#${r.code}</span>
                        </div>
                        <div class="product-name">${r.name}</div>
                        <div class="rank-fluctuations">
                            <div class="fluct-info">
                                <span class="fluct-label">어제대비</span>
                                <span class="fluct-val">${diffSpan(r.diff_yesterday || 0)}</span>
                            </div>
                            <div class="fluct-info">
                                <span class="fluct-label">지난주대비</span>
                                <span class="fluct-val">${diffSpan(r.diff_last_week || 0)}</span>
                            </div>
                        </div>
                    </div>
                </div>`;
            });
        } else {
            const nieceData = currentData.niece_ranking || [];
            if (nieceData.length === 0) {
                html += '<div class="no-data">조카 선물 랭킹 데이터가 없습니다.</div>';
            }
            nieceData.forEach(r => {
                html += `
                <div class="ranking-item">
                    <div class="rank-badge">${r.rank}</div>
                    <img src="${r.img || ''}" class="ranking-thumb" onerror="this.style.display='none'">
                    <div class="ranking-details">
                        <div class="product-header">
                            <span class="product-code">#${r.code}</span>
                        </div>
                        <div class="product-name">${r.name}</div>
                        <div class="rank-fluctuations">
                            <div class="fluct-info">
                                <span class="fluct-label">어제대비</span>
                                <span class="fluct-val">${diffSpan(r.diff_yesterday || 0)}</span>
                            </div>
                            <div class="fluct-info">
                                <span class="fluct-label">지난주대비</span>
                                <span class="fluct-val">${diffSpan(r.diff_last_week || 0)}</span>
                            </div>
                        </div>
                    </div>
                </div>`;
            });
        }
        rankingList.innerHTML = html + '</div>';
    }

    async function fetchAll() {
        try {
            const res = await fetch(`./data/current_data.json?v=${Date.now()}`);
            currentData = await res.json();
            if(updateStatus) updateStatus.innerText = `마지막 업데이트: ${currentData.last_updated}`;
            renderCalendar(); renderDetails(); renderRanking();
        } catch (e) { console.error(e); }
    }

    document.getElementById('prev-month').onclick = () => { currentDate.setMonth(currentDate.getMonth() - 1); renderCalendar(); };
    document.getElementById('next-month').onclick = () => { currentDate.setMonth(currentDate.getMonth() + 1); renderCalendar(); };

    initUI(); fetchAll();
});