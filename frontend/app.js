document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const calendarDays = document.getElementById('calendar-days');
    const currentMonthLabel = document.getElementById('current-month');
    const eventDetailsContainer = document.getElementById('event-details');
    const rankingList = document.getElementById('ranking-list');
    const updateStatus = document.getElementById('update-status');
    const changeLog = document.getElementById('change-log');
    const changeList = document.getElementById('change-list');
    const tooltip = document.getElementById('tooltip');

    let currentData = null;
    let currentDate = new Date(2026, 2, 1); // Default to March 2026
    let currentSubTab = 'realtime';

    // Tab Switching
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.tab).classList.add('active');
        });
    });

    // Sub-tab Switching for Ranking
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('sub-tab-btn')) {
            document.querySelectorAll('.sub-tab-btn').forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');
            currentSubTab = e.target.dataset.sub;
            renderRanking();
        }
    });

    // Fetch Data
    async function fetchData() {
        try {
            // Cache busting with timestamp
            const response = await fetch(`data/current_data.json?v=${new Date().getTime()}`);
            currentData = await response.json();
            renderDashboard();
        } catch (error) {
            console.error("Error fetching data:", error);
            updateStatus.innerText = "데이터를 불러오는 중 오류가 발생했습니다.";
        }
    }

    function renderDashboard() {
        if (!currentData) return;

        // Update status
        const lastUpdated = new Date(currentData.last_updated).toLocaleString();
        updateStatus.innerText = `마지막 업데이트: ${lastUpdated}`;

        // Render Change Log
        if (currentData.changes && currentData.changes.length > 0) {
            changeLog.classList.remove('hidden');
            changeList.innerHTML = currentData.changes.map(c => `<li>${c}</li>`).join('');
        }

        renderCalendar();
        renderDetails();
        renderRanking();
    }

    function renderCalendar() {
        calendarDays.innerHTML = '';
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();

        currentMonthLabel.innerText = `${year}년 ${month + 1}월`;

        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const prevMonthLastDay = new Date(year, month, 0).getDate();

        // Previous month days
        for (let i = firstDay; i > 0; i--) {
            const dayDiv = document.createElement('div');
            dayDiv.className = 'day other-month';
            dayDiv.innerHTML = `<div class="day-num">${prevMonthLastDay - i + 1}</div>`;
            calendarDays.appendChild(dayDiv);
        }

        // Parse events for overlapping
        const parseDate = (str, y) => {
            if (!str) return null;
            const match = str.match(/(\d+)월\s*(\d+)일/);
            if (match) return new Date(y, parseInt(match[1]) - 1, parseInt(match[2]));
            return null;
        };

        const monthEvents = [];
        if (currentData.events) {
            currentData.events.forEach((event, idx) => {
                if (!event.schedule) return;
                const parts = event.schedule.split(/~|-/);
                if (parts.length === 2) {
                    const start = parseDate(parts[0], year);
                    const end = parseDate(parts[1], year);
                    if (start && end) {
                        const monthStart = new Date(year, month, 1);
                        const monthEnd = new Date(year, month + 1, 0);
                        if (start <= monthEnd && end >= monthStart) {
                            monthEvents.push({ ...event, start, end, id: idx });
                        }
                    }
                }
            });
            // Sort by start date, then duration (descending)
            monthEvents.sort((a, b) => {
                if (a.start.getTime() !== b.start.getTime()) return a.start - b.start;
                return (b.end - b.start) - (a.end - a.start);
            });
        }

        // slot map: day -> slot_index -> event
        const slots = Array.from({ length: daysInMonth + 1 }, () => []);
        monthEvents.forEach(event => {
            const sDay = event.start.getMonth() === month && event.start.getFullYear() === year ? event.start.getDate() : 1;
            const eDay = event.end.getMonth() === month && event.end.getFullYear() === year ? event.end.getDate() : daysInMonth;

            event.renderStartDay = sDay;
            event.renderEndDay = eDay;

            // Find first available slot
            let slotIdx = 0;
            while (true) {
                let available = true;
                for (let d = sDay; d <= eDay; d++) {
                    if (slots[d][slotIdx]) {
                        available = false; break;
                    }
                }
                if (available) break;
                slotIdx++;
            }
            event.slot = slotIdx;
            for (let d = sDay; d <= eDay; d++) {
                slots[d][slotIdx] = event;
            }
        });

        const maxSlot = Math.max(-1, ...slots.map(daySlots => daySlots.length - 1));

        // Current month days
        const todayObj = new Date();
        const tYear = todayObj.getFullYear();
        const tMonth = todayObj.getMonth();
        const tDate = todayObj.getDate();

        for (let i = 1; i <= daysInMonth; i++) {
            const dayDiv = document.createElement('div');
            dayDiv.className = 'day';
            if (year === tYear && month === tMonth && i === tDate) {
                dayDiv.classList.add('today');
            }
            dayDiv.innerHTML = `<div class="day-num">${i}</div>`;

            // Inject events for this day
            const dayEventsContainer = document.createElement('div');
            dayEventsContainer.className = 'day-events';

            for (let s = 0; s <= maxSlot; s++) {
                const event = slots[i][s];
                if (event) {
                    const bar = document.createElement('div');
                    bar.className = `event-bar color-${event.id % 5}`;

                    // is it start of rendering for this event?
                    if (i === event.renderStartDay) {
                        bar.classList.add('start-bar');
                        bar.innerText = event.name;
                    } else {
                        bar.innerText = '\u00A0'; // non-breaking space (visually no text)
                    }
                    if (i === event.renderEndDay) bar.classList.add('end-bar');
                    if (i > event.renderStartDay && i < event.renderEndDay) bar.classList.add('mid-bar');

                    bar.title = event.scheme;
                    bar.onmouseenter = (e) => showTooltip(e, event.scheme);
                    bar.onmouseleave = hideTooltip;
                    dayEventsContainer.appendChild(bar);
                } else {
                    const emptyBar = document.createElement('div');
                    emptyBar.className = 'event-bar empty';
                    emptyBar.innerText = '\u00A0';
                    dayEventsContainer.appendChild(emptyBar);
                }
            }

            // Check for deadlines
            if (currentData.events) {
                currentData.events.forEach(event => {
                    if (event.deadline) {
                        const dMatch = event.deadline.match(/(\d+)월\s*(\d+)일/);
                        if (dMatch) {
                            const dM = parseInt(dMatch[1]) - 1;
                            const dD = parseInt(dMatch[2]);
                            if (dM === month && dD === i) {
                                const bar = document.createElement('div');
                                bar.className = 'event-bar deadline';
                                bar.innerText = `[마감] ${event.name}`;
                                bar.onmouseenter = (e) => showTooltip(e, `마감일: ${event.deadline}`);
                                bar.onmouseleave = hideTooltip;
                                dayEventsContainer.appendChild(bar);
                            }
                        }
                    }
                });
            }

            dayDiv.appendChild(dayEventsContainer);
            calendarDays.appendChild(dayDiv);
        }
    }

    function renderDetails() {
        const today = new Date();
        const parseStartDate = (schedule) => {
            if (!schedule) return new Date(9999, 0, 1);
            const parts = schedule.split(/~|-/);
            const match = parts[0].match(/(\d+)월\s*(\d+)일/);
            if (match) return new Date(currentDate.getFullYear(), parseInt(match[1]) - 1, parseInt(match[2]));
            return new Date(9999, 0, 1);
        };
        const sortedEvents = [...currentData.events].sort((a, b) => parseStartDate(a.schedule) - parseStartDate(b.schedule));
        eventDetailsContainer.innerHTML = sortedEvents.map(event => {
            let isEnded = false;
            if (event.schedule) {
                const parts = event.schedule.split(/~|-/);
                if (parts.length === 2) {
                    const match = parts[1].match(/(\d+)월\s*(\d+)일/);
                    if (match) {
                        const endY = currentDate.getFullYear(); // using currently displayed year, or assume current year
                        const endM = parseInt(match[1]) - 1;
                        const endD = parseInt(match[2]);
                        const endDate = new Date(endY, endM, endD, 23, 59, 59);
                        if (today > endDate) {
                            isEnded = true;
                        }
                    }
                }
            }
            const displayName = isEnded ? `${event.name} <span style="color:red; font-size:14px;">(종료)</span>` : event.name;

            return `
            <div class="event-card">
                <h3>${displayName}</h3>
                <p><span class="label">일정:</span> ${event.schedule}</p>
                <p><span class="label">마감일:</span> ${event.deadline}</p>
                <div class="scheme">
                    <strong>행사 스킴:</strong>
                    <div class="scheme-lines">${event.scheme.split('\n').map(line => `<div class="scheme-line">${line}</div>`).join('')}</div>
                </div>
            </div>
            `;
        }).join('');
    }

    function renderRanking() {
        if (!currentData || !currentData.ranking) {
            rankingList.innerHTML = '<div class="no-data">현재 랭킹 데이터가 없습니다.</div>';
            return;
        }

        let rankings = currentData.ranking;
        if (!Array.isArray(rankings)) rankings = [rankings]; // Handle single item fallback

        // Filter by category
        if (currentSubTab === 'niece') {
            // Use separate niece_ranking if available, else fallback to category filter
            if (currentData.niece_ranking && currentData.niece_ranking.length > 0) {
                rankings = currentData.niece_ranking;
            } else {
                rankings = rankings.filter(r => r.category === 'niece');
            }
        } else {
            // realtime: only show category=realtime items
            rankings = rankings.filter(r => !r.category || r.category === 'realtime');
        }

        if (rankings.length === 0) {
            rankingList.innerHTML = `<div class="no-data">${currentSubTab === 'niece' ? '조카선물 랭킹 데이터가 없습니다.<br><small>current_data.json의 niece_ranking 배열에 데이터를 직접 입력해 주세요.</small>' : '랭킹 정보를 불러올 수 없습니다.'}</div>`;
            return;
        }

        rankingList.innerHTML = rankings.map(r => {
            const formatFluct = (diff, label) => {
                if (diff === undefined || diff === null) return `<div class="fluct-info"><span class="stay">-</span> <span class="fluct-label">${label}</span></div>`;
                const icon = diff > 0 ? '▲' : (diff < 0 ? '▼' : '-');
                const css = diff > 0 ? 'up' : (diff < 0 ? 'down' : 'stay');
                return `
                    <div class="fluct-info">
                        <span class="fluct-val ${css}">${icon} ${Math.abs(diff)}</span>
                        <span class="fluct-label">${label}</span>
                    </div>
                `;
            };

            return `
                <div class="ranking-item">
                    <div class="rank-badge">${r.rank}</div>
                    <img class="ranking-thumb" src="${r.img}" alt="${r.name}" onerror="this.src='https://st.kakaocdn.net/commerce_ui/static/common_module/default_fallback_thumbnail.png'">
                    <div class="ranking-details">
                        <div class="product-code">#${r.product_code || '---'}</div>
                        <div class="product-name">${r.name}</div>
                        <div class="rank-fluctuations">
                            ${formatFluct(r.diff_yesterday, '전일대비')}
                            ${formatFluct(r.diff_last_week, '전주대비')}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    function showTooltip(e, text) {
        if (!text) return;
        tooltip.innerText = text;
        tooltip.classList.remove('hidden');
        tooltip.style.left = (e.clientX + 10) + 'px';
        tooltip.style.top = (e.clientY + 10) + 'px';
    }

    function hideTooltip() {
        tooltip.classList.add('hidden');
    }

    // Navigation
    document.getElementById('prev-month').addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar();
    });
    document.getElementById('next-month').addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar();
    });

    fetchData();
});
