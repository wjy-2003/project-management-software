# 实时协作模块快速启动指南

## 前提条件

确保已安装所有依赖:
```powershell
pip install django channels channels-redis
```

## 启动服务器

### 开发环境
```powershell
python manage.py runserver 0.0.0.0:8000
```

### 如果需要后台运行
```powershell
Start-Process python -ArgumentList "manage.py", "runserver", "0.0.0.0:8000" -WindowStyle Hidden
```

## 测试实时协作

### 1. 创建两个用户账号

访问 http://localhost:8000/admin/ 创建两个测试用户:
- user1 / password123
- user2 / password123

### 2. 用户1创建会话

1. 用 user1 登录
2. 进入"实时协作"模块
3. 点击"创建会话"
4. 上传一些测试文件(如 test.py, test.js)
5. 点击"创建"
6. 记下会话ID

### 3. 用户2加入会话

**方法1: 通过邀请**
1. 用户1在会话页面右侧"邀请成员"中输入 user2 的ID
2. 选择角色(编辑者)
3. 点击"发送邀请"

**方法2: 直接加入**
1. 用 user2 登录(使用另一个浏览器或无痕模式)
2. 在会话列表中找到会话
3. 点击"加入会话"

### 4. 测试实时编辑

1. 两个用户都打开相同的文件
2. 用户1开始编辑,观察用户2的编辑器是否实时更新
3. 用户2移动光标,观察用户1的编辑器中是否显示彩色光标
4. 修改文档后等待2秒,检查是否自动保存

## 验证功能

### ✅ WebSocket连接
- 打开浏览器开发者工具(F12) → 网络(Network)
- 筛选 WS (WebSocket)
- 应该看到 ws://localhost:8000/ws/collaboration/... 的连接
- 状态应该是 101 Switching Protocols

### ✅ 光标同步
- 用户1移动光标
- 用户2的编辑器中应该显示用户1的彩色光标
- 光标上方显示用户ID

### ✅ 内容同步
- 用户1输入文字
- 用户2应该实时看到相同内容
- 延迟应该小于100ms

### ✅ 自动保存
- 修改文档后等待2秒
- 浏览器控制台应该显示 "文件 xxx 已保存"
- 刷新页面,修改应该保留

## 故障排查

### WebSocket连接失败

**检查ASGI配置:**
```powershell
python -c "from webapp.asgi import application; print('ASGI OK')"
```

**检查路由:**
```powershell
python manage.py shell
>>> from RealtimeCollaboration.routing import websocket_urlpatterns
>>> print(websocket_urlpatterns)
```

**查看服务器日志:**
观察终端输出,应该看到:
```
WebSocket HANDSHAKING /ws/collaboration/...
WebSocket CONNECT /ws/collaboration/...
```

### 光标不显示

1. 打开浏览器控制台
2. 检查是否有 JavaScript 错误
3. 确认两个用户打开了相同文件
4. 检查 WebSocket 消息:
   ```javascript
   // 应该看到类似的消息
   {"type": "cursor_update", "file_id": "...", "position": {"line": 0, "ch": 0}}
   ```

### 内容不同步

1. 检查用户权限:
   - 查看者(Viewer)无法编辑
   - 只有编辑者(Editor)和发起人(Initiator)可以编辑

2. 检查 WebSocket 消息:
   ```javascript
   // 应该看到
   {"type": "document_change", "changes": {...}}
   ```

3. 检查浏览器控制台是否有错误

### 保存失败

1. 检查 CSRF token:
   ```javascript
   console.log(document.cookie);
   // 应该包含 csrftoken=...
   ```

2. 检查文件路径:
   ```powershell
   ls media/collaboration_sessions/
   ```

3. 检查权限:
   ```powershell
   # 确保media目录可写
   Test-Path -Path "media" -PathType Container
   ```

## 调试技巧

### 查看 WebSocket 消息

在浏览器控制台运行:
```javascript
// 拦截 WebSocket 消息
const originalSend = WebSocket.prototype.send;
WebSocket.prototype.send = function(data) {
    console.log('发送:', data);
    return originalSend.call(this, data);
};
```

### 查看远程光标

```javascript
// 列出所有远程光标
console.log(remoteCursors);

// 手动测试光标
updateRemoteCursor('test-user', {line: 5, ch: 10});
```

### 测试文档同步

```javascript
// 手动触发文档变化
applyRemoteChange({
    from: {line: 0, ch: 0},
    to: {line: 0, ch: 0},
    text: ['测试文本']
});
```

## 性能监控

### 查看消息数量

在浏览器控制台:
```javascript
let msgCount = 0;
ws.addEventListener('message', () => {
    msgCount++;
    console.log('收到消息数:', msgCount);
});
```

### 查看光标更新频率

```javascript
let cursorUpdates = 0;
setInterval(() => {
    console.log('每秒光标更新:', cursorUpdates);
    cursorUpdates = 0;
}, 1000);
```

## 常见问题

### Q: 可以支持多少并发用户?
A: InMemoryChannelLayer 适合小团队(<10人)。生产环境建议使用 Redis Channel Layer。

### Q: 断网后会丢失数据吗?
A: 未保存的修改可能丢失。建议启用自动保存(默认2秒)。

### Q: 支持哪些文件类型?
A: 所有文本文件。CodeMirror支持多种语言高亮。

### Q: 能否回滚到历史版本?
A: 当前版本不支持。未来会添加版本历史功能。

### Q: 两个用户同时编辑同一位置会怎样?
A: 后提交的修改会覆盖先前的。建议用户协调编辑区域。

## 下一步

- 配置 Redis Channel Layer 提高性能
- 添加文档历史版本
- 实现更复杂的冲突解决
- 添加语音/视频通话
- 集成代码审查功能

## 相关文档

- [REALTIME_COLLABORATION.md](REALTIME_COLLABORATION.md) - 详细功能说明
- [Django Channels 文档](https://channels.readthedocs.io/)
- [CodeMirror 文档](https://codemirror.net/5/doc/manual.html)
