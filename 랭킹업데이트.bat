@echo off
setlocal
:: 1. 폴더 이동
cd /d "%~dp0"

:: 2. 설정 정보 (파니님 정보로 세팅됨)
set GITHUB_USER=tiffany0714
set REPO_NAME=kakao_project
set TOKEN=YOUR_TOKEN_HERE
set WORKFLOW_ID=daily_update.yml

echo ==========================================
echo [1/4] 깃허브에 실시간 크롤링 명령 전송 중...
echo ==========================================
curl -X POST -H "Authorization: token %TOKEN%" ^
     -H "Accept: application/vnd.github.v3+json" ^
     https://api.github.com/repos/%GITHUB_USER%/%REPO_NAME%/actions/workflows/%WORKFLOW_ID%/dispatches ^
     -d "{\"ref\":\"main\"}"

echo.
echo ==========================================
echo [2/4] 깃허브가 열일 중입니다 (약 2분 소요)...
echo 이 창을 끄지 말고 잠시만 기다려주세요.
echo ==========================================
:: 크롤링 및 파일 저장 시간을 벌기 위해 120초 대기
timeout /t 180

echo.
echo ==========================================
echo [3/4] 업데이트된 최신 데이터 가져오는 중...
echo ==========================================
git fetch --all
git reset --hard origin/main

echo.
echo ==========================================
echo [4/4] 로컬 서버 실행 및 브라우저 열기
echo ==========================================
:: 기존에 켜져 있을지 모를 5000포트 서버 강제 종료
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000') do taskkill /f /pid %%a 2>nul

start http://localhost:5000
python run_local_server.py

pause