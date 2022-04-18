ARG VARIANT="focal"
FROM mcr.microsoft.com/vscode/devcontainers/base:0-${VARIANT}
USER root
WORKDIR /home/app/
RUN apt-get update
RUN apt-get -y install curl gnupg
RUN curl -sL https://deb.nodesource.com/setup_14.x  | bash -
RUN apt-get -y install nodejs
RUN npm install
RUN npm install -g truffle
RUN apt-get -y install inetutils-ping
RUN apt-get update && apt-get install -y vim
RUN npm install ping
COPY truffle /home/app/
# COPY contract /home/app/truffle_current/contracts