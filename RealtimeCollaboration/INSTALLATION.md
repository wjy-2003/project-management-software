# 实时协作功能 - 安装指南

## 前置要求

- Python 3.8+
- Django 4.2+
- 虚拟环境（推荐）

## 安装步骤

### 1. 激活虚拟环境

```powershell
# Windows PowerShell
cd e:\hkCources\5351\project-management-software
.\pmsvenv\Scripts\Activate.ps1

# 或 Windows CMD
cd e:\hkCources\5351\project-management-software
pmsvenv\Scripts\activate.bat

# Linux/Mac
cd /path/to/project-management-software
source pmsvenv/bin/activate
```

### 2. 安装依赖

```bash
# 安装必需的包
pip install daphne>=4.0.0

# 或者重新安装所有依赖
pip install -r requirements.txt
```

### 3. 检查安装

```bash
# 验证 channels 和 daphne 已安装
pip list | grep -E "channels|daphne"

# Windows PowerShell
pip list | findstr "channels daphne"

# 应该看到类似输出：
# channels          4.3.1
# daphne            4.1.2
```

## 配置验证

### 1. 检查 Django 设置

确认 `webapp/settings.py` 中已添加：

```python
INSTALLED_APPS = [
    "daphne",  # 必须在第一位
    # ... 其他应用
    "channels",
    "RealtimeCollaboration",
]

ASGI_APPLICATION = "webapp.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    },
}
```

### 2. 检查 ASGI 配置

确认 `webapp/asgi.py` 包含 WebSocket 路由配置。

### 3. 检查 URL 配置

确认 `webapp/urls.py` 包含：

```python
urlpatterns = [
    # ...
    path("api/collaboration/", include('RealtimeCollaboration.urls')),
]
```

## 运行服务

### 开发环境

使用 Daphne ASGI 服务器（支持 WebSocket）：

```bash
# 方式 1: 使用 daphne
daphne -b 127.0.0.1 -p 8000 webapp.asgi:application

# 方式 2: 使用 Django runserver（Django 3.0+ 自动支持 ASGI）
python manage.py runserver
```

### 验证服务运行

```bash
# 在另一个终端中测试 HTTP API
curl http://localhost:8000/api/collaboration/stats/

# 应该返回：
# {"success": true, "active_sessions": 0}
```

## 测试安装

### 1. 运行单元测试

```bash
python manage.py test RealtimeCollaboration
```

### 2. 使用测试客户端

```bash
# 安装测试依赖
pip install requests websocket-client

# 运行测试客户端
cd RealtimeCollaboration
python test_client.py
```

## 故障排查

### 问题 1: ModuleNotFoundError: No module named 'channels'

**解决方案**:
```bash
pip install channels>=4.0.0 daphne>=4.0.0
```

### 问题 2: ASGI application not found

**原因**: `ASGI_APPLICATION` 设置错误或 ASGI 模块配置有误

**解决方案**:
- 检查 `webapp/settings.py` 中 `ASGI_APPLICATION = "webapp.asgi.application"`
- 检查 `webapp/asgi.py` 文件是否正确配置

### 问题 3: WebSocket 连接失败

**可能原因**:
1. 未使用 ASGI 服务器（如直接运行 wsgi.py）
2. 防火墙阻止 WebSocket 连接
3. 会话不存在

**解决方案**:
```bash
# 确保使用 daphne 或支持 ASGI 的服务器
daphne webapp.asgi:application

# 检查会话是否存在
curl http://localhost:8000/api/collaboration/sessions/{session_id}/
```

### 问题 4: Channel layer error

**原因**: Channel Layer 配置错误

**解决方案**:
```python
# 开发环境使用内存通道层（webapp/settings.py）
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    },
}
```

### 问题 5: 虚拟环境未激活

**症状**: 提示找不到模块

**解决方案**:
```bash
# 确认虚拟环境已激活
# 命令提示符前应该有 (pmsvenv) 标识
# 如果没有，重新激活：
.\pmsvenv\Scripts\Activate.ps1
```

## 生产环境配置（可选）

### 使用 Redis 作为 Channel Layer

```bash
# 1. 安装 Redis
# Windows: https://github.com/microsoftarchive/redis/releases
# Linux: sudo apt-get install redis-server

# 2. 安装 channels-redis
pip install channels-redis

# 3. 更新 settings.py
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

### 使用 Supervisor 管理进程

创建 `/etc/supervisor/conf.d/collaboration.conf`:

```ini
[program:collaboration_server]
command=/path/to/pmsvenv/bin/daphne -b 0.0.0.0 -p 8000 webapp.asgi:application
directory=/path/to/project-management-software
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/collaboration.log
stderr_logfile=/var/log/collaboration_error.log
```

重启 Supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start collaboration_server
```

## 下一步

- 阅读 [README.md](README.md) 了解功能使用
- 阅读 [API_DOCUMENTATION.md](API_DOCUMENTATION.md) 了解 API 详情
- 运行 `test_client.py` 测试基本功能

## 获取帮助

如果遇到问题：
1. 检查 Django 日志输出
2. 查看本文档的故障排查部分
3. 运行单元测试验证功能
4. 检查 WebSocket 连接状态
