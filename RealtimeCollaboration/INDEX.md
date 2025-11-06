# 实时协作功能 - 文档索引

## 📚 文档导航

### 入门文档

1. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** ⭐ 推荐首读
   - 一分钟快速开始
   - 常用命令和 API
   - 快速参考表
   - 代码示例

2. **[INSTALLATION.md](INSTALLATION.md)**
   - 详细安装步骤
   - 环境配置
   - 故障排查
   - 生产环境部署

3. **[README.md](README.md)**
   - 功能概述
   - 完整使用指南
   - 使用场景和示例
   - 架构说明

### 技术文档

4. **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)**
   - 完整 REST API 参考
   - WebSocket 协议详解
   - 所有消息类型说明
   - 请求/响应示例
   - 错误码说明

5. **[SUMMARY.md](SUMMARY.md)**
   - 实现总结
   - 文件结构说明
   - 技术栈介绍
   - 工作流程图
   - 特性和限制

### 开发文档

6. **[tests.py](tests.py)**
   - 单元测试代码
   - 测试用例参考
   - 如何编写测试

7. **[test_client.py](test_client.py)**
   - 测试客户端示例
   - 演示如何使用 API
   - 多客户端协作示例

## 🚀 快速导航

### 我想...

- **快速开始使用** → [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **安装和配置** → [INSTALLATION.md](INSTALLATION.md)
- **了解完整功能** → [README.md](README.md)
- **查看 API 文档** → [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **了解实现细节** → [SUMMARY.md](SUMMARY.md)
- **运行测试** → [tests.py](tests.py) + [test_client.py](test_client.py)

## 📂 核心代码文件

| 文件 | 说明 | 重要性 |
|------|------|--------|
| **session_manager.py** | 内存会话管理器 | ⭐⭐⭐ |
| **consumers.py** | WebSocket 消费者 | ⭐⭐⭐ |
| **views.py** | REST API 视图 | ⭐⭐⭐ |
| **routing.py** | WebSocket 路由 | ⭐⭐ |
| **urls.py** | HTTP URL 配置 | ⭐⭐ |
| **tests.py** | 单元测试 | ⭐⭐ |
| test_client.py | 测试客户端 | ⭐ |
| models.py | 模型（未使用） | - |
| admin.py | Admin（未使用） | - |

## 🔧 项目配置文件

已修改的项目配置：

1. **webapp/settings.py**
   - 添加了 `daphne`、`channels`、`RealtimeCollaboration` 到 `INSTALLED_APPS`
   - 配置了 `ASGI_APPLICATION`
   - 配置了 `CHANNEL_LAYERS`

2. **webapp/asgi.py**
   - 完全重写，添加 WebSocket 支持
   - 配置了路由分发器

3. **webapp/urls.py**
   - 添加了 `/api/collaboration/` 路由

4. **requirements.txt**
   - 添加了 `daphne>=4.0.0`

## 📖 阅读顺序建议

### 新手用户

1. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 快速了解
2. [INSTALLATION.md](INSTALLATION.md) - 安装配置
3. [README.md](README.md) - 详细使用指南
4. 运行 [test_client.py](test_client.py) - 实际体验

### 开发者

1. [SUMMARY.md](SUMMARY.md) - 了解整体架构
2. [session_manager.py](session_manager.py) - 核心数据管理
3. [consumers.py](consumers.py) - WebSocket 处理逻辑
4. [views.py](views.py) - REST API 实现
5. [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API 详细规范
6. [tests.py](tests.py) - 测试用例

### API 用户

1. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - API 快速参考
2. [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - 完整 API 文档
3. [test_client.py](test_client.py) - 客户端示例

## 🎯 常见任务

### 启动服务

```bash
# 查看：INSTALLATION.md > 运行服务
daphne webapp.asgi:application
```

### 创建会话

```bash
# 查看：QUICK_REFERENCE.md > 核心 API
# 或：API_DOCUMENTATION.md > 创建会话
curl -X POST http://localhost:8000/api/collaboration/sessions/create/ \
  -H "Content-Type: application/json" \
  -d '{"initiator": "alice"}'
```

### 连接 WebSocket

```python
# 查看：QUICK_REFERENCE.md > WebSocket
# 或：test_client.py
import websocket
ws = websocket.create_connection(
    f'ws://localhost:8000/ws/collaboration/{session_id}/{member_id}/'
)
```

### 运行测试

```bash
# 查看：INSTALLATION.md > 测试安装
python manage.py test RealtimeCollaboration
```

### 故障排查

```bash
# 查看：INSTALLATION.md > 故障排查
# 或：QUICK_REFERENCE.md > 常见问题
```

## 💡 关键概念

### 会话 (Session)
- 临时协作空间
- 由发起者创建
- 存储在内存中
- 最后一个成员离开时销毁
- 详见：[README.md](README.md#核心特性)

### 成员角色 (Roles)
- `initiator`: 发起者（所有权限）
- `editor`: 编辑者（可修改结构）
- `viewer`: 只读（仅查看）
- 详见：[API_DOCUMENTATION.md](API_DOCUMENTATION.md#角色权限说明)

### 文件夹结构 (Structure)
- 由发起者维护权威版本
- 支持 8 种操作（创建、删除、移动、重命名）
- 实时同步到所有成员
- 详见：[QUICK_REFERENCE.md](QUICK_REFERENCE.md#文件夹结构操作)

### 消息类型 (Message Types)
- 结构变更、内容协作、成员事件、权限变更
- 详见：[API_DOCUMENTATION.md](API_DOCUMENTATION.md#消息类型)

## 🔍 代码导航

### 想要实现类似功能？

**会话管理**：
```python
# 查看 session_manager.py
session_id = session_manager.create_session(initiator)
session_manager.add_member(session_id, member_id, role)
```

**WebSocket 处理**：
```python
# 查看 consumers.py > CollaborationConsumer
async def receive(self, text_data):
    # 处理消息逻辑
```

**REST API**：
```python
# 查看 views.py
@csrf_exempt
@require_http_methods(["POST"])
def create_session(request):
    # API 实现逻辑
```

## 🌟 核心特性速览

✅ 无数据库依赖  
✅ 实时 WebSocket 通信  
✅ 三级权限控制  
✅ 文件夹结构同步  
✅ 自动会话清理  
✅ 线程安全  
✅ 完整的 REST API  
✅ 详细的文档和测试  

## 📦 依赖包

```
Django>=4.2
channels>=4.0.0
daphne>=4.0.0
```

测试依赖（可选）：
```
requests>=2.31.0
websocket-client>=1.6.0
```

## 🤝 贡献

欢迎贡献！请参考：
- 代码风格：[docs/coding_style.md](../docs/coding_style.md)
- Git 使用：[docs/git_usage_tutorial.md](../docs/git_usage_tutorial.md)

## 📝 版本历史

- **v1.0** (2025-10-30): 初始实现
  - 完成所有核心功能
  - 提供完整文档
  - 包含单元测试和示例客户端

## 📄 许可证

根据项目主许可证

---

**需要帮助？**
1. 先查看 [QUICK_REFERENCE.md](QUICK_REFERENCE.md) 快速参考
2. 查看 [INSTALLATION.md](INSTALLATION.md) 故障排查部分
3. 运行测试验证功能：`python manage.py test RealtimeCollaboration`

**准备好了？**
→ 开始阅读 [QUICK_REFERENCE.md](QUICK_REFERENCE.md) 快速上手！
