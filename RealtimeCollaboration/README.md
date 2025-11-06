# 实时协作功能 - 使用指南

## 概述

基于 Django Channels 的无持久化实时协作后端，支持多用户实时同步文件夹结构和文件内容。所有数据仅存储在内存中，会话结束后自动清除。

## 核心特性

1. **无数据库依赖**：所有会话数据存储在内存中
2. **实时 WebSocket 通信**：支持低延迟的实时协作
3. **权限控制**：发起者、编辑者、只读三种角色
4. **文件夹结构同步**：由发起者维护权威版本
5. **自动会话清理**：最后一个成员离开时自动销毁

## 安装依赖

确保已安装以下 Python 包：

```bash
pip install django>=4.2
pip install channels>=4.0.0
pip install daphne>=4.0.0
```

或者使用项目的 requirements.txt：

```bash
pip install -r requirements.txt
```

## 启动服务

使用 Daphne ASGI 服务器启动（支持 WebSocket）：

```bash
# 开发环境
daphne -b 127.0.0.1 -p 8000 webapp.asgi:application

# 或使用 Django 的 runserver（Django 3.0+ 支持 ASGI）
python manage.py runserver
```

## API 端点

### 1. 创建会话

**POST** `/api/collaboration/sessions/create/`

```json
// 请求
{
  "initiator": "user_alice"
}

// 响应
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Session created successfully"
}
```

### 2. 加入会话

**POST** `/api/collaboration/sessions/{session_id}/join/`

```json
// 请求
{
  "member_id": "user_bob",
  "role": "editor"  // "editor" 或 "viewer"
}

// 响应
{
  "success": true,
  "message": "Joined session successfully"
}
```

### 3. 获取会话信息

**GET** `/api/collaboration/sessions/{session_id}/`

```json
// 响应
{
  "success": true,
  "session": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "initiator": "user_alice",
    "created_at": "2025-10-30T12:00:00",
    "members": [
      {
        "member_id": "user_alice",
        "role": "initiator",
        "joined_at": "2025-10-30T12:00:00"
      },
      {
        "member_id": "user_bob",
        "role": "editor",
        "joined_at": "2025-10-30T12:05:00"
      }
    ],
    "structure": {
      "folders": [],
      "files": []
    }
  }
}
```

### 4. 更新成员权限

**POST** `/api/collaboration/sessions/{session_id}/permissions/`

```json
// 请求（仅发起者可调用）
{
  "initiator_id": "user_alice",
  "member_id": "user_bob",
  "role": "viewer"
}

// 响应
{
  "success": true,
  "message": "Permission updated successfully"
}
```

### 5. 离开会话

**POST** `/api/collaboration/sessions/{session_id}/leave/`

```json
// 请求
{
  "member_id": "user_bob"
}

// 响应
{
  "success": true,
  "message": "Left session successfully",
  "session_destroyed": false
}
```

### 6. 获取成员列表

**GET** `/api/collaboration/sessions/{session_id}/members/`

### 7. 获取文件夹结构

**GET** `/api/collaboration/sessions/{session_id}/structure/`

### 8. 获取统计信息

**GET** `/api/collaboration/stats/`

```json
// 响应
{
  "success": true,
  "active_sessions": 5
}
```

## WebSocket 连接

### 连接地址

```
ws://localhost:8000/ws/collaboration/{session_id}/{member_id}/
```

### 消息类型

#### 1. 连接后接收（服务器 → 客户端）

```json
{
  "type": "session_info",
  "session": {
    "session_id": "...",
    "initiator": "user_alice",
    "members": [...],
    "structure": {...}
  },
  "timestamp": "2025-10-30T12:00:00"
}
```

#### 2. 文件夹结构变更（客户端 → 服务器）

```json
{
  "type": "structure_change",
  "operation": "create_folder",  // 或 create_file, delete_folder, delete_file, move_folder, move_file, rename_folder, rename_file
  "payload": {
    "id": "folder_001",
    "name": "src",
    "parent_id": null
  }
}
```

