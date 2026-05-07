# --- Build Stage ---
FROM node:20-slim AS builder

WORKDIR /app

# Install build dependencies
COPY package*.json ./
RUN npm install

# Copy source and build
COPY . .
RUN npm run build

# --- Production Stage ---
FROM node:20-slim

WORKDIR /app

# Only copy necessary files for production
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/server.ts ./
COPY --from=builder /app/src/lib ./src/lib
COPY --from=builder /app/node_modules ./node_modules

# Ensure environment is production
ENV NODE_ENV=production
ENV PORT=3000

EXPOSE 3000

# Use tsx to run the server in production (standard for this setup)
CMD ["npx", "tsx", "server.ts"]
