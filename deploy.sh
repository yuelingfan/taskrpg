#!/bin/bash
set -e

# =============================================================================
# TaskRPG 远程服务器部署脚本
# 用法：
#   1. 直接登录服务器执行：bash deploy.sh
#   2. 本地一键部署：ssh root@服务器IP 'bash /opt/taskrpg/deploy.sh'
# =============================================================================

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置（根据实际情况修改）
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_NAME="taskrpg"
GIT_BRANCH="main"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# 步骤 0：前置检查
# =============================================================================
log_info "开始部署 ${PROJECT_NAME}..."
log_info "项目目录: ${PROJECT_DIR}"

cd "${PROJECT_DIR}"

# 检查必要命令（docker compose 新版插件命令）
for cmd in git docker node npm; do
    if ! command -v "$cmd" &> /dev/null; then
        log_error "缺少必要命令: $cmd，请先安装"
        exit 1
    fi
done

# 检查 docker compose 插件是否可用
if ! docker compose version &> /dev/null; then
    log_error "缺少 docker compose 插件，请执行: sudo apt install -y docker-compose-plugin"
    exit 1
fi

# 设置 docker compose 命令别名
DOCKER_COMPOSE="docker compose"

# 检查 .env 文件是否存在
if [ ! -f "backend/.env" ]; then
    log_warn "backend/.env 文件不存在，请从 backend/.env.example 复制并配置"
    log_info "执行: cp backend/.env.example backend/.env"
    cp backend/.env.example backend/.env
    log_warn "请编辑 backend/.env 填入正确的 API Key 和数据库密码后再部署"
    exit 1
fi

# 检查 docker daemon 是否运行
if ! docker info &> /dev/null; then
    log_error "Docker 守护进程未运行，请先启动 Docker"
    exit 1
fi

# =============================================================================
# 步骤 1：拉取最新代码
# =============================================================================
log_info "拉取最新代码 (branch: ${GIT_BRANCH})..."

# 检查是否是 git 仓库
if [ ! -d ".git" ]; then
    log_error "当前目录不是 git 仓库"
    exit 1
fi

# 保存本地未提交的修改（可选）
if [ -n "$(git status --porcelain)" ]; then
    log_warn "检测到本地有未提交的修改"
    read -p "是否保存本地修改并继续？[Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        log_info "取消部署"
        exit 0
    fi
    git stash push -m "deploy-auto-stash-$(date +%Y%m%d-%H%M%S)"
    log_info "本地修改已保存到 stash"
fi

git fetch origin
git checkout "${GIT_BRANCH}"
git pull origin "${GIT_BRANCH}"

CURRENT_COMMIT=$(git rev-parse --short HEAD)
log_success "代码已更新到 commit: ${CURRENT_COMMIT}"

# =============================================================================
# 步骤 2：构建前端
# =============================================================================
log_info "构建前端..."

cd "${PROJECT_DIR}/frontend"

# 安装依赖
if [ ! -d "node_modules" ]; then
    log_info "首次安装前端依赖..."
    npm install
else
    log_info "更新前端依赖..."
    npm install
fi

# 构建生产包
npm run build

if [ ! -d "dist" ]; then
    log_error "前端构建失败，dist 目录不存在"
    exit 1
fi

log_success "前端构建完成"

# =============================================================================
# 步骤 3：停止旧容器并清理
# =============================================================================
log_info "停止旧容器..."

cd "${PROJECT_DIR}"

${DOCKER_COMPOSE} down

# 清理 dangling 镜像（可选，释放磁盘空间）
DANGLING_IMAGES=$(docker images -f "dangling=true" -q)
if [ -n "$DANGLING_IMAGES" ]; then
    log_info "清理悬空镜像..."
    docker rmi $DANGLING_IMAGES || true
fi

# =============================================================================
# 步骤 4：重新构建并启动容器
# =============================================================================
log_info "重新构建并启动 Docker 容器..."

${DOCKER_COMPOSE} up -d --build

# 等待后端健康检查
log_info "等待后端服务就绪..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/ &> /dev/null; then
        log_success "后端服务已就绪"
        break
    fi
    if [ "$i" -eq 30 ]; then
        log_error "后端服务启动超时，请检查日志: docker-compose logs backend"
        exit 1
    fi
    sleep 2
done

# =============================================================================
# 步骤 5：健康检查
# =============================================================================
log_info "执行健康检查..."

# 检查容器运行状态
RUNNING_CONTAINERS=$(${DOCKER_COMPOSE} ps -q | wc -l)
if [ "$RUNNING_CONTAINERS" -lt 3 ]; then
    log_error "部分容器未正常运行，当前运行容器数: ${RUNNING_CONTAINERS}"
    ${DOCKER_COMPOSE} ps
    exit 1
fi

# 检查 SSE 接口是否可访问
if curl -sf -X POST http://localhost:8000/ai/chat/stream \
    -H "Content-Type: application/json" \
    -d '{"message":"test","user_id":1}' &> /dev/null; then
    log_success "SSE 接口可访问"
else
    log_warn "SSE 接口可能未就绪，请检查后端日志"
fi

# =============================================================================
# 步骤 6：输出部署结果
# =============================================================================
log_success "=========================================="
log_success "${PROJECT_NAME} 部署成功！"
log_success "=========================================="
log_info "当前版本: ${CURRENT_COMMIT}"
log_info "访问地址: http://$(curl -s ifconfig.me || echo 'your-server-ip')"
log_info "后端 API: http://$(curl -s ifconfig.me || echo 'your-server-ip'):8000"
log_info "查看日志: ${DOCKER_COMPOSE} logs -f backend"
log_info "停止服务: ${DOCKER_COMPOSE} down"
log_info "重启服务: ${DOCKER_COMPOSE} restart"
