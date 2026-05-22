# TaskRPG 阿里云部署指南

## 1. 阿里云服务器购买与初始化

### 1.1 购买服务器
- 产品：**轻量应用服务器** 或 **ECS**
- 配置：**2核2G** 起步（个人项目够用）
- 系统镜像：**Ubuntu 22.04 LTS**（推荐）或 CentOS 8
- 带宽：3Mbps 起步
- 地域：选择离你最近的（如华东1/华北2）

### 1.2 配置安全组（防火墙）
购买后进入控制台，配置安全组规则：

| 端口 | 用途 | 授权对象 |
|------|------|----------|
| 22 | SSH 远程连接 | 你的IP |
| 80 | HTTP 访问 | 0.0.0.0/0 |
| 443 | HTTPS（可选） | 0.0.0.0/0 |

> 注意：后端 8000 和数据库 5432 不需要暴露到公网，Nginx 反向代理即可。

### 1.3 连接服务器
```bash
ssh root@你的服务器公网IP
```

## 2. 服务器环境准备

### 2.1 更新系统
```bash
apt update && apt upgrade -y
```

### 2.2 安装 Docker
```bash
# 安装依赖
apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# 添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker 软件源
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 验证
docker --version
docker compose version
```

### 2.3 安装 Git
```bash
apt install -y git
```

## 3. 项目部署

### 3.1 克隆代码
```bash
cd /opt
git clone https://github.com/yuelingfan/taskrpg.git
cd taskrpg
```

### 3.2 配置环境变量
```bash
cp backend/.env.example .env
nano .env
```

编辑 `.env` 文件（项目根目录下，**不要提交到 Git**）：

```env
# 数据库（docker-compose 会使用这些值初始化 PostgreSQL）
DB_USER=taskrpg
DB_PASSWORD=你的强密码（修改）
DB_NAME=taskrpg

# OpenAI / DeepSeek 配置
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1

# JWT Secret（生产环境必须修改）
JWT_SECRET=你的随机长字符串（如 openssl rand -hex 32 生成）
```

### 3.3 构建并启动
```bash
# 前端构建（需要 Node.js 环境，或者本地构建后上传）
# 如果你在本地已有构建好的 dist 目录，直接上传即可
# 否则在服务器上安装 Node.js 后构建：

cd frontend
npm install
npm run build
cd ..

# 启动所有服务（Docker Compose）
docker compose up -d

# 查看运行状态
docker compose ps

# 查看日志
docker compose logs -f backend
```

### 3.4 初始化数据库
首次部署需要创建数据库表：
```bash
# 进入后端容器执行 Python 初始化
docker compose exec backend python -c "
from database import Base, engine
Base.metadata.create_all(bind=engine)
print('Tables created')
"
```

## 4. 访问应用

浏览器访问：`http://你的服务器公网IP`

- 前端：Nginx 提供静态页面
- API：`/api/*` 自动代理到后端容器
- 后端原生地址：`http://你的IP:8000`（不推荐直接访问）

## 5. 常用运维命令

```bash
# 查看所有容器状态
docker compose ps

# 查看日志
docker compose logs -f backend
docker compose logs -f postgres
docker compose logs -f nginx

# 重启服务
docker compose restart backend

# 停止所有服务
docker compose down

# 停止并删除数据卷（慎用）
docker compose down -v

# 进入数据库容器
docker compose exec postgres psql -U taskrpg -d taskrpg

# 更新代码后重新构建
git pull
docker compose down
docker compose up -d --build
```

## 6. 可选：配置 HTTPS（域名 + SSL）

如果你有域名，可以用 Caddy 或 Certbot 自动申请免费 SSL 证书：

### 6.1 安装 Certbot
```bash
apt install -y certbot python3-certbot-nginx
```

### 6.2 申请证书
```bash
certbot --nginx -d your-domain.com
```

### 6.3 修改 nginx.conf 支持 HTTPS
Certbot 会自动修改 nginx 配置，无需手动操作。

## 7. 内存优化（2核2G 服务器）

2核2G 内存比较紧张，建议做以下优化：

### 7.1 添加 Swap（虚拟内存）
```bash
# 创建 2GB swap 文件
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# 永久生效
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### 7.2 限制容器内存（已配置在 docker-compose.yml 中）
- PostgreSQL: 512MB
- Backend: 512MB
- Nginx: 128MB

### 7.3 关闭不需要的服务
```bash
systemctl disable snapd
systemctl stop snapd
```

## 8. 故障排查

### 后端启动失败
```bash
docker compose logs backend
```
常见原因：
- 环境变量缺失（检查 `.env` 文件）
- 数据库连接失败（检查 postgres 容器是否 healthy）

### 前端白屏/404
```bash
docker compose logs nginx
```
常见原因：
- `frontend/dist` 目录不存在 → 需要先 `npm run build`
- `nginx.conf` 路径错误

### 数据库连接不上
```bash
# 检查 postgres 是否运行
docker compose ps

# 检查数据库是否就绪
docker compose exec postgres pg_isready -U taskrpg
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `docker-compose.yml` | 定义 postgres + backend + nginx 三个服务 |
| `backend/Dockerfile` | 后端 Python 应用容器构建 |
| `nginx.conf` | Nginx 反向代理 + 静态文件服务配置 |
| `.env` | 环境变量（数据库密码、API Key、JWT Secret） |
| `DEPLOY.md` | 本部署文档 |
