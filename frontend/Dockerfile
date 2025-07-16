# frontend/Dockerfile
FROM node:18

WORKDIR /app

# Copy package files (note: no frontend/ prefix since context is root)
COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install

# Copy the rest of the frontend code
COPY frontend ./

EXPOSE 5173

# Add host flag for Docker networking
CMD ["yarn", "dev", "--host", "0.0.0.0"]