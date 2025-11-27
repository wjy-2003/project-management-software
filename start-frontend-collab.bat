@echo off
echo ========================================
echo    启动协作编辑器前端
echo ========================================
echo.

cd /d E:\Github\project-management-software\CollabFrontend

echo 安装依赖...
npm install

echo 启动React开发服务器...
echo 前端将运行在: http://localhost:3000
echo 后端连接地址: http://localhost:8001
echo.
echo 浏览器将自动打开...
echo 按Ctrl+C停止服务器
echo.

npm start

pause
