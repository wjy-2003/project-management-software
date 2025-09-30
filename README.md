# project-management-software

## 在其他设备上部署项目流程

1. 克隆项目代码
   ```powershell
   git clone <仓库地址>
   cd project-management-software
   ```
2. 创建并激活虚拟环境
   ```powershell
   python -m venv pmsvenv
   .\pmsvenv\Scripts\Activate
   ```
3. 安装依赖库
   ```powershell
   pip install -r requirements.txt
   ```
4. 迁移数据库（如有）
   ```powershell
   python manage.py migrate
   ```
5. 启动开发服务器
   ```powershell
   python manage.py runserver
   ```
6. 访问项目主页
   在浏览器中打开 http://127.0.0.1:8000/

如需生产部署，请参考 Django 官方文档配置数据库、静态文件、WebSocket、Redis 等服务。

---

## Deployment Steps on Other Devices (English)

1. Clone the project repository
   ```powershell
   git clone <repository_url>
   cd project-management-software
   ```
2. Create and activate a virtual environment
   ```powershell
   python -m venv pmsvenv
   .\pmsvenv\Scripts\Activate
   ```
3. Install dependencies
   ```powershell
   pip install -r requirements.txt
   ```
4. Migrate the database (if needed)
   ```powershell
   python manage.py migrate
   ```
5. Start the development server
   ```powershell
   python manage.py runserver
   ```
6. Access the project homepage
   Open http://127.0.0.1:8000/ in your browser

For production deployment, please refer to the Django documentation for configuring database, static files, WebSocket, Redis, etc.
