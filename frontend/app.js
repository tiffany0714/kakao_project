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
    
    // 추가된 필터 요소
    const seasonFilterContainer = document.getElementById('strategy-filter-container');
    const seasonFilter = document.getElementById('seasonFilter');

    let currentData = null;
    let currentDate = new Date(2026, 2, 1); 
    const savedTab = localStorage.getItem('activeTab') || 'tab1';
    const savedSubTab = localStorage.getItem('activeSubTab') || 'realtime';
    let currentSubTab = savedSubTab;

    // 탭 복구
    const restoreTab = () => {
        const targetTabBtn = document.querySelector(`.tab-btn[data-tab="${savedTab}"]`);
        if (targetTabBtn) {
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            targetTabBtn.classList.add('active');
            const targetContent = document.getElementById(savedTab);
            if (targetContent) targetContent.classList.add('active');
        }
    };
    restoreTab();

    // 메인 탭 클릭 이벤트
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            const targetId = tab.dataset.tab;
            document.getElementById(targetId).classList.add('active');
            localStorage.setItem('activeTab', targetId);
        });
    });

    // 서브 탭 클릭 이벤트 (실시간 vs 전략상품)
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('sub-tab-btn')) {
            document.querySelectorAll('.sub-tab-btn').forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');
            currentSubTab = e.target.dataset.sub;
            localStorage.setItem('activeSubTab', currentSubTab);
            
            // 전략 상품 탭일 때만 필터 보여주기
            if (currentSubTab === 'strategy') {
                seasonFilterContainer.classList.remove('hidden');
            } else {
                seasonFilterContainer.classList.add('hidden');
            }
            
            renderRanking();
        }
    });

    // 계절 필터 변경 시 리렌더링
    if(seasonFilter) {
        seasonFilter.addEventListener('change', renderRanking);
    }

    const restoreSubTabUI = () => {
        const subBtn = document.querySelector(`.sub-tab-btn[data-sub="${currentSubTab}"]`);
        if (subBtn) {
            document.querySelectorAll('.sub-tab-btn').forEach(btn => btn.classList.remove('active'));
            subBtn.classList.add('active');
            if (currentSubTab === 'strategy') seasonFilterContainer.classList.remove('hidden');
        }
    };

    // 데이터 호출
    async function fetchData() {
        try {
            const url = `./data/current_data.json?v=${new Date().getTime()}`;
            const response = await fetch(url);
            if (!response.ok) throw new Error("Network response was not ok");
            currentData = await response.json();
            renderDashboard();
        } catch (error) {
            console.error("Error fetching data:", error);
            if(updateStatus) updateStatus.innerText = "데이터 로딩 실패.";
        }
    }

    function renderDashboard() {
        if (!currentData) return;
        const lastUpdated = new Date(currentData.last_updated).toLocaleString();
        if(updateStatus) updateStatus.innerText = `마지막 업데이트: ${lastUpdated}`;
        renderCalendar();
        renderDetails();
        restoreSubTabUI();
        renderRanking();
    }

    // 랭킹 렌더링 (핵심 수정 부분)
    function renderRanking() {
        if (!currentData || !rankingList) return;
        
        let html = '';

        if (currentSubTab === 'realtime') {
            // [1] 실시간 TOP 20 모드
            const rankings = currentData.total_ranking || [];
            if (rankings.length === 0) {
                rankingList.innerHTML = '<div class="no-data">실시간 데이터가 없습니다.</div>';
                return;
            }
            html = rankings.map(r => renderRankingItem(r)).join('');
        } else {
            // [2] 시즌별 전략 상품 모드
            const filterValue = seasonFilter.value;
            const rankings = currentData.seasonal_ranking || [];
            
            const filtered = rankings.filter(item => filterValue === '전체' || item.season === filterValue);
            
            if (filtered.length === 0) {
                rankingList.innerHTML = '<div class="no-data">해당 계절의 등록 상품이 없습니다.</div>';
                return;
            }
            html = filtered.map(r => renderRankingItem(r, true)).join('');
        }
        
        rankingList.innerHTML = html;
    }

    // 아이템 하나하나를 그리는 보조 함수
    function renderRankingItem(r, isStrategy = false) {
        const rankDisplay = r.rank === "순위권 밖" ? "OUT" : `${r.rank}위`;
        const diff = parseInt(r.diff || 0);
        let diffHTML = '<span class="stay">-</span>';
        
        if (diff > 0) diffHTML = `<span class="up">▲ ${diff}</span>`;
        else if (diff < 0) diffHTML = `<span class="down">▼ ${Math.abs(diff)}</span>`;

        // 전략 상품일 때는 계절 태그 추가
        const seasonTag = isStrategy ? `<span class="season-tag">${r.season}</span>` : '';

        return `
            <div class="ranking-item">
                <div class="rank-badge">${rankDisplay}</div>
                <img class="ranking-thumb" src="${r.img}" onerror="this.src='https://st.kakaocdn.net/commerce_ui/static/common_module/default_fallback_thumbnail.png'">
                <div class="ranking-details">
                    <div class="product-code">${seasonTag} #${r.code || r.product_code || '---'}</div>
                    <div class="product-name">${r.name}</div>
                    <div class="rank-fluctuations">
                        <div class="fluct-info">${diffHTML} <span class="fluct-label">전일대비</span></div>
                    </div>
                </div>
            </div>`;
    }

    // --- 기타 캘린더/디테일 함수 (기존 유지) ---
    function parseDate(str, y) {
        if (!str) return null;
        const koMatch = str.match(/(\d+)월\s*(\d+)일/);
        if (koMatch) return new Date(y, parseInt(koMatch[1]) - 1, parseInt(koMatch[2]));
        return null;
    }

    function renderCalendar() { /* 기존 코드와 동일 */ }
    function renderDetails() { /* 기존 코드와 동일 */ }
    function showTooltip(e, text) { /* 기존 코드와 동일 */ }
    function hideTooltip() { tooltip.classList.add('hidden'); }

    // 월 이동 버튼
    document.getElementById('prev-month')?.addEventListener('click', () => { currentDate.setMonth(currentDate.getMonth() - 1); renderCalendar(); });
    document.getElementById('next-month')?.addEventListener('click', () => { currentDate.setMonth(currentDate.getMonth() + 1); renderCalendar(); });

    fetchData();
});