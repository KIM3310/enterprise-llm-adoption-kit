FROM node:26-alpine

WORKDIR /app

COPY package.json /app/package.json
RUN npm install

COPY . /app

EXPOSE 5173
CMD ["npm", "run", "dev"]
