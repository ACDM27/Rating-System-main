FROM ccr.ccs.tencentyun.com/z5882852/node:22-alpine3.21

# 设置工作目录
WORKDIR /app

# 全局安装 pnpm
RUN npm install -g pnpm --registry https://registry.npmmirror.com/

# 复制 package.json 和 pnpm-lock.yaml（如果存在）
COPY package.json pnpm-lock.yaml* ./

# 安装依赖
RUN pnpm install --frozen-lockfile --registry https://registry.npmmirror.com/

# 复制项目文件
COPY . .

# 构建项目
RUN pnpm build --mode production

# 暴露端口
EXPOSE 4173

# 启动预览服务器
CMD ["pnpm", "preview", "--host", "0.0.0.0", "--port", "80"]