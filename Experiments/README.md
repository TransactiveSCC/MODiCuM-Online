# Experiments

# Table of contents
- [Table of contents](#table-of-contents)
- [Gas Experiment](#gas-experiment)
- [Gas Experiment Files](#gas-experiment-files)
- [Power Experiment](#power-experiment)
- [Power Experiment Files](#power-experiment-files)
- [ End-to-end Execution Experiments](#end-to-end-execution-experiments)


# Gas Experiment
* To find the average gas prices on hardhat's local network, run the following from the main directory: npm install
* Then from the Experiments/Contract directory, run: npx hardhat test<br>
* There are three separate tests: one for a run with mediation, one without mediation, and one with the job canceled </br>
* The gas prices should appear in the terminal<br>
* Currently, 200 runs are done<br>
* To increase the number of runs, go to ha dhat.config.js and modify the number of runs under the solidity optimizer tab<br>

# Gas Experiment Files

* Experiments/Gas
  * hardhat.config.js:
    * Configures the network and the gasReporter plugin parameters
    * Sets the paths for the contracts, testing, cache, and artifacts
* Experiments/Gas/hardhat/contracts
  * ModicumV2.sol:
    * A slightly modified version of the MV2.sol contract that is deployed when using hardhat
    * Compared to the main contract, this contract has a few functions with removed timestamps
    * and the hash function is public.
* Experiments/Gas/hardhat/test
  * unit.js
    * Contains 4 different sets of unit tests to simulate basic runs:
      * A run with no mediation, a run with mediation, an early cancellation run, and a refunded run
    * This file is executed upon using the command npx hardhat test

# Power Experiment

* cd to the Experiments/Power folder
* Run docker-compose build and docker-compose up --no-color |& tee -a miner.log
* Open a new tab, cd to the Experiments/Power folder and run: docker exec -it truffle-suite bash | tee -a truffle.log
* Inside truffle, ping geth to get the IP
* vim truffle-config.js. Change the IP to that of the geth container
* Save and exit, and then run: truffle console
* Enter the following into the terminal:
  web3.eth.personal.unlockAccount(accounts[0], "password", 36000) </br>
  web3.eth.personal.unlockAccount(accounts[1], "password", 36000) </br>
  web3.eth.personal.unlockAccount(accounts[2], "password", 36000) </br>
  web3.eth.personal.unlockAccount(accounts[3], "password", 36000) </br>
* Then run: truffle exec script.js
* Wait for the script to finish, and then move the truffle.log file into the Input folder of Results/Power
* Edit the path directories, build, and run the code to get the timestamps of the function intervals
* The processed results should appear in the Results/Contract/process-truffle/Output folder

# Power Experiment Files

* Experiments/Power
  * docker-compose.yml
    * Creates a docker container for a geth node and a container with truffle installed
  * geth.Dockerfile
    * The dockerfile to create and mine on the geth node
  * truffle.Dockerfile
    * The dockerfile to create the truffle container
* Experiments/Power/geth-config
  * genesis.json
    * Parameterizes the geth node
  * genesis.json-accounts
    * Parameterizes the users in the geth node
  * passwords.txt
    * Contains the passwords for each respective user
* Experiments/Power/truffle
  * script.js
    * The script launched when using the command truffle exec script.js
    * It calls each function for a given interval and prints the initial timestamp and the ending timestamp for each function
  * truffle-config.js
    * Configures the truffle settings and allows truffle to connect to and use the private geth chain
* Experiments/Power/truffle
  * Migrations.sol
    * Used to track all contracts deployed onto the geth network following its own deployment
  * MV2.sol
    * The final MV2 smart contract, whose functions are called by script.js
* Experiments/Power/migrations
  * 1_initial_migration.js
    * Deploys Migrations.sol onto the private geth chain
  * 2_deploy_contracts.js
    * Deploys MV2.sol onto the private geth chain

# End-to-end Execution Experiments

This is related to the end-to-end execution experiments in Section 5.2 of the paper. 
All experiments were run on Google Cloud GKE. First follow the setup instructions
in `Demo/RM-GKE.md` to configure GKE and influx, and get the pulsar and market clusters running.
The instructions to run an experiment are as follows:

1. `make delete` Deletes any running experiments
2. delete any files in `Demo/deployments`
3. Delete data from influx database. If influx is running on google
cloud the url may look like this: `https://us-central1-1.gcp.cloud2.influxdata.com/` 
4. increment market version (`VERSION`) in `Demo/run/cfg.py`
5. delete repository `https://console.cloud.google.com/artifacts`. 
6. delete local images - `docker system prune -a`
7. `make artifact-repo-gcr`
8. `make build-gcr`
9. `make push-gcr`
10. `make convert-gcr`
11. Change number of customers and suppliers in `Demo/deployments`.
12. `make deploy-gcr` Starts the experiment.
13. `make check` Check status

To retrieve results for the experiment first export the metrics from BigQuery.
Then use `Demo/demo_results/results.ipynb` to retrieve the messages stored in
influx and process the results.

Additionally see `Demo/RM-STANDALONE.md` for instructions on running experiments locally
rather than using GKE.


