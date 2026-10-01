FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ── Produção: só os estáticos do build, servidos por Nginx — nada de dev
# server do Vite (expõe /@vite/client, /@fs/*, /src/*.tsx e fontes sem build).
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
