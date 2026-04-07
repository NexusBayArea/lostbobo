# Frontend Dockerfile
# Stage 1: Build
FROM node:20-slim AS build

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install --silent

# Copy source code
COPY . .

# Build arg for API URL
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Build the app
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
