document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const rankingList = document.getElementById('ranking-list');
    const updateStatus = document.getElementById('update-status');
    const seasonFilterContainer = document.getElementById('strategy-filter-container');
    const seasonFilter = document.getElementById('seasonFilter');

    let currentData = null;
    const savedTab = localStorage.getItem('activeTab') || 'tab1';
    let currentSubTab = localStorage.getItem('activeSubTab') || 'strategy';

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

    // 서브 탭 (랭킹 vs 조카선물) 클릭
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('sub-tab-btn')) {
            document.querySelectorAll('.sub-tab-btn').forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');
            currentSubTab = e.target.dataset.sub;
            localStorage.setItem('activeSubTab', currentSubTab);
            
            // 랭킹(strategy)일 때만 계절 필터 노출
            if (currentSubTab === 'strategy') seasonFilterContainer?.classList.remove('hidden');
            else seasonFilterContainer?.classList.add('hidden');
            
            renderRanking();
        }
    });

    if(seasonFilter) seasonFilter.addEventListener('change', renderRanking);

    async function fetchData() {
        try {
            const response = await fetch(`./data/current_data.json?v=${new Date().getTime()}`);
            currentData = await response.json();
            if(updateStatus) updateStatus.innerText = `마지막 업데이트: ${currentData.last_updated}`;
            renderRanking();
        } catch (e) {
            console.error("데이터 로드 실패", e);
        }
    }

    function renderRanking() {
        if (!currentData || !rankingList) return;
        let html = '';

        if (currentSubTab === 'strategy') {
            // [랭킹] 탭: 엑셀 기반 전략 상품
            const filter = seasonFilter.value;
            const items = currentData.seasonal_ranking || [];
            html = `<table class="rank-table"><thead><tr><th>계절</th><th>이미지</th><th>상품명</th><th>순위(등락)</th></tr></thead><tbody>`;
            
            items.filter(i => filter === '전체' || i.season === filter).forEach(r => {
                const diffNum = parseInt(r.diff || 0);
                const diffHTML = diffNum > 0 ? `<span style="color:red">▲${diffNum}</span>` : (diffNum < 0 ? `<span style="color:blue">▼${Math.abs(diffNum)}</span>` : '-');
                const rankText = r.rank === 999 ? '권외' : `${r.rank}위`;
                
                html += `<tr><td>${r.season}</td><td><img src="${r.img}" width="40"></td><td>${r.name}<br><small>#${r.code}</small></td><td><b>${rankText}</b><br>(${diffHTML})</td></tr>`;
            });
            html += `</tbody></table>`;
        } else {
            // [조카선물] 탭: 오즈키즈 탐색 결과
            const items = currentData.niece_ranking || [];
            html = `<table class="rank-table"><thead><tr><th>상품명</th><th>현재 위치</th></tr></thead><tbody>`;
            items.forEach(r => {
                html += `<tr><td>${r.name}<br><small>#${r.code}</small></td><td><b>${r.rank}번째</b></td></tr>`;
            });
            html += `</tbody></table>`;
        }
        rankingList.innerHTML = html;
    }

    fetchData();
});