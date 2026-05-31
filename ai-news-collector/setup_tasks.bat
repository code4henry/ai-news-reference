@echo off
echo 设置AI技术资讯收集和推送系统定时任务...

:: 检查Python是否已安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

:: 安装依赖
echo 安装Python依赖包...
pip install -r requirements.txt

:: 创建定时任务
echo 创建Windows计划任务...

:: 设置新闻收集任务 (每天早上8点)
schtasks /create /tn "AI_News_Collector" /tr "python C:\Users\wyzhw\.openclaw\workspace-march\ai-news-collector\main.py news" /sc daily /st 08:00 /f

:: 设置排行榜收集任务 (每天中午12点)
schtasks /create /tn "AI_Ranking_Collector" /tr "python C:\Users\wyzhw\.openclaw\workspace-march\ai-news-collector\main.py rankings" /sc daily /st 12:00 /f

:: 设置数据清理任务 (每天凌晨2点)
schtasks /create /tn "AI_Data_Cleanup" /tr "python C:\Users\wyzhw\.openclaw\workspace-march\ai-news-collector\main.py cleanup" /sc daily /st 02:00 /f

:: 设置数据备份任务 (每周日凌晨3点)
schtasks /create /tn "AI_Data_Backup" /tr "python C:\Users\wyzhw\.openclaw\workspace-march\ai-news-collector\main.py backup" /sc weekly /d SUN /st 03:00 /f

echo 定时任务设置完成!
echo.
echo 任务列表:
echo 1. AI_News_Collector - 每天早上8点收集新闻
echo 2. AI_Ranking_Collector - 每天中午12点收集排行榜数据
echo 3. AI_Data_Cleanup - 每天凌晨2点清理旧数据
echo 4. AI_Data_Backup - 每周日凌晨3点备份数据
echo.
echo 注意: 请确保Python和脚本路径正确
echo 如需修改任务，请使用任务计划程序或手动删除后重新运行此脚本
pause