FROM node:20-alpine AS build
WORKDIR /app
RUN corepack enable
COPY frontend /app
RUN pnpm install --frozen-lockfile
RUN pnpm -r build

FROM nginx:1.27-alpine
COPY --from=build /app/apps/retailer-web/dist /usr/share/nginx/html