**操作示例：**

**创建文件夹：**
```json
{
  "type": "structure_change",
  "operation": "create_folder",
  "payload": {
    "id": "f1",
    "name": "src",
    "parent_id": null
  }
}
```

**创建文件：**
```json
{
  "type": "structure_change",
  "operation": "create_file",
  "payload": {
    "id": "file1",
    "name": "main.py",
    "parent_id": "f1",
    "type": "python"
  }
}
```

**删除文件夹：**
```json
{
  "type": "structure_change",
  "operation": "delete_folder",
  "payload": {
    "id": "f1"
  }
}
```

**移动文件：**
```json
{
  "type": "structure_change",
  "operation": "move_file",
  "payload": {
    "id": "file1",
    "new_parent_id": "f2"
  }
}
```

**重命名文件夹：**
```json
{
  "type": "structure_change",
  "operation": "rename_folder",
  "payload": {
    "id": "f1",
    "new_name": "source"
  }
}
```

#### 3. 结构变更广播（服务器 → 所有客户端）

```json
{
  "type": "structure_changed",
  "operation": "create_folder",
  "payload": {...},
  "changed_by": "user_alice",
  "timestamp": "2025-10-30T12:00:00"
}
```

#### 4. 文件内容协作（客户端 → 服务器，如 Yjs 指令）

```json
{
  "type": "content_collaboration",
  "file_id": "file_001",
  "content_data": {
    // Yjs 或其他协作编辑器的数据格式
    "update": "base64_encoded_yjs_update"
  }
}
```

#### 5. 内容更新广播（服务器 → 其他客户端）

```json
{
  "type": "content_update",
  "file_id": "file_001",
  "content_data": {...},
  "sender": "user_bob",
  "timestamp": "2025-10-30T12:00:00"
}
```

#### 6. 成员事件通知

```json
// 成员加入
{
  "type": "member_joined",
  "member_id": "user_charlie",
  "timestamp": "2025-10-30T12:10:00"
}

// 成员离开
{
  "type": "member_left",
  "member_id": "user_charlie",
  "timestamp": "2025-10-30T12:20:00"
}
```

#### 7. 权限变更通知

```json
{
  "type": "permission_updated",
  "member_id": "user_bob",
  "new_role": "viewer",
  "changed_by": "user_alice",
  "timestamp": "2025-10-30T12:15:00"
}
```

#### 8. 错误消息

```json
{
  "type": "error",
  "message": "Permission denied: viewer role cannot edit structure",
  "timestamp": "2025-10-30T12:00:00"
}
```

## 权限说明

### 角色类型

1. **initiator（发起者）**
   - 创建会话时自动获得
   - 可以修改文件夹结构
   - 可以修改其他成员的权限
   - 不可被降级

2. **editor（编辑者）**
   - 可以修改文件夹结构
   - 结构变更需经过发起者验证
   - 可以参与文件内容协作

3. **viewer（只读）**
   - 只能查看文件夹结构
   - 可以参与文件内容协作（如果应用层允许）
   - 不能修改文件夹结构

### 权限验证流程

1. **发起者的变更**：直接应用并广播
2. **编辑者的变更**：发送请求给发起者 → 发起者验证 → 应用并广播
3. **只读者的变更**：直接拒绝，返回错误

## 使用示例

### Python 客户端示例

```python
import requests
import websocket
import json

# 1. 创建会话
response = requests.post('http://localhost:8000/api/collaboration/sessions/create/', 
                        json={'initiator': 'alice'})
session_id = response.json()['session_id']

# 2. 连接 WebSocket
ws = websocket.create_connection(
    f'ws://localhost:8000/ws/collaboration/{session_id}/alice/'
)

# 3. 接收会话信息
session_info = json.loads(ws.recv())
print(f"Connected to session: {session_info}")

# 4. 创建文件夹
ws.send(json.dumps({
    'type': 'structure_change',
    'operation': 'create_folder',
    'payload': {
        'id': 'f1',
        'name': 'src',
        'parent_id': None
    }
}))

# 5. 接收广播消息
while True:
    message = json.loads(ws.recv())
    print(f"Received: {message}")
```

