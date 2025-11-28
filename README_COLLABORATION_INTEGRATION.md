# 🚀 实时协作编辑器 - 完整集成指南

## 📁 项目结构

```
E:\Github\project-management-software\
├── webapp/                    # Django后端主项目
├── RealtimeCollaboration/      # Django实时协作应用
├── collab-editor/            # 原始前端版本（需要手动配置）
├── CollabFrontend/           # ✨ 新的集成前端版本（推荐使用）
├── .venv/                    # uv虚拟环境
├── start-backend.bat          # 后端启动脚本
├── start-frontend-collab.bat # 前端启动脚本
└── README_COLLABORATION_INTEGRATION.md
```

## ⚡ 快速启动

### 方法1：使用批处理脚本（推荐）

1. **启动后端**：
   ```bash
   双击运行：start-backend.bat
   ```

2. **启动前端**：
   ```bash
   双击运行：start-frontend-collab.bat
   ```

### 方法2：手动启动

#### 后端启动
```bash
cd E:\Github\project-management-software
.venv\Scripts\activate
python manage.py runserver 0.0.0.0:8001
```

#### 前端启动
```bash
cd E:\Github\project-management-software\CollabFrontend
npm start
```

## 🔧 技术架构

### 后端 (Django + Channels)
- **框架**: Django 5.2
- **实时通信**: Django Channels + WebSocket
- **协作引擎**: Yjs CRDT
- **数据库**: SQLite (开发环境)

### 前端 (React + Monaco Editor)
- **框架**: React 19.2
- **代码编辑器**: Monaco Editor
- **UI库**: Ant Design 6.0
- **协作引擎**: Yjs
- **通信**: WebSocket + Axios

## 🌐 端口配置

| 服务 | 端口 | 协议 | 用途 |
|------|------|------|------|
| 后端HTTP | 8001 | HTTP | REST API |
| 后端WebSocket | 8001 | WS | 实时协作 |
| 前端开发服务器 | 3000 | HTTP | React应用 |

## 🔗 连接地址

- **后端API**: `http://localhost:8001/api/collaboration/`
- **WebSocket**: `ws://localhost:8001/ws/collaboration/`
- **前端应用**: `http://localhost:3000`

## 🎯 功能特性

### ✅ 已实现功能
1. **实时协作编辑**
   - 多人同时编辑同一文件
   - 实时光标同步
   - 操作冲突自动解决

2. **文件管理**
   - 创建/删除文件和文件夹
   - 文件重命名
   - 多层级目录结构

3. **权限管理**
   - 创建者（Initiator）权限
   - 编辑者（Editor）权限
   - 查看者（Viewer）权限

4. **会话管理**
   - 创建/加入协作房间
   - 分享邀请链接
   - 实时成员状态显示

5. **代码高亮**
   - 支持多种编程语言
   - Monaco编辑器语法高亮
   - 智能代码补全

## 🔍 故障排除

### 1. WebSocket连接失败
**问题**: `WebSocket connection failed`

**解决方案**:
- 确保使用Daphne启动ASGI服务器：
  ```bash
  daphne -b 0.0.0.0 -p 8001 webapp.asgi:application
  ```
- 检查防火墙设置
- 确认端口8001未被占用

### 2. CORS错误
**问题**: `CORS policy error`

**解决方案**:
- 检查 `webapp/settings.py` 中的CORS配置：
  ```python
  CORS_ALLOWED_ORIGINS = [
      "http://localhost:3000",
      "http://127.0.0.1:3000",
  ]
  ```

### 3. 后端启动失败
**问题**: `ModuleNotFoundError`

**解决方案**:
- 确保激活uv虚拟环境：
  ```bash
  .venv\Scripts\activate
  ```
- 安装依赖：
  ```bash
  pip install -r requirements.txt
  ```

### 4. 前端启动失败
**问题**: `npm ERR!`

**解决方案**:
- 清除npm缓存：
  ```bash
  npm cache clean --force
  rm -rf node_modules package-lock.json
  npm install
  ```

## 📱 使用流程

1. **创建协作房间**
   - 点击"创建房间"按钮
   - 自动生成房间ID

2. **邀请成员**
   - 点击"分享"按钮复制链接
   - 或分享房间ID给其他用户

3. **加入协作**
   - 通过链接自动加入
   - 或手动输入房间ID

4. **文件协作**
   - 选择文件开始编辑
   - 实时查看其他用户编辑
   - 使用右键菜单管理文件

## 🔮 开发计划

### 即将推出的功能
- [ ] 语音/视频通话集成
- [ ] 版本历史记录
- [ ] 代码片段库
- [ ] 模板系统
- [ ] Docker容器化部署
- [ ] 云端同步存储

### 技术优化
- [ ] 性能优化（大文件处理）
- [ ] 离线编辑支持
- [ ] 端到端加密
- [ ] 移动端适配

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 发起Pull Request

## 📄 许可证

本项目采用MIT许可证 - 详见LICENSE文件

## 🆘 技术支持

- **文档**: 查看 `docs/` 目录
- **问题反馈**: 提交Issue
- **讨论**: 项目Discussions

---

**Happy Collaborating! 🎉**
