document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const rankingList = document.getElementById('ranking-list');
    const updateStatus = document.getElementById('update-status');

    let currentData = null;
    let activeSubTab = localStorage.getItem('activeSubTab') || 'strategy';
    let activeSeason = '전체';
    
    // 캘린더 날짜 상태
    let viewDate = new Date(2026, 2, 1); // 기본 3월로 시작

    // 탭 전환 로직
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

    // 캘린더 네비게이션
    document.getElementById('prev-month-btn')?.addEventListener('click', () => {
        viewDate.setMonth(viewDate.getMonth() - 1);
        renderCalendar();
    });
    document.getElementById('next-month-btn')?.addEventListener('click', () => {
        viewDate.setMonth(viewDate.getMonth() + 1);
        renderCalendar();
    });

    // 데이터 로드 및 렌더링
    async function loadData() {
        try {
            const response = await fetch(`data/current_data.json?v=${Date.now()}`);
            currentData = await response.json();
            
            if (updateStatus) {
                updateStatus.textContent = `최근 업데이트: ${currentData.last_updated}`;
            }

            renderCalendar();
            renderEventDetails();
            renderRanking();
        } catch (error) {
            console.error('데이터 로드 실패:', error);
            if (updateStatus) updateStatus.textContent = '데이터 로드 실패';
        }
    }

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

        // 빈 칸 추가
        for (let i = 0; i < firstDay; i++) {
            const empty = document.createElement('div');
            empty.className = 'calendar-day empty';
            calendarDays.appendChild(empty);
        }

        const events = currentData?.events || [];
        
        for (let day = 1; day <= daysInMonth; day++) {
            const dateStr = `${month + 1}월 ${day}일`;
            
            // 당일 진행중인 이벤트 필터링 (연속 바 로직 개선)
            const dayEvents = events.filter(e => {
                const schedule = e.schedule || "";
                if (schedule.includes('~')) {
                    const parts = schedule.split('~').map(p => p.trim());
                    // 멀티 월 처리 (예: 3월 16일 ~ 4월 5일)
                    const parseDate = (str) => {
                        const m = parseInt(str.split('월')[0]);
                        const d = parseInt(str.split('월')[1].split('일')[0]);
                        return new Date(2026, m - 1, d);
                    };
                    const start = parseDate(parts[0]);
                    const end = parseDate(parts[1]);
                    const current = new Date(year, month, day);
                    return current >= start && current <= end;
                }
                return schedule.includes(dateStr);
            });

            const deadlines = events.filter(e => e.deadline && e.deadline.includes(dateStr));
            
            const cell = document.createElement('div');
            cell.className = 'calendar-day';
            cell.innerHTML = `<div class="day-num">${day}</div>`;

            const eventWrapper = document.createElement('div');
            eventWrapper.className = 'event-wrapper';

            // 마감 표시
            deadlines.forEach(d => {
                const deadlineTag = document.createElement('div');
                deadlineTag.className = 'deadline-bar';
                deadlineTag.textContent = `🚩마감: ${d.name}`;
                deadlineTag.addEventListener('mouseenter', (e) => showTooltip(e, d));
                deadlineTag.addEventListener('mouseleave', hideTooltip);
                eventWrapper.appendChild(deadlineTag);
            });

            // 이벤트 바
            dayEvents.forEach(e => {
                const startStr = e.schedule.includes('~') ? e.schedule.split('~')[0].trim() : e.schedule;
                const isStart = startStr === dateStr;
                
                const eventBar = document.createElement('div');
                eventBar.className = 'event-bar';
                if (isStart) eventBar.textContent = e.name;
                
                eventBar.addEventListener('mouseenter', (ev) => showTooltip(ev, e));
                eventBar.addEventListener('mouseleave', hideTooltip);
                eventWrapper.appendChild(eventBar);
            });

            cell.appendChild(eventWrapper);
            calendarDays.appendChild(cell);
        }
    }

    function renderEventDetails() {
        const detailsGrid = document.getElementById('event-details');
        if (!detailsGrid) return;
        detailsGrid.innerHTML = '';

        const events = currentData?.events || [];
        events.forEach(e => {
            const card = document.createElement('div');
            card.className = 'event-card slide-up';
            card.innerHTML = `
                <div class="event-area">${e.area}</div>
                <div class="event-title">${e.name}</div>
                <div class="event-info"><strong>📅 기간:</strong> ${e.schedule}</div>
                <div class="event-info"><strong>📜 내용:</strong> ${e.scheme.replace(/\n/g, '<br>')}</div>
                <div class="event-deadline">⏰ 마감기한: ${e.deadline}</div>
            `;
            detailsGrid.appendChild(card);
        });
    }

    function renderRanking() {
        if (!currentData || !rankingList) return;
        rankingList.innerHTML = '';

        const subTabContainer = document.querySelector('.sub-tabs-container');
        if (subTabContainer) {
            subTabContainer.onclick = (e) => {
                if (e.target.classList.contains('sub-tab-btn')) {
                    document.querySelectorAll('.sub-tab-btn').forEach(b => b.classList.remove('active'));
                    e.target.classList.add('active');
                    activeSubTab = e.target.dataset.sub;
                    localStorage.setItem('activeSubTab', activeSubTab);
                    renderRanking();
                }
            };
        }

        const seasonTabs = document.querySelectorAll('.season-tab');
        seasonTabs.forEach(tab => {
            tab.onclick = () => {
                seasonTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                activeSeason = tab.dataset.season;
                renderRanking();
            };
        });

        let html = '';
        const getDiffHtml = (diff) => {
            if (!diff || diff === 0) return '<span class="stay">-</span>';
            return diff > 0 
                ? `<span class="up">▲${diff}</span>` 
                : `<span class="down">▼${Math.abs(diff)}</span>`;
        };

        if (activeSubTab === 'strategy') {
            document.getElementById('strategy-filter-tabs').style.display = 'flex';
            const sortedRank = (currentData.seasonal_ranking || []).sort((a,b) => (a.rank || 999) - (b.rank || 999));
            const filtered = sortedRank.filter(r => {
                if (activeSeason === '전체') return true;
                if (activeSeason === '봄/가을') return r.season === '봄' || r.season === '가을' || r.season === '봄/가을';
                if (activeSeason === '사계절') return r.season === '사계절';
                return r.season === activeSeason;
            });

            if (filtered.length === 0) {
                html += '<div class="no-data">해당 계절의 상품 데이터가 없습니다.</div>';
            } else {
                filtered.forEach(r => {
                    html += `
                    <div class="ranking-card slide-up">
                        <div class="rank-badge">${r.rank === 999 ? '권외' : r.rank}</div>
                        <div class="ranking-details">
                            <div class="product-header">
                                <span class="season-badge ${r.season.replace('/', '')}">${r.season}</span>
                                <span class="product-code">#${r.code}</span>
                            </div>
                            <div class="product-name">${r.name}</div>
                            <div class="rank-fluctuations">
                                <div class="fluct-info">
                                    <span class="fluct-label">어제</span>
                                    <span class="fluct-val">${getDiffHtml(r.diff)}</span>
                                </div>
                                <div class="fluct-info">
                                    <span class="fluct-label">지난주</span>
                                    <span class="fluct-val">${getDiffHtml(r.week_diff || 0)}</span>
                                </div>
                            </div>
                        </div>
                    </div>`;
                });
            }
        } else {
            document.getElementById('strategy-filter-tabs').style.display = 'none';
            const nieceData = (currentData.niece_ranking || []).sort((a,b) => (a.rank || 999) - (b.rank || 999));
            if (nieceData.length === 0) {
                html += '<div class="no-data">조카선물 랭킹 데이터가 없습니다.</div>';
            } else {
                nieceData.forEach(r => {
                    html += `
                    <div class="ranking-card slide-up">
                        <div class="rank-badge">${r.rank}</div>
                        <div class="ranking-details">
                            <div class="product-header">
                                <span class="product-code">#${r.code}</span>
                            </div>
                            <div class="product-name">${r.name}</div>
                            <div class="rank-fluctuations">
                                <div class="fluct-info">
                                    <span class="fluct-label">어제</span>
                                    <span class="fluct-val">${getDiffHtml(r.diff)}</span>
                                </div>
                            </div>
                        </div>
                    </div>`;
                });
            }
        }
        rankingList.innerHTML = html;
    }

    // 툴팁
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip hidden';
    document.body.appendChild(tooltip);

    function showTooltip(event, data) {
        tooltip.innerHTML = `
            <strong>${data.name}</strong><br>
            📅 기간: ${data.schedule}<br>
            📜 내용: ${data.scheme || '정보 없음'}<br>
            ⏰ 마감: ${data.deadline || '없음'}
        `;
        tooltip.classList.remove('hidden');
        moveTooltip(event);
    }

    function moveTooltip(event) {
        tooltip.style.left = (event.pageX + 10) + 'px';
        tooltip.style.top = (event.pageY + 10) + 'px';
    }

    function hideTooltip() {
        tooltip.classList.add('hidden');
    }

    window.addEventListener('scroll', hideTooltip);

    loadData();
});