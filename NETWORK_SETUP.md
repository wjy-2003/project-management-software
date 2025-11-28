# 网络访问配置指南

## 快速启动

### 1. 启动服务器
```powershell
python manage.py runserver 0.0.0.0:8000
```

### 2. 查看本机IP地址
```powershell
ipconfig
```
找到"以太网适配器"或"无线局域网适配器"下的"IPv4 地址"，例如：`192.168.1.100`

### 3. 从其他设备访问
在浏览器中输入：`http://192.168.1.100:8000`

---

## 如果连接慢或超时，请按以下步骤排查：

### ✅ 步骤1: 检查Windows防火墙

**方法1：临时关闭防火墙测试**
1. 打开"Windows安全中心"
2. 点击"防火墙和网络保护"
3. 选择当前活动的网络配置文件
4. 关闭"Windows Defender 防火墙"
5. 测试能否访问

**方法2：添加防火墙规则（推荐）**
```powershell
# 以管理员身份运行PowerShell
netsh advfirewall firewall add rule name="Django Dev Server" dir=in action=allow protocol=TCP localport=8000
```

### ✅ 步骤2: 检查网络连接

**测试网络连通性：**
```powershell
# 从另一台电脑ping服务器
ping 192.168.1.100

# 测试端口是否开放
Test-NetConnection -ComputerName 192.168.1.100 -Port 8000
```

### ✅ 步骤3: 使用不同端口

有时8000端口可能被占用或被阻止，尝试使用其他端口：
```powershell
python manage.py runserver 0.0.0.0:8080
```
然后访问：`http://192.168.1.100:8080`

### ✅ 步骤4: 检查杀毒软件

某些杀毒软件可能阻止网络连接，暂时禁用杀毒软件测试。

### ✅ 步骤5: 检查路由器设置

确保两台电脑在同一局域网内：
- 连接到相同的WiFi或路由器
- 检查是否启用了"AP隔离"（客户端隔离）功能，如果启用请关闭

---

## 性能优化建议

### 1. 使用有线连接
WiFi可能比有线网络慢，如果可能，使用网线连接。

### 2. 减少中间件
临时注释掉不需要的中间件：
```python
# 在settings.py中
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # "django.middleware.csrf.CsrfViewMiddleware",  # 临时禁用测试
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # "django.middleware.clickjacking.XFrameOptionsMiddleware",  # 临时禁用测试
]
```

### 3. 启用Gzip压缩
```python
# 在settings.py的MIDDLEWARE中添加
"django.middleware.gzip.GZipMiddleware",
```

### 4. 静态文件服务
如果访问静态文件很慢，考虑使用WhiteNoise：
```powershell
pip install whitenoise
```

---

## 常见问题

### Q: 访问速度很慢但能连接
**A:** 可能是DNS解析问题，直接使用IP地址而不是主机名

### Q: 连接超时
**A:**
1. 检查防火墙设置
2. 确认两台电脑在同一网络
3. 尝试使用不同端口

### Q: 页面加载慢
**A:**
1. 检查静态文件是否正确加载
2. 打开浏览器开发者工具(F12)查看网络请求
3. 检查是否有卡住的请求

### Q: WebSocket连接失败
**A:**
1. 确保使用ws://而不是wss://
2. 检查Channels配置
3. 查看服务器日志

---

## 调试命令

### 查看Django服务器日志
启动时添加详细日志：
```powershell
python manage.py runserver 0.0.0.0:8000 --verbosity 2
```

### 查看所有网络连接
```powershell
netstat -ano | findstr :8000
```

### 检查进程占用端口
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess
```

---

## 紧急方案：使用ngrok

如果局域网配置困难，可以使用ngrok创建公网隧道：

```powershell
# 1. 下载ngrok: https://ngrok.com/download
# 2. 启动Django服务器
python manage.py runserver

# 3. 在另一个终端运行ngrok
ngrok http 8000

# 4. 使用ngrok提供的公网URL访问
```

---

## 联系支持

如果以上方法都无法解决问题，请检查：
1. 服务器控制台是否有错误信息
2. 浏览器控制台(F12)是否有错误
3. 网络配置是否正确
