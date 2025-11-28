# 协作编辑器前后端集成指南

## 🎯 问题分析

### 当前问题：
1. **IP地址硬编码**：前端代码中硬编码了 `192.168.191.224:8001`
2. **环境配置**：需要使用uv虚拟环境运行Django后端
3. **端口配置**：后端8001端口，前端需要独立启动
4. **跨域配置**：Django已配置CORS，但需要确保正确

## 🛠️ 运行测试步骤

### 1. 启动后端 (Django)

```bash
# 进入项目根目录
cd E:\Github\project-management-software

# 激活uv虚拟环境
.venv\Scripts\activate  # Windows
# 或
source .venv/bin/activate  # Linux/Mac

# 启动Django ASGI服务器（支持WebSocket）
python manage.py runserver 0.0.0.0:8001

# 或者使用Daphne启动ASGI服务器
daphne -b 0.0.0.0 -p 8001 webapp.asgi:application
```

### 2. 启动前端 (React)

```bash
# 进入前端目录
cd collab-editor

# 安装依赖（如果尚未安装）
npm install

# 修改配置文件 - 将IP改为localhost
# 编辑 src/App.js 第14行：
# const BACKEND_IP = 'localhost';  // 改为localhost

# 启动前端开发服务器
npm start
```

### 3. 测试连接

1. **后端测试**：
   - 访问：`http://localhost:8001/api/collaboration/sessions/create/`
   - 应该看到JSON响应或Django调试页面

2. **前端测试**：
   - 访问：`http://localhost:3000`
   - 点击"创建房间"按钮
   - 查看浏览器控制台是否有连接错误

### 4. 调试步骤

如果无法连接：

1. **检查后端是否启动**：
   ```bash
   curl http://localhost:8001/api/collaboration/
   ```

2. **检查WebSocket连接**：
   - 浏览器F12 → Network → WS标签
   - 查看WebSocket连接状态

3. **检查Django日志**：
   - 查看终端输出，确认没有错误

4. **检查防火墙**：
   - Windows防火墙可能阻止端口访问

## 🔧 配置优化建议

### 1. 环境变量配置
创建 `.env` 文件：
```
REACT_APP_BACKEND_IP=localhost
REACT_APP_BACKEND_PORT=8001
```

### 2. Django设置优化
在 `webapp/settings.py` 中：
```python
# 允许的域名
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# CORS配置
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# WebSocket允许的源
WS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

## 📝 常见错误解决

### 1. "WebSocket connection failed"
- 确保使用Daphne而不是manage.py runserver
- 检查防火墙设置

### 2. "CORS policy error"
- 确认CORS配置正确
- 检查前端请求的域名是否在允许列表中

### 3. "404 Not Found"
- 确认URL路由配置正确
- 检查`webapp/urls.py`和`RealtimeCollaboration/urls.py`

### 4. "ModuleNotFoundError"
- 确保激活了虚拟环境
- 运行 `pip install -r requirements.txt`

## 🚀 快速启动脚本

创建 `start-backend.bat` (Windows)：
```batch
@echo off
cd /d E:\Github\project-management-software
call .venv\Scripts\activate
python manage.py runserver 0.0.0.0:8001
pause
```

创建 `start-frontend.bat` (Windows)：
```batch
@echo off
cd /d E:\Github\project-management-software\collab-editor
npm start
pause
```
