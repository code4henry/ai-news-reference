@echo off
:: ============================================================
:: AI 技术资讯收集系统 - Windows 任务计划注册脚本
:: ============================================================
:: 用法: 在 ai-news-collector 目录下双击或管理员 cmd 运行 setup_tasks.bat
:: 卸载: schtasks /delete /tn "AI_News_Collector" /f  (对每个任务重复)
:: ============================================================

setlocal enableextensions

set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

echo ============================================================
echo  AI 技术资讯收集系统 - 定时任务注册
echo  项目目录: %PROJECT_DIR%
echo ============================================================
echo.

:: Python 检查
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 python，请先安装 Python 3.7+ 并加入 PATH
    pause
    exit /b 1
)

:: 安装依赖
echo [1/5] 安装 Python 依赖 ...
python -m pip install -r "%PROJECT_DIR%\requirements.txt"
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo.

:: 卸载旧任务（如存在）
echo [2/5] 清理旧任务（如存在）...
for %%T in (AI_News_Collector AI_Ranking_Collector AI_Data_Cleanup AI_Data_Backup) do (
    schtasks /query /tn "%%T" >nul 2>&1
    if not errorlevel 1 schtasks /delete /tn "%%T" /f >nul 2>&1
)
echo.

:: 注册任务
echo [3/5] 注册: AI_News_Collector (每天 08:00) ...
schtasks /create /tn "AI_News_Collector" /tr "python -m ai_news_collector.main news" /sc daily /st 08:00 /f /ru "%USERNAME%" /rl highest /wd "%PROJECT_DIR%"

echo [4/5] 注册: AI_Ranking_Collector (每天 12:00) ...
schtasks /create /tn "AI_Ranking_Collector" /tr "python -m ai_news_collector.main rankings" /sc daily /st 12:00 /f /ru "%USERNAME%" /rl highest /wd "%PROJECT_DIR%"

echo [5/5] 注册: AI_Data_Cleanup (每天 02:00) ...
schtasks /create /tn "AI_Data_Cleanup" /tr "python -m ai_news_collector.main cleanup" /sc daily /st 02:00 /f /ru "%USERNAME%" /rl highest /wd "%PROJECT_DIR%"

echo 注册: AI_Data_Backup (每周日 03:00) ...
schtasks /create /tn "AI_Data_Backup" /tr "python -m ai_news_collector.main backup" /sc weekly /d SUN /st 03:00 /f /ru "%USERNAME%" /rl highest /wd "%PROJECT_DIR%"
echo.

echo ============================================================
echo  注册完成！任务列表:
echo  ----------------------------------------------------------
echo   1. AI_News_Collector       每天 08:00   收集新闻
echo   2. AI_Ranking_Collector    每天 12:00   收集排行榜
echo   3. AI_Data_Cleanup         每天 02:00   清理旧数据
echo   4. AI_Data_Backup          每周日 03:00 备份数据
echo  ----------------------------------------------------------
echo  注意: 修改配置后请重新运行本脚本以更新任务
echo        QQ 通知需在 news_sources.yaml 配 group_id 或 user_id
echo ============================================================
pause
endlocal
