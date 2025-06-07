# 構建階段
FROM node:18-alpine as builder

WORKDIR /app

# 複製 package.json 和 package-lock.json
COPY package*.json ./

# 安裝依賴
RUN npm install

# 複製源代碼
COPY . .

# 構建應用
RUN npm run build

# 運行階段
FROM nginx:alpine

# 複製 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 從構建階段複製構建好的文件
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 啟動 nginx
CMD ["nginx", "-g", "daemon off;"] 