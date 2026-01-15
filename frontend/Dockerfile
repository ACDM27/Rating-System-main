# Build stage
FROM node:20-alpine as builder

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm --registry=https://registry.npmmirror.com

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies (use mirror for speed in China)
RUN pnpm install --frozen-lockfile --registry=https://registry.npmmirror.com

# Copy source code
COPY . .

# Build for production
RUN pnpm build

# Production stage
FROM nginx:alpine

# Copy build artifacts from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY default.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]