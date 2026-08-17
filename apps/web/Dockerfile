FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --frozen-lockfile
COPY apps/web apps/web
ARG API_BASE_URL=http://api:8000/api/v1
ENV API_BASE_URL=$API_BASE_URL NEXT_TELEMETRY_DISABLED=1
RUN pnpm --dir apps/web build

FROM node:22-alpine
WORKDIR /app
RUN corepack enable
COPY --from=build /app/package.json /app/pnpm-lock.yaml /app/pnpm-workspace.yaml ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/apps/web ./apps/web
ENV API_BASE_URL=http://api:8000/api/v1 NEXT_TELEMETRY_DISABLED=1 NODE_ENV=production
EXPOSE 3000
CMD ["node", "apps/web/node_modules/next/dist/bin/next", "start", "apps/web"]
