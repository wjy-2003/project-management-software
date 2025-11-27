@echo off
echo ========================================
echo    启动Django后端服务器
echo ========================================
echo.

cd /d E:\Github\project-management-software

echo 激活uv虚拟环境...
call .venv\Scripts\activate

echo 启动Django ASGI服务器 (支持WebSocket)...
echo 后端将运行在: http://localhost:8001
echo 前端连接地址: ws://localhost:8001/ws/collaboration
echo.
echo 按Ctrl+C停止服务器
echo.

python manage.py runserver 0.0.0.0:8001

pause
