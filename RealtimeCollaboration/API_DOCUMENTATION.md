# 实时协作 API 文档

## 基本信息

- **Base URL**: `http://localhost:8000/api/collaboration/`
- **WebSocket URL**: `ws://localhost:8000/ws/collaboration/`
- **Content-Type**: `application/json`

## REST API 端点

### 1. 创建会话

创建新的协作会话，调用者自动成为发起者。

**端点**: `POST /api/collaboration/sessions/create/`

**请求体**:
```json
{
  "initiator": "user_id"
}
```

**响应** (201 Created):
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Session created successfully"
}
```

**错误响应** (400 Bad Request):
```json
{
  "success": false,
  "message": "Initiator ID is required"
}
```

---

### 2. 获取会话信息

获取会话的详细信息，包括成员列表和文件夹结构。

**端点**: `GET /api/collaboration/sessions/{session_id}/`

**路径参数**:
- `session_id`: 会话唯一标识符

**响应** (200 OK):
```json
{
  "success": true,
  "session": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "initiator": "alice",
    "created_at": "2025-10-30T12:00:00.000000",
    "members": [
      {
        "member_id": "alice",
        "role": "initiator",
        "joined_at": "2025-10-30T12:00:00.000000"
      },
      {
        "member_id": "bob",
        "role": "editor",
        "joined_at": "2025-10-30T12:05:00.000000"
      }
    ],
    "structure": {
      "folders": [
        {
          "id": "f1",
          "name": "src",
          "parent_id": null
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

**错误响应** (404 Not Found):
```json
{
  "success": false,
  "message": "Session not found"
}
```

---

### 3. 加入会话

加入现有的协作会话。

**端点**: `POST /api/collaboration/sessions/{session_id}/join/`

**路径参数**:
- `session_id`: 会话唯一标识符

**请求体**:
```json
{
  "member_id": "bob",
  "role": "editor"
}
```

**字段说明**:
- `member_id`: 成员唯一标识符（必需）
- `role`: 成员角色，可选值为 `"editor"` 或 `"viewer"`，默认为 `"viewer"`

**响应** (200 OK):
```json
{
  "success": true,
  "message": "Joined session successfully"
}
```

**错误响应**:
```json
// 400 Bad Request - 缺少参数
{
  "success": false,
  "message": "Member ID is required"
}

// 400 Bad Request - 无效角色
{
  "success": false,
  "message": "Invalid role. Must be \"editor\" or \"viewer\""
}

// 404 Not Found - 会话不存在
{
  "success": false,
  "message": "Session not found"
}
```

---

### 4. 离开会话

离开协作会话。如果是最后一个成员离开，会话将被销毁。

**端点**: `POST /api/collaboration/sessions/{session_id}/leave/`

**路径参数**:
- `session_id`: 会话唯一标识符

**请求体**:
```json
{
  "member_id": "bob"
}
```

**响应** (200 OK):
```json
{
  "success": true,
  "message": "Left session successfully",
  "session_destroyed": false
}
```

**字段说明**:
- `session_destroyed`: 布尔值，表示会话是否因最后一个成员离开而被销毁

---

### 5. 更新成员权限

更新成员的角色权限。**仅发起者可调用此接口**。

**端点**: `POST /api/collaboration/sessions/{session_id}/permissions/`

**路径参数**:
- `session_id`: 会话唯一标识符

**请求体**:
```json
{
  "initiator_id": "alice",
  "member_id": "bob",
  "role": "editor"
}
```

**字段说明**:
- `initiator_id`: 发起者标识符（用于验证权限）
- `member_id`: 目标成员标识符
- `role`: 新角色，可选值为 `"editor"` 或 `"viewer"`

**响应** (200 OK):
```json
{
  "success": true,
  "message": "Permission updated successfully"
}
```

**错误响应**:
```json
// 403 Forbidden - 权限被拒绝
{
  "success": false,
  "message": "Permission denied: only initiator can change permissions"
}

// 400 Bad Request - 更新失败
{
  "success": false,
  "message": "Failed to update permission. Member may not exist."
}
```

---

### 6. 获取成员列表

获取会话中所有成员的列表。

**端点**: `GET /api/collaboration/sessions/{session_id}/members/`

**路径参数**:
- `session_id`: 会话唯一标识符

**响应** (200 OK):
```json
{
  "success": true,
  "members": [
    {
      "member_id": "alice",
      "role": "initiator",
      "joined_at": "2025-10-30T12:00:00.000000"
    },
    {
      "member_id": "bob",
      "role": "editor",
      "joined_at": "2025-10-30T12:05:00.000000"
    }
  ]
}
```

---

### 7. 获取文件夹结构

获取会话的文件夹和文件结构。

**端点**: `GET /api/collaboration/sessions/{session_id}/structure/`

**路径参数**:
- `session_id`: 会话唯一标识符

**响应** (200 OK):
```json
{
  "success": true,
  "structure": {
    "folders": [
      {
        "id": "f1",
        "name": "src",
        "parent_id": null
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
```

---

### 8. 获取统计信息

获取系统的统计信息，包括当前活跃会话数量。

**端点**: `GET /api/collaboration/stats/`

**响应** (200 OK):
```json
{
  "success": true,
  "active_sessions": 5
}
```

---

## WebSocket 协议

### 连接

**URL 格式**: `ws://localhost:8000/ws/collaboration/{session_id}/{member_id}/`

**URL 参数**:
- `session_id`: 会话唯一标识符
- `member_id`: 成员唯一标识符

**连接流程**:
1. 客户端建立 WebSocket 连接
2. 服务器验证会话是否存在
3. 如果验证成功，服务器发送初始会话信息
4. 连接建立，可以开始发送/接收消息

### 初始消息（服务器 → 客户端）

连接成功后，服务器立即发送会话信息：

```json
{
  "type": "session_info",
  "session": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "initiator": "alice",
    "members": [...],
    "structure": {...}
  },
  "timestamp": "2025-10-30T12:00:00.000000"
}
```

### 消息类型

#### 1. 文件夹结构变更请求（客户端 → 服务器）

**消息格式**:
```json
{
  "type": "structure_change",
  "operation": "operation_name",
  "payload": {
    // 操作相关的数据
  }
}
```

**支持的操作**:

##### a. 创建文件夹
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

##### b. 创建文件
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

##### c. 删除文件夹
```json
{
  "type": "structure_change",
  "operation": "delete_folder",
  "payload": {
    "id": "f1"
  }
}
```

##### d. 删除文件
```json
{
  "type": "structure_change",
  "operation": "delete_file",
  "payload": {
    "id": "file1"
  }
}
```

##### e. 移动文件夹
```json
{
  "type": "structure_change",
  "operation": "move_folder",
  "payload": {
    "id": "f1",
    "new_parent_id": "f2"
  }
}
```

##### f. 移动文件
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

##### g. 重命名文件夹
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

##### h. 重命名文件
```json
{
  "type": "structure_change",
  "operation": "rename_file",
  "payload": {
    "id": "file1",
    "new_name": "index.py"
  }
}
```

#### 2. 结构变更广播（服务器 → 所有客户端）

当结构变更被应用后，服务器向所有客户端广播：

```json
{
  "type": "structure_changed",
  "operation": "create_folder",
  "payload": {
    "id": "f1",
    "name": "src",
    "parent_id": null
  },
  "changed_by": "alice",
  "timestamp": "2025-10-30T12:00:00.000000"
}
```

#### 3. 文件内容协作（客户端 → 服务器）

用于发送文件内容变更，如 Yjs 更新：

```json
{
  "type": "content_collaboration",
  "file_id": "file1",
  "content_data": {
    "update": "base64_encoded_yjs_update",
    "clock": 42
  }
}
```

**字段说明**:
- `file_id`: 文件唯一标识符
- `content_data`: 内容数据，格式由协作编辑器决定（如 Yjs、OT 等）

#### 4. 内容更新广播（服务器 → 其他客户端）

服务器将内容更新转发给其他客户端（不发送给发送者）：

```json
{
  "type": "content_update",
  "file_id": "file1",
  "content_data": {
    "update": "base64_encoded_yjs_update",
    "clock": 42
  },
  "sender": "bob",
  "timestamp": "2025-10-30T12:00:00.000000"
}
```

#### 5. 成员事件通知（服务器 → 所有客户端）

##### 成员加入
```json
{
  "type": "member_joined",
  "member_id": "charlie",
  "timestamp": "2025-10-30T12:10:00.000000"
}
```

##### 成员离开
```json
{
  "type": "member_left",
  "member_id": "charlie",
  "timestamp": "2025-10-30T12:20:00.000000"
}
```

#### 6. 权限变更通知（服务器 → 所有客户端）

```json
{
  "type": "permission_updated",
  "member_id": "bob",
  "new_role": "viewer",
  "changed_by": "alice",
  "timestamp": "2025-10-30T12:15:00.000000"
}
```

#### 7. 错误消息（服务器 → 客户端）

```json
{
  "type": "error",
  "message": "Permission denied: viewer role cannot edit structure",
  "timestamp": "2025-10-30T12:00:00.000000"
}
```

**常见错误消息**:
- `"Permission denied: viewer role cannot edit structure"` - 只读成员尝试修改结构
- `"Permission denied: only initiator can change permissions"` - 非发起者尝试修改权限
- `"Session not found"` - 会话不存在
- `"Unknown operation: xxx"` - 未知的操作类型
- `"Invalid JSON format"` - JSON 格式错误

---

## 角色权限说明

### 角色类型

| 角色 | 查看结构 | 修改结构 | 修改权限 | 参与内容协作 |
|------|---------|---------|---------|-------------|
| **initiator** | ✓ | ✓（直接应用） | ✓ | ✓ |
| **editor** | ✓ | ✓（需验证） | ✗ | ✓ |
| **viewer** | ✓ | ✗ | ✗ | ✓ |

### 权限规则

1. **发起者 (initiator)**:
   - 创建会话时自动成为发起者
   - 拥有所有权限
   - 可以直接修改文件夹结构
   - 可以修改其他成员的权限
   - 角色不可更改

2. **编辑者 (editor)**:
   - 可以修改文件夹结构
   - 结构变更需要经过发起者验证
   - 不能修改其他成员的权限
   - 可以参与文件内容协作

3. **只读 (viewer)**:
   - 只能查看文件夹结构
   - 不能修改文件夹结构
   - 不能修改权限
   - 可以参与文件内容协作（如果应用层允许）

### 结构变更验证流程

```
发起者的变更:
  客户端 → 服务器 → 直接应用 → 广播给所有客户端

编辑者的变更:
  客户端 → 服务器 → 发送请求给发起者 → 发起者验证 → 应用 → 广播

只读者的变更:
  客户端 → 服务器 → 拒绝 → 返回错误消息
```

---

## 错误码

| HTTP 状态码 | 说明 |
|-----------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 403 | 权限被拒绝 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

**WebSocket 关闭码**:
| 关闭码 | 说明 |
|-------|------|
| 4004 | 会话不存在 |

---

## 使用示例

### Python 示例

```python
import requests
import websocket
import json

# 1. 创建会话
response = requests.post(
    'http://localhost:8000/api/collaboration/sessions/create/',
    json={'initiator': 'alice'}
)
session_id = response.json()['session_id']

# 2. 连接 WebSocket
ws = websocket.create_connection(
    f'ws://localhost:8000/ws/collaboration/{session_id}/alice/'
)

# 3. 接收会话信息
session_info = json.loads(ws.recv())
print(session_info)

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

# 5. 监听消息
while True:
    message = json.loads(ws.recv())
    print(f"Received: {message}")
```

### JavaScript 示例

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
};

// 4. 创建文件
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
```

---

## 最佳实践

1. **连接管理**:
   - 在连接 WebSocket 前先调用加入会话 API
   - 监听 WebSocket 关闭事件并实现重连机制
   - 使用心跳机制保持连接活跃

2. **结构同步**:
   - 收到 `structure_changed` 消息后立即更新本地结构
   - 使用乐观更新策略提升用户体验
   - 处理冲突时以服务器广播为准

3. **错误处理**:
   - 监听 `error` 类型消息并向用户显示
   - 对于权限错误，禁用相应的 UI 操作
   - 实现重试机制处理网络错误

4. **性能优化**:
   - 批量发送结构变更而非逐个发送
   - 对频繁的内容协作消息进行防抖处理
   - 大文件结构使用虚拟滚动

---

## 限制和注意事项

1. **内存存储**: 所有数据存储在内存中，服务器重启会丢失所有会话
2. **单机部署**: 默认使用内存 Channel Layer，不支持多服务器部署
3. **无认证**: 当前版本不包含身份验证，生产环境需要添加
4. **会话持久化**: 会话在最后一个成员离开时自动销毁
5. **结构大小**: 没有对文件夹结构大小的限制，建议应用层控制
