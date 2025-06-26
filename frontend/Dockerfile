FROM node:18-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN rm -rf node_modules package-lock.json && npm install

# Copy source code
COPY . .

# Build the application
#RUN npm run build

# Expose port 4173
EXPOSE 5173

# Set environment variables
ENV VITE_API_URL=http://backend:8000

# Start the application with --host flag
CMD ["npm", "run", "dev", "--", "--host"]
