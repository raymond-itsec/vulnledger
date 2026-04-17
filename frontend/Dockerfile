FROM node:22.22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 5173

ARG FINDINGS_RUNTIME_MODE=prod
ENV FINDINGS_RUNTIME_MODE=${FINDINGS_RUNTIME_MODE}

CMD ["/bin/sh", "-c", "if [ \"$FINDINGS_RUNTIME_MODE\" = \"dev\" ]; then exec npm run dev -- --host 0.0.0.0 --port 5173; else exec npm run preview -- --host 0.0.0.0 --port 5173; fi"]