### JavaScript 客户端示例

```javascript
// 1. 创建会话
const response = await fetch('http://localhost:8000/api/collaboration/sessions/create/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ initiator: 'alice' })
});
const { session_id } = await response.json();

// 2. 连接 WebSocket
const ws = new WebSocket(`ws://localhost:8000/ws/collaboration/${session_id}/alice/`);

// 3. 接收消息
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
  
  if (message.type === 'structure_changed') {
    // 更新本地文件夹结构
    updateLocalStructure(message);
  } else if (message.type === 'content_update') {
    // 更新文件内容
    updateFileContent(message);
  }
};

// 4. 发送结构变更
ws.send(JSON.stringify({
  type: 'structure_change',
  operation: 'create_file',
  payload: {
    id: 'file1',
    name: 'main.py',
    parent_id: 'f1',
    type: 'python'
  }
}));

// 5. 发送内容协作消息（如 Yjs）
ws.send(JSON.stringify({
  type: 'content_collaboration',
  file_id: 'file1',
  content_data: {
    update: encodedYjsUpdate
  }
}));
```

## 架构说明

### 内存数据结构

```python
active_sessions = {
    "session_123": {
        "session_id": "session_123",
        "initiator": "user_alice",
        "created_at": "2025-10-30T12:00:00",
        "members": {
            "user_alice": {
                "role": "initiator",
                "joined_at": "2025-10-30T12:00:00",
                "channel_name": "specific.channel.name"
            },
            "user_bob": {
                "role": "editor",
                "joined_at": "2025-10-30T12:05:00",
                "channel_name": "specific.channel.name"
            }
        },
        "structure": {
            "folders": [
                {
                    "id": "f1",
                    "name": "src",
                    "parent_id": None
                },
                {
                    "id": "f2",
                    "name": "utils",
                    "parent_id": "f1"
                }
            ],
            "files": [
                {
                    "id": "file1",
                    "name": "main.py",
                    "parent_id": "f1",
                    "type": "python"
                }
            ]
        }
    }
}
```

### 线程安全

- `SessionManager` 使用单例模式
- 所有会话操作使用线程锁（`threading.Lock`）保护
- 支持多线程并发访问

### 会话生命周期

1. **创建**：发起者调用 API 创建会话
2. **加入**：成员通过会话 ID 加入
3. **协作**：成员通过 WebSocket 进行实时协作
4. **离开**：成员断开连接或主动离开
5. **销毁**：最后一个成员离开时自动清理

## 生产环境部署

### 使用 Redis 作为 Channel Layer

修改 `webapp/settings.py`：

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

安装依赖：

```bash
pip install channels-redis
```

### 使用 Supervisor 管理进程

```ini
[program:collaboration_server]
command=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 webapp.asgi:application
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
```

## 注意事项

1. **内存限制**：所有数据存储在内存中，服务器重启会丢失所有会话
2. **扩展性**：单机部署，不支持水平扩展（除非使用 Redis Channel Layer）
3. **安全性**：生产环境需要添加身份验证和授权机制
4. **并发**：使用内存 Channel Layer 时，所有 WebSocket 必须连接到同一进程

## 故障排查

### WebSocket 连接失败

```bash
# 检查 Daphne 是否运行
ps aux | grep daphne

# 检查端口是否被占用
netstat -an | grep 8000
```

### 会话不存在

- 确保先调用创建/加入会话 API
- 检查会话 ID 是否正确
- 确认会话未被销毁（所有成员离开）

### 权限被拒绝

- 检查成员角色（viewer 不能修改结构）
- 确认操作者身份（只有发起者可以修改权限）

## 测试

运行测试（待实现）：

```bash
python manage.py test RealtimeCollaboration
```

## 许可证

根据项目主许可证
