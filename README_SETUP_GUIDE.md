# 🚀 项目设置和运行指南

## 📦 前端依赖下载说明

### ✅ **是的，`npm install` 会自动下载依赖**

当你运行 `npm install` 时，会自动：

1. **下载依赖包**：
   - React 19.2.0
   - Monaco Editor 4.7.0
   - Ant Design 6.0.0
   - Axios 1.13.2
   - Yjs 13.6.27
   - Yjs WebSocket Provider 3.0.0
   - React Scripts 5.0.1

2. **创建 node_modules** 目录：
   - 所有依赖文件都会下载到 `CollabFrontend/node_modules/`
   - 这个目录已在 `.gitignore` 中被忽略，不会被提交到版本控制

3. **生成 package-lock.json**：
   - 锁定确切版本号，确保可重复构建
   - 包含依赖树的详细信息

## 🔧 **完整设置步骤**

### **方法1：快速设置（推荐）**

#### 步骤1：克隆项目
```bash
git clone <项目仓库地址>
cd project-management-software
```

#### 步骤2：设置后端
```bash
# 激活Python虚拟环境
.venv\Scripts\activate

# 安装Python依赖（如果需要）
pip install -r requirements.txt

# 运行数据库迁移
python manage.py migrate

# 启动后端
python manage.py runserver 0.0.0.0:8001
```

#### 步骤3：设置前端
```bash
# 进入前端目录
cd CollabFrontend

# 安装前端依赖（自动下载）
npm install

# 启动前端
npm start
```

### **方法2：Docker设置（生产环境）**

创建 `docker-compose.yml`：
```yaml
version: '3.8'

services:
  backend:
    build: ./webapp
    ports:
      - "8001:8001"
    environment:
      - DEBUG=1
      - ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
    command: python manage.py runserver 0.0.0.0:8001
    volumes:
      - .:/app

  frontend:
    build: ./CollabFrontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_BACKEND_IP=localhost
      - REACT_APP_BACKEND_PORT=8001
      - REACT_APP_API_BASE=http://localhost:8001/api/collaboration
      - REACT_APP_WS_BASE=ws://localhost:8001/ws/collaboration
    depends_on:
      - backend
    command: npm start
    volumes:
      - ./CollabFrontend:/app
      - /app/node_modules
```

运行：
```bash
docker-compose up
```

## 📋 依赖包详细说明

### **核心依赖**：
```json
{
  "react": "^19.2.0",                    // UI框架
  "react-dom": "^19.2.0",                 // DOM渲染
  "@monaco-editor/react": "^4.7.0",     // 代码编辑器
  "antd": "^6.0.0",                       // UI组件库
  "axios": "^1.13.2",                    // HTTP客户端
  "yjs": "^13.6.27",                     // 协作引擎
  "y-websocket": "^3.0.0",             // WebSocket连接
  "react-scripts": "^5.0.1"               // 构建工具
}
```

### **下载大小**：
- **总大小**：约 200-300MB
- **网络速度**：取决于网络环境
- **时间**：首次安装需要 2-5 分钟

## ⚙️ **环境配置**

### **前端环境变量** (.env)：
```env
# 开发环境
REACT_APP_BACKEND_IP=localhost
REACT_APP_BACKEND_PORT=8001
REACT_APP_API_BASE=http://localhost:8001/api/collaboration
REACT_APP_WS_BASE=ws://localhost:8001/ws/collaboration

# 生产环境（部署时）
REACT_APP_BACKEND_IP=your-server-domain.com
REACT_APP_BACKEND_PORT=8001
REACT_APP_API_BASE=https://your-server-domain.com/api/collaboration
REACT_APP_WS_BASE=wss://your-server-domain.com/ws/collaboration
```

### **后端环境变量**：
```python
# Django settings/webapp.py
import os

# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'pmsdb.sqlite3',
    }
}

# 调试模式
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

# 允许的主机
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# CORS设置
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://yourdomain.com"  # 生产环境
]
```

## 🐛 **常见问题和解决方案**

### **问题1：依赖下载失败**
```bash
# 清除npm缓存
npm cache clean --force

# 删除node_modules和package-lock.json
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

### **问题2：端口冲突**
```bash
# 检查端口占用
netstat -ano | findstr :8001  # Windows
netstat -tulpn | grep :8001  # Linux/Mac

# 修改端口
# 后端：python manage.py runserver 0.0.0.0:8002
# 前端：修改 .env 中的端口配置
```

### **问题3：权限问题**
```bash
# Windows下权限问题
npm config set prefix %APPDATA%\npm

# 使用管理员权限
Run as Administrator
```

### **问题4：离线安装**
```bash
# 下载离线包
npm pack <package-name>

