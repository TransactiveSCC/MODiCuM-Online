# Results

# Table of contents
- [Table of contents](#table-of-contents)
- [Gas Experiment Results](#gas-experiment-results)
- [Power Experiment Results](#power-experiment-results)
- [ End-to-end Execution Result files](#end-to-end-execution-result-files)

# Gas Experiment Results
* Results/Gas
  * GasOutputJobCanceled
    * npx hardhat test with the "Early Refund Run" tests
  * GasOutputJobRefunded
    * npx hardhat test with the "Signing Refund Run" tests
  * GasOutputMediation
    * npx hardhat test with the "Run with Mediation" tests
  * GasOutputNoMediation
    * npx hardhat test with the "Run without Mediation" tests

# Power Experiment Results
* Results/Power/process-truffle
  * /.vscode
    * tasks.json
        * Used to build a main.exe file that will process the truffle.log file in Input and paste the results in Output
    * settings.json
        * All imported libraries
  * /Input
    * The directory for the truffle.log file
  * /Output
    * The directory for the truffleProcessed.txt file
    * This file may need some manual processing to remove unwanted text characters
  * /src
    * main.cpp
        * Creates output file and a TruffleReader object
    * Reader.h
        * A parent class with common functions and variables
  * /truffle
    * TruffleReader.cpp/.h
        * Processes a file looking for the method name, the start time, the block number, and the block difficulty
* Results/Power/processed
  * Contains the processed truffle file for the power consumption experiment
* Results/Power/raw
  * Contains the raw miner, truffle, and watts files
    * watts.txt
        * Contains the data for the power consumption for the function call intervals and idle geth node
    * idle-machine.txt
        * Contains the data for the power consumption of the idle PC

# End-to-end Execution Result files

The CSV files with the aggregated results for the end-to-end experiments
are in `Results/End-to-end`.

* `Results/End-to-end/influx`: contains the experiment results for scenarios S1-S6
as outlined in Section 5.2 of the paper. The scenario parameters for each of the
CSVs is as follows.
  * simone.csv: 10 customers and 10 ideal suppliers
  * simtwo.csv: 20 customers and 10 ideal suppliers
  * simthree.csv: 20 customers and 20 ideal suppliers
  * simfour.csv: 10 customers and 10 sporadic suppliers
  * simfive.csv: 20 customers and 10 sporadic suppliers
  * simsix.csv: 20 customers and 20 sporadic suppliers
* `Results/End-to-end/resource`: contains the resource metrics presented in figures
10 and 11 in the paper. 
  * cpu.csv: the CPU utilization for all 6 scenarios
  * memory.csv: the memory utilization for all 6 scenarios

