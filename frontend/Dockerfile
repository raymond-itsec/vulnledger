# Node major version MUST match `.nvmrc` at the repo root. CI workflows
# read .nvmrc; this Dockerfile pins a specific minor + digest for
# supply-chain hardening. When bumping Node:
#   1. Update .nvmrc (single source of truth for major)
#   2. Update this FROM line (specific digest + minor for image)
#   3. Regenerate frontend/package-lock.json against the new Node
FROM node:26.0-alpine@sha256:30f5a66e7265ef70aac56b4753ffa7905e54eca1084bc25503893ad8e9273f05

WORKDIR /app

ARG APP_VERSION
ENV VITE_APP_VERSION=${APP_VERSION}

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

RUN chown -R node:node /app

USER node

EXPOSE 5173

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
