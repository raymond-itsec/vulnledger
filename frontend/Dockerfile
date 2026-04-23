FROM node:22.22-alpine@sha256:8ea2348b068a9544dae7317b4f3aafcdc032df1647bb7d768a05a5cad1a7683f

WORKDIR /app

ARG APP_VERSION=0.1.16
ENV VITE_APP_VERSION=${APP_VERSION}

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

RUN chown -R node:node /app

USER node

EXPOSE 5173

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
