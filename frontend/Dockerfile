FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Expose port 4173
EXPOSE 4173

# Set environment variables
ENV VITE_API_URL=http://backend:8000

# Start the application with --host flag
CMD ["npm", "run", "preview", "--", "--host"]
