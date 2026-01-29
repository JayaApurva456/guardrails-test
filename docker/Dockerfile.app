FROM node:18-alpine

WORKDIR /app

COPY github-app/package*.json ./
RUN npm install

COPY github-app/ ./
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
