require("@nomiclabs/hardhat-waffle");
require("hardhat-gas-reporter");
require("@nomiclabs/hardhat-web3");

/**
 * @type import('hardhat/config').HardhatUserConfig
 */
module.exports = {
  defaultNetwork: "hardhat",
  networks: {
    hardhat: { /*
     forking: {
        url: 'TMP' // Put unique alchemy URL here
      }, */
      chainId: 1337
    } // Can also add ropsten, geth
  },
  solidity: {
    version: "0.8.0",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  gasReporter: {
    currency: 'USD',
    // gasPrice: 71,
    // outputFile: "./Experiments/Contract/hardhat/GasOutputJobCanceled",
    showTimeSpent: true,
    rst: true,
    noColors: true,
    onlyCalledMethods: true,
    // coinmarketcap: "", // Put unique coin market cap api here
  },
  paths: {
    sources: "./hardhat/contracts",
    tests: "./hardhat/test",
    cache: "./hardhat/cache",
    artifacts: "./hardhat/artifacts"
  },
  mocha: {
    timeout: 200000000000000000
  },
  namedAccounts: {
    deployer: 0
  }
};
