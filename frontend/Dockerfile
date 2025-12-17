# StreamHost Frontend Dockerfile
# React Application

# Build stage
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Accept build argument for backend URL
ARG REACT_APP_BACKEND_URL=http://localhost:8001

# Set environment variable for build
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Copy package files
COPY package.json yarn.lock ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy source code
COPY . .

# Build the application
RUN yarn build

# Production stage
FROM node:18-alpine AS production

WORKDIR /app

# Install serve for production
RUN yarn global add serve

# Copy built files from builder
COPY --from=builder /app/build ./build

# Create non-root user
RUN addgroup -g 1001 -S streamhost \
    && adduser -S streamhost -u 1001 \
    && chown -R streamhost:streamhost /app
USER streamhost

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Serve the application
CMD ["serve", "-s", "build", "-l", "3000"]
