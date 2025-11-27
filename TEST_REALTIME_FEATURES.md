# 实时协作功能测试指南

## 已修复的问题

### 1. ✅ 在线成员实时更新
- **问题**: 当有用户加入/离开会话时,成员列表不会更新
- **修复**: 添加了 `addMemberToList()` 和 `removeMemberFromList()` 函数
- **实现**: WebSocket收到 `member_joined` 或 `member_left` 消息时自动更新DOM

### 2. ✅ 显示自己的光标位置
- **问题**: 编辑器中看不到自己的光标
- **修复**:
  - 添加了 `cursorBlinkRate: 530` 配置让光标闪烁
  - 使用CSS增强光标可见性
  - 聚焦时光标显示为绿色

### 3. ✅ 光标位置同步准确性
- **问题**: 多用户编辑时,远程光标位置显示不准确
- **修复**:
  - 从绝对定位改为使用CodeMirror的 `setBookmark` API
  - 使用widget方式插入光标,自动跟随文档变化调整位置
  - 文档变更时bookmark会自动更新位置

## 测试步骤

### 测试1: 成员实时更新

**准备:**
1. 打开两个不同的浏览器(如Chrome和Edge)
2. 用不同账号登录(user1和user2)

**步骤:**
1. 用user1创建一个新会话
2. 记下会话ID
3. 用user2的浏览器访问会话列表,点击"打开"加入会话
4. 在user1的浏览器中观察右侧成员列表

**预期结果:**
- ✅ user1的成员列表中立即出现user2
- ✅ 在线成员数从1变成2
- ✅ 新成员旁边显示"新成员"徽章
- ✅ 绿色圆点闪烁动画

**验证命令(浏览器控制台):**
```javascript
// 检查成员列表
document.querySelectorAll('#membersList li').length  // 应该是2

// 检查在线人数
document.getElementById('onlineCount').textContent  // 应该是"2"
```

### 测试2: 自己的光标显示

**步骤:**
1. 用任一用户登录并进入会话
2. 从左侧文件树选择一个文件
3. 在编辑器中点击任意位置
4. 开始输入文字

**预期结果:**
- ✅ 光标是白色竖线,会闪烁
- ✅ 编辑器获得焦点时,光标变成绿色
- ✅ 光标位置准确,跟随输入移动
- ✅ 光标高度与行高一致

**验证:**
- 观察光标是否清晰可见
- 光标闪烁频率约每秒2次
- 点击其他位置,光标立即跟随

### 测试3: 远程光标位置准确性

**准备:**
1. 两个浏览器,两个用户
2. 都加入同一个会话
3. 都打开同一个文件

**步骤:**
1. user1在第1行输入: `console.log('test');`
2. user2在第3行输入: `var x = 10;`
3. user1观察user2的光标
4. user2移动光标到第1行末尾
5. user1在第2行插入新行: `console.log('hello');`
6. 观察user2的光标是否正确移动到第4行

**预期结果:**
- ✅ user2的光标显示在正确的位置(第3行)
- ✅ 光标上方显示user2的ID标签
- ✅ 光标是彩色的(不同用户不同颜色)
- ✅ 当user1插入新行后,user2的光标自动移到第4行
- ✅ 光标位置始终准确对应文档内容

**高级测试:**
1. user1快速连续输入多行文字
2. 观察user2的光标是否实时跟随移动
3. user2同时在其他位置输入
4. 两个光标应该都准确显示

**验证命令(浏览器控制台):**
```javascript
// 检查远程光标数量
remoteCursors.size  // 应该等于(在线用户数 - 1)

// 检查特定用户的光标
remoteCursors.forEach((cursor, userId) => {
    console.log(`用户 ${userId}:`, cursor.position);
});

// 检查光标widget是否存在
remoteCursors.forEach((cursor, userId) => {
    console.log(`${userId} widget:`, cursor.widget ? '存在' : '不存在');
});
```

### 测试4: 光标在文档编辑时的行为