# 安装离线包
npm install ./<package-name>.tgz
```

## 📦 **包管理器选择**

### **npm（默认）**：
```bash
npm install
npm start
npm run build
```

### **yarn（替代）**：
```bash
# 安装yarn
npm install -g yarn

# 使用yarn
yarn install
yarn start
yarn build
```

### **pnpm（快速）**：
```bash
# 安装pnpm
npm install -g pnpm

# 使用pnpm（更快，节省磁盘空间）
pnpm install
pnpm start
pnpm build
```

## 🌐 **网络配置**

### **代理设置**：
```bash
# 设置npm代理
npm config set proxy http://proxy.company.com:8080

# 设置npm registry
npm config set registry https://registry.npm.taobao.org

# 设置GitHub packages
npm config set @github:registry https://npm.pkg.github.com
```

### **私有npm包**：
```bash
# 登录私有registry
npm login

# 安装私有包
npm install @company/private-package

# 使用.npmrc配置文件
echo "@company:registry=https://npm.company.com" > .npmrc
```

## 🔒 **安全考虑**

### **依赖安全**：
```json
{
  "engines": {
    "node": ">=14.0.0",
    "npm": ">=6.0.0"
  },
  "browserslist": [
    ">0.2%",
    "not dead",
    "not op_mini all"
  ]
}
```

### **生产构建**：
```bash
# 生产构建
npm run build

# 分析构建包大小
npm run build --analyze

# 源码映射
npm run build -- --source-map
```

## 📱 **多平台支持**

### **Windows**：
```powershell
# PowerShell
npm install
npm start

# 批处理
start-frontend.bat
```

### **Linux/Mac**：
```bash
#!/bin/bash
# 安装依赖
npm install

# 启动开发服务器
npm start

# 构建生产版本
npm run build
```

### **WSL（Windows子系统）**：
```bash
# 在WSL中启动前端
npm start

# 从Windows访问
# 浏览器访问：http://localhost:3000
```

## 🚀 **一键启动脚本**

### **Windows (start-dev.bat)**：
```batch
@echo off
echo ========================================
echo    启动开发环境
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 启动后端...
start "Django Backend" /min cmd /k "cd /d %~dp0 && .venv\Scripts\activate && python manage.py runserver 0.0.0.0:8001"

timeout /t 3
echo [2/3] 启动前端...
start "React Frontend" /min cmd /k "cd /d %~dp0\CollabFrontend && npm start"

echo.
echo 开发环境已启动！
echo - 后端: http://localhost:8001
echo - 前端: http://localhost:3000
echo.
pause
```

### **Linux/Mac (start-dev.sh)**：
```bash
#!/bin/bash
echo "========================================"
echo "    启动开发环境"
echo "========================================"

cd "$(dirname "$0")"

# 启动后端
echo "[1/2] 启动后端..."
gnome-terminal -- python manage.py runserver 0.0.0.0:8001 &
BACKEND_PID=$!

# 等待后端启动
sleep 5

# 启动前端
echo "[2/2] 启动前端..."
gnome-terminal -- npm start &
FRONTEND_PID=$!

echo ""
echo "开发环境已启动！"
echo "- 后端: http://localhost:8001"
echo "- 前端: http://localhost:3000"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 等待用户中断
trap "echo '停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

wait
```

## 📊 **性能优化**

### **构建优化**：
```json
// webpack.config.js (如果需要)
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all',
    },
    minimizer: [
      '...(<...>)',
      '@...',
      'css-minimizer-...'],
  },
}
```

### **缓存配置**：
```json
// next.config.js (如果使用Next.js)
module.exports = {
  onDemandEntries: ['webpackHotDevClient'],
  webpack(config, { isServer }) {
    config.optimization.splitChunks = {
      chunks: 'all',
      cache: true,
    }
    return config
  },
}
```

## 📋 **检查清单**

在运行项目前，确保：

- [ ] Python 3.11+ 已安装
- [ ] Node.js 14+ 已安装
- [ ] 端口 8001 和 3000 未被占用
- [ ] 防火墙允许这些端口
- [ ] 足够的磁盘空间（至少 1GB）
- [ ] 网络连接正常

## 🎯 **总结**

**是的**，`npm install` 会自动下载所有必要的依赖包，但需要注意：

1. **首次安装**：需要网络下载，时间较长
2. **缓存机制**：第二次安装会更快
3. **版本锁定**：package-lock.json 确保版本一致性
4. **平台差异**：不同操作系统可能有细微差异
5. **网络问题**：考虑使用镜像或代理

通过以上配置，任何人都可以快速设置和运行整个项目！🚀
