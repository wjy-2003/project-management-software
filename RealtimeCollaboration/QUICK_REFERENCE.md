# 实时协作功能 - 快速参考

## 一分钟快速开始

```bash
# 1. 安装依赖
pip install daphne>=4.0.0

# 2. 运行服务器
daphne webapp.asgi:application

# 3. 测试（新终端）
curl http://localhost:8000/api/collaboration/stats/
```

## 常用命令

### 服务器

```bash
# 开发服务器（支持 WebSocket）
daphne -b 127.0.0.1 -p 8000 webapp.asgi:application

# Django runserver（Django 3.0+）
python manage.py runserver

# 运行测试
python manage.py test RealtimeCollaboration
```

### 测试客户端

```bash
# 安装测试依赖
pip install requests websocket-client

# 运行测试客户端
python RealtimeCollaboration/test_client.py
```

## 核心 API

### HTTP API

```python
import requests

# 创建会话
resp = requests.post('http://localhost:8000/api/collaboration/sessions/create/',
                     json={'initiator': 'alice'})
session_id = resp.json()['session_id']

# 加入会话
requests.post(f'http://localhost:8000/api/collaboration/sessions/{session_id}/join/',
              json={'member_id': 'bob', 'role': 'editor'})

# 获取会话信息
resp = requests.get(f'http://localhost:8000/api/collaboration/sessions/{session_id}/')
print(resp.json())
```

### WebSocket

```python
import websocket
import json

# 连接
ws = websocket.create_connection(
    f'ws://localhost:8000/ws/collaboration/{session_id}/alice/'
)

# 接收消息
msg = json.loads(ws.recv())

# 创建文件夹
ws.send(json.dumps({
    'type': 'structure_change',
    'operation': 'create_folder',
    'payload': {'id': 'f1', 'name': 'src', 'parent_id': None}
}))

# 创建文件
ws.send(json.dumps({
    'type': 'structure_change',
    'operation': 'create_file',
    'payload': {'id': 'file1', 'name': 'main.py', 'parent_id': 'f1', 'type': 'python'}
}))

# 监听
while True:
    print(json.loads(ws.recv()))
```

## 文件夹结构操作

### 所有操作类型

| 操作 | operation | payload 字段 |
|------|-----------|-------------|
| 创建文件夹 | `create_folder` | `id`, `name`, `parent_id` |
| 创建文件 | `create_file` | `id`, `name`, `parent_id`, `type` |
| 删除文件夹 | `delete_folder` | `id` |
| 删除文件 | `delete_file` | `id` |
| 移动文件夹 | `move_folder` | `id`, `new_parent_id` |
| 移动文件 | `move_file` | `id`, `new_parent_id` |
| 重命名文件夹 | `rename_folder` | `id`, `new_name` |
| 重命名文件 | `rename_file` | `id`, `new_name` |

### 操作示例

```json
// 创建文件夹
{
  "type": "structure_change",
  "operation": "create_folder",
  "payload": {"id": "f1", "name": "src", "parent_id": null}
}

// 移动文件
{
  "type": "structure_change",
  "operation": "move_file",
  "payload": {"id": "file1", "new_parent_id": "f2"}
}

// 重命名文件夹
{
  "type": "structure_change",
  "operation": "rename_folder",
  "payload": {"id": "f1", "new_name": "source"}
}
```

## 角色权限

| 角色 | 查看 | 修改结构 | 修改权限 |
|------|------|---------|---------|
| **initiator** | ✓ | ✓（直接） | ✓ |
| **editor** | ✓ | ✓（需验证） | ✗ |
| **viewer** | ✓ | ✗ | ✗ |

## 消息类型速查

### 客户端 → 服务器

| 类型 | 说明 |
|------|------|
| `structure_change` | 结构变更请求 |
| `content_collaboration` | 内容协作消息（如 Yjs） |
| `permission_change` | 权限变更请求（仅发起者） |

### 服务器 → 客户端

| 类型 | 说明 |
|------|------|
| `session_info` | 会话信息（连接时） |
| `structure_changed` | 结构变更广播 |
| `content_update` | 内容更新广播 |
| `member_joined` | 成员加入通知 |
| `member_left` | 成员离开通知 |
| `permission_updated` | 权限更新通知 |
| `error` | 错误消息 |

## JavaScript 示例

```javascript
// 创建会话
const response = await fetch('http://localhost:8000/api/collaboration/sessions/create/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ initiator: 'alice' })
});
const { session_id } = await response.json();

// 连接 WebSocket
const ws = new WebSocket(`ws://localhost:8000/ws/collaboration/${session_id}/alice/`);

// 接收消息
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'session_info':
      console.log('会话信息:', message.session);
      break;
    case 'structure_changed':
      console.log('结构变更:', message.operation, message.payload);
      break;
    case 'member_joined':
      console.log('成员加入:', message.member_id);
      break;
    case 'error':
      console.error('错误:', message.message);
      break;
  }
};

// 创建文件
ws.send(JSON.stringify({
  type: 'structure_change',
  operation: 'create_file',
  payload: {
    id: 'file1',
    name: 'README.md',
    parent_id: null,
    type: 'markdown'
  }
}));
```

## 常见问题

### Q: WebSocket 连接失败？
**A**: 确保使用 `daphne` 而不是普通的 Django runserver。

### Q: 会话不存在？
**A**: 先调用 HTTP API 创建或加入会话，然后再连接 WebSocket。

### Q: 权限被拒绝？
**A**: 检查成员角色。viewer 不能修改结构，非 initiator 不能修改权限。

### Q: 服务器重启后会话丢失？
**A**: 正常现象，所有数据存储在内存中。生产环境可添加持久化。

### Q: 需要数据库吗？
**A**: 不需要！本实现完全不依赖数据库。

## 调试技巧

### 启用 Django 调试

```python
# settings.py
DEBUG = True
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
```

### 查看活跃会话

```python
from RealtimeCollaboration.session_manager import session_manager

# 会话数量
print(session_manager.get_session_count())

# 所有会话
print(session_manager.active_sessions)
```

### 测试单个功能

```python
# 测试会话管理
python manage.py test RealtimeCollaboration.SessionManagerTestCase

# 测试 API
python manage.py test RealtimeCollaboration.CollaborationAPITestCase
```

## 性能建议

1. **批量操作**: 批量发送结构变更而非逐个发送
2. **防抖**: 对频繁操作（如内容协作）使用防抖
3. **限制大小**: 控制文件夹结构的大小（建议 < 1000 项）
4. **使用 Redis**: 生产环境使用 Redis Channel Layer
5. **监控内存**: 定期监控服务器内存使用

## 文档链接

- **详细使用**: [README.md](README.md)
- **完整 API**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **安装指南**: [INSTALLATION.md](INSTALLATION.md)
- **实现总结**: [SUMMARY.md](SUMMARY.md)

## 联系与支持

遇到问题？
1. 查看错误日志
2. 运行单元测试
3. 检查本文档和其他文档
4. 查看 Django Channels 官方文档
