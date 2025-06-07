# 使用Node.js 18 Alpine镜像作为基础镜像
FROM node:18-alpine

# 设置工作目录
WORKDIR /app

# 安装pnpm
RUN npm install -g pnpm

# 复制package.json和pnpm-lock.yaml
COPY package.json pnpm-lock.yaml ./

# 安装依赖
RUN pnpm install --frozen-lockfile

# 复制源代码
COPY . .

# 构建应用
RUN pnpm run build

# 暴露端口
EXPOSE 8001

# 设置环境变量
ENV NODE_ENV=production
ENV PORT=8001
ENV HOST=0.0.0.0

# 启动应用
CMD ["pnpm", "run", "start:prod"] 