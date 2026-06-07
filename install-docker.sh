#!/bin/bash
# Ubuntu 22.04 安装 Docker（阿里云镜像源）

set -e

echo "==> 安装依赖..."
apt-get update
apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

echo "==> 添加阿里云 Docker GPG 密钥..."
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "==> 添加阿里云 Docker 软件源..."
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

echo "==> 更新并安装 Docker..."
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "==> 启动 Docker 服务..."
systemctl enable docker
systemctl start docker

echo "==> 配置阿里云镜像加速..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": ["https://mirror.aliyuncs.com"]
}
EOF
systemctl restart docker

echo "==> 验证安装..."
docker --version
docker compose version

echo "==> Docker 安装完成！"