**场景: 在光标前插入文字**
1. user2的光标在第5行第10个字符
2. user1在第3行插入一段文字
3. user2的光标应该保持在第5行第10个字符(不受影响)

**场景: 在光标所在行插入文字**
1. user2的光标在第5行第10个字符
2. user1在第5行第5个字符处插入文字
3. user2的光标应该自动向右移动

**场景: 删除包含光标的内容**
1. user2的光标在第5行第10个字符
2. user1删除第4-6行
3. user2的光标应该移动到合适的位置

## 调试技巧

### 1. 查看WebSocket消息
```javascript
// 在浏览器控制台运行
const oldOnMessage = ws.onmessage;
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('📨 收到消息:', data);
    oldOnMessage(event);
};
```

### 2. 监控光标更新
```javascript
// 查看光标更新频率
let cursorUpdateCount = 0;
setInterval(() => {
    console.log('光标更新次数/秒:', cursorUpdateCount);
    cursorUpdateCount = 0;
}, 1000);

// 在sendCursorUpdate函数中添加
cursorUpdateCount++;
```

### 3. 检查成员列表
```javascript
// 获取当前成员列表
const members = Array.from(document.querySelectorAll('#membersList li'))
    .map(li => li.getAttribute('data-member-id'));
console.log('当前成员:', members);
```

### 4. 查看光标详情
```javascript
// 列出所有远程光标
remoteCursors.forEach((cursor, userId) => {
    console.log(`👤 ${userId}:`);
    console.log('  位置:', cursor.position);
    console.log('  Widget:', cursor.widget);
    console.log('  元素:', cursor.element);
});
```

## 常见问题排查

### Q1: 成员加入但列表没更新
**检查:**
- 浏览器控制台是否有错误
- WebSocket是否连接(右上角连接状态)
- 运行: `console.log('WebSocket状态:', ws.readyState)` (1表示已连接)

**解决:**
- 刷新页面
- 检查服务器日志
- 确认两个用户在同一个会话

### Q2: 看不到自己的光标
**检查:**
- 编辑器是否获得焦点(点击编辑器区域)
- 文件是否已打开(标题显示文件名)
- CSS是否正确加载

**解决:**
- 点击编辑器让其获得焦点
- F12打开开发者工具 → Elements → 搜索 `.CodeMirror-cursor`
- 检查该元素的样式是否正确

### Q3: 远程光标位置不对
**检查:**
- 两个用户是否打开了相同的文件
- WebSocket消息是否正常传输
- 运行: `remoteCursors.size` 查看远程光标数量

**解决:**
- 刷新页面重新连接
- 检查控制台是否有 "光标定位失败" 错误
- 确认CodeMirror版本兼容

### Q4: 光标消失或不更新
**检查:**
- 远程用户是否还在线
- 运行: `codeEditor.getAllMarks()` 查看所有标记

**解决:**
```javascript
// 清除所有光标重新开始
remoteCursors.forEach((cursor, userId) => removeCursor(userId));
```

## 性能监控

### 监控指标:
```javascript
// 添加性能监控
const stats = {
    messagesReceived: 0,
    cursorUpdates: 0,
    documentChanges: 0
};

// 在handleWebSocketMessage中添加计数
stats.messagesReceived++;

setInterval(() => {
    console.log('📊 性能统计:');
    console.log('  消息/秒:', stats.messagesReceived);
    console.log('  光标更新/秒:', stats.cursorUpdates);
    console.log('  文档变更/秒:', stats.documentChanges);
    stats.messagesReceived = 0;
    stats.cursorUpdates = 0;
    stats.documentChanges = 0;
}, 1000);
```

## 预期性能指标

- **光标更新延迟**: < 100ms
- **文档同步延迟**: < 50ms
- **成员列表更新**: < 200ms
- **WebSocket消息大小**: < 1KB
- **每秒消息数**: < 50条(正常打字)

## 成功标准

✅ 所有测试通过
✅ 光标位置准确率 > 99%
✅ 成员列表实时更新(< 1秒延迟)
✅ 无JavaScript错误
✅ 无内存泄漏(长时间使用后性能稳定)
