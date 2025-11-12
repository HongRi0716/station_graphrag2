# Build stage
FROM apecloud-registry.cn-zhangjiakou.cr.aliyuncs.com/apecloud/node:20.18.0-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json yarn.lock* ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy source code
COPY . .

# Build the Next.js application
RUN yarn build

# Production stage
FROM apecloud-registry.cn-zhangjiakou.cr.aliyuncs.com/apecloud/node:20.18.0-alpine

WORKDIR /app

# Copy built application from builder stage
COPY --from=builder /app/build ./

# Install pm2 globally
RUN yarn global add pm2

ENV HOSTNAME="0.0.0.0"
ENV NODE_ENV=production
ENV PORT=3000

EXPOSE 3000

# server.js is created by next build from the standalone output
# https://nextjs.org/docs/pages/api-reference/config/next-config-js/output
CMD ["pm2-runtime", "start", "server.js"]

