FROM node:18-alpine

WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json package-lock.json* ./
RUN npm ci

# Copy the rest of the application
COPY . .

# Build the Next.js app
RUN npm run build

# Expose the listening port
EXPOSE 3000

# Run the app
CMD ["npm", "start"]
