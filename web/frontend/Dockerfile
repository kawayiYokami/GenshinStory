# --- Stage 1: Build the Vue.js application ---
FROM node:22-alpine AS build-stage

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json to leverage Docker cache
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application source code
COPY . .

# Build the application for production
# The output will be in the /app/dist directory
RUN npm run build

# --- Stage 2: Serve the application with Nginx ---
FROM nginx:stable-alpine AS production-stage

# Copy the build output from the build-stage
# The /usr/share/nginx/html is the default root directory for Nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy the custom Nginx configuration
# We will create this nginx.conf file next. It's crucial for proxying API requests.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for the Nginx server
EXPOSE 80

# The default command for the nginx image is to run nginx in the foreground.
# CMD ["nginx", "-g", "daemon off;"]