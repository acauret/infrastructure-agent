FROM node:20-alpine AS deps
WORKDIR /app
COPY app/frontend/package.json ./package.json
RUN npm install --prefer-offline --no-audit --no-fund

FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY app/frontend ./
RUN npm run build

FROM node:20-alpine AS run
ENV NODE_ENV=production
WORKDIR /app
COPY --from=build /app .
EXPOSE 3000
CMD ["npm", "start"]
