FROM ethereum/client-go:stable

COPY geth-config /geth-config
RUN geth account new --datadir /gethdata/.ethereum --password /geth-config/password.txt;
RUN geth account new --datadir /gethdata/.ethereum --password /geth-config/password.txt;
RUN geth account new --datadir /gethdata/.ethereum --password /geth-config/password.txt;
RUN geth account new --datadir /gethdata/.ethereum --password /geth-config/password.txt;
RUN geth --nousb --datadir /gethdata/.ethereum init /geth-config/genesis.json;

VOLUME /gethdata

EXPOSE 8545 8546 30303 30303/udp

ENTRYPOINT [ "geth", \
             "--datadir=/gethdata/.ethereum", \
             "--ethash.dagdir=/gethdata/.ethash", \
             "--http", "--http.addr=0.0.0.0", \
             "--http.api=eth,web3,net,personal", \
	         "--allow-insecure-unlock", \
             "--mine", "--miner.threads=1", \
             "--miner.etherbase=0", \
             "--miner.gastarget=2000000000", \
             "--rpc.gascap=10000000", \
             "--networkid=15", "--nousb", "--nodiscover", \
             "--password=/geth-config/password.txt --allow-insecure-unlock --unlock 0 console" ]


