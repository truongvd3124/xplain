# Stage 1: Build the React/Vite app
FROM node:20-alpine AS build

WORKDIR /app

# Sao chép package.json và package-lock.json
COPY package*.json ./

# Cài đặt dependencies
RUN npm ci

# Sao chép toàn bộ code frontend
COPY . .

# Biên dịch frontend ra thư mục dist
RUN npm run build

# Stage 2: Serve tĩnh bằng Nginx
FROM nginx:alpine

# Sao chép file cấu hình Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Sao chép sản phẩm build từ stage 1 vào thư mục phục vụ của Nginx
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
