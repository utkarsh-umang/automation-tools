# Stage 1: Build the React app
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# VITE_API_BASE_URL is intentionally left empty so the app uses relative
# paths (e.g. /api/v1/...) — nginx in Stage 2 proxies them to the backend.
# Pass --build-arg VITE_API_BASE_URL=http://your-domain.com only if you need
# to override (e.g. a separate API domain).
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
