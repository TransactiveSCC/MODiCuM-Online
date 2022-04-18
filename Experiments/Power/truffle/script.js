const contract = artifacts.require("ModicumV2");

module.exports = async function(callback) {
    try {
        const accounts = await web3.eth.getAccounts();
        const customer = accounts[0];
        const allocator = accounts[1];
        const supplier = accounts[2];
        const mediator = accounts[3];
        web3.eth.personal.unlockAccount(accounts[0], "password", 36000)
        web3.eth.personal.unlockAccount(accounts[1], "password", 36000)
        web3.eth.personal.unlockAccount(accounts[2], "password", 36000)
        web3.eth.personal.unlockAccount(accounts[3], "password", 36000)

        console.log("Method: Constructor\tStart Time: " + Date.now())
        const instance = await contract.new({from: customer}).then((result) => {
                console.log("Deployment")
                //console.log(result);
                return result;
        })
        console.log("Method: Constructor\tEnd Time: " + Date.now())

        let tmp;

        tmp = await web3.eth.sendTransaction({to: allocator,from:accounts[0], value: web3.utils.toWei('1')}).then((result) => {
            console.log("Send transaction")
            console.log(result);
            return result;
        }).catch(err => {
            console.log('error', err);
        });
        tmp = await web3.eth.sendTransaction({to: supplier,from:accounts[0], value: web3.utils.toWei('1')}).then((result) => {
            console.log("Send transaction")
            console.log(result);
            return result;
        }).catch(err => {
            console.log('error', err);
        });
        tmp = await web3.eth.sendTransaction({to: mediator,from:accounts[0], value: web3.utils.toWei('1')}).then((result) => {
            console.log("Send transaction")
            console.log(result);
            return result;
        }).catch(err => {
            console.log('error', err);
        });

        const pause = () => {
            return new Promise(resolve => {
                setTimeout(() => resolve(), 100)
            })}
        const extendedPause = () => {
            return new Promise(resolve => {
                setTimeout(() => resolve(), 600000)
            })}

        let x;
        let total = 0;
        let endTime = Date.now() + 600000;
        
        console.log("Method: setup\tStart Time: " + Date.now())
        while(Date.now() < endTime) {
            x = await instance.setup(1, 1, 15, 0, 0, {from: accounts[0]}).then((result) => {
                console.log(result)
                return result
            }).catch(err => {
                console.log('error', err);
            })
            
            let y = x.receipt.blockNumber;

            let z = await web3.eth.getBlock(y).then((result) => {
                    return result
            }).catch(err => {
                console.log('error', err);
            });
            console.log(z)
            total++;
        }

        console.log("End Time: " + Date.now())
        console.log("Total setup functions called: " + total);

        total = 0;
        endTime = Date.now() + 600000;
        console.log("Method: createAllocation\tStart Time: " + Date.now())
        while(Date.now() < endTime) {
            x = await instance.createAllocation(1, customer, mediator, web3.utils.asciiToHex("a"), web3.utils.asciiToHex("hi"), {from: allocator}).then((result) => {
                console.log(result)
                return result
            }).catch(err => {
                console.log('error', err);
            });
            let y = x.receipt.blockNumber;

            let z = await web3.eth.getBlock(y).then((result) => {
                    return result
            }).catch(err => {
                console.log('error', err);
            });
            console.log(z)
            total++;
        }

        console.log("End Time: " + Date.now())
        console.log("Total createAllocation functions called: " + total);

        let j = 0;
        endTime = Date.now() + 600000;
        console.log("Method: addSupplier\tStart Time: " + Date.now())
        while(j < total && Date.now() < endTime) {
            x = await instance.addSupplier(j, supplier, web3.utils.asciiToHex("b"), true,{from: allocator}).then((result) => {
                console.log(result)
                j++
                return result
            }).catch(err => {
                console.log('error', err);
            });
            let y = x.receipt.blockNumber;

            let z = await web3.eth.getBlock(y).then((result) => {
                    return result
            }).catch(err => {
                console.log('error', err);
            });
            console.log(z)        
        }

        console.log("End Time: " + Date.now())
        console.log("Total addSupplier functions called: " + j);
        total = j;
        j = 0;
        endTime = Date.now() + 600000;
        console.log("Method: mediatorSign\tStart Time: " + Date.now())
        while(j < total && Date.now() < endTime) {
            x = await instance.mediatorSign(j, {from: mediator}).then((result) => {
                console.log(result)
                j++
                return result
            }).catch(err => {
                console.log('error', err);
            });
            
            let y = x.receipt.blockNumber;

            let z = await web3.eth.getBlock(y).then((result) => {
                return result
            }).catch(err => {
                console.log('error', err);
            });
                console.log(z)
        }

        console.log("End Time: " + Date.now())
        console.log("Total mediatorSign functions called: " + j);
        total = j;
        j = 0;
        endTime = Date.now() + 600000;
        console.log("Method: supplierSign\tStart Time: " + Date.now())
        while(j < total && Date.now() < endTime) {
            x = await instance.supplierSign(j, 0, {from: supplier, value: 1000}).then((result) => {
                console.log(result)
                j++
                return result
            }).catch(err => {
                console.log('error', err);
            });
            
            let y = x.receipt.blockNumber;

            let z = await web3.eth.getBlock(y).then((result) => {
                    return result
            }).catch(err => {
                console.log('error', err);
            });
                console.log(z)
        }

        console.log("End Time: " + Date.now())
        console.log("Total supplierSign functions called: " + j);
        total = j;
        j = 0;
        endTime = Date.now() + 600000;
        console.log("Method: customerSign\tStart Time: " + Date.now())
        while(j < total && Date.now() < endTime) {
            x = await instance.customerSign(j, {from: customer, value: 1000}).then((result) => {
                console.log(result)
                j++
                return result
            }).catch(err => {
                console.log('error', err);
            });
            
            let y = x.receipt.blockNumber;

            let z = await web3.eth.getBlock(y).then((result) => {
                    return result
            }).catch(err => {
                console.log('error', err);
            });
                console.log(z)
        }

        console.log("End Time: " + Date.now())
        console.log("Total customerSign functions called: " + j);
        total = j;
        j = 0;
        endTime = Date.now() + 600000;
        console.log("Method: postOutput\tStart Time: " + Date.now())
        while(j < total && Date.now() < endTime) {
            x = await instance.postOutput(j,0,web3.utils.asciiToHex("c"),{from:supplier}).then((result) => {
                console.log(result)
                j++
                return result
            }).catch(err => {
                console.log('error', err);
            });
            let y = x.receipt.blockNumber;

            let z = await web3.eth.getBlock(y).then((result) => {
                    return result
            }).catch(err => {
                console.log('error', err);
            });
            console.log(z)
        }

        console.log("End Time: " + Date.now())
        console.log("Total postOutput functions called: " + j);
        total = j;
        j = 0;
        endTime = Date.now() + 600000;
        console.log("Method: postMediation\tStart Time: " + Date.now())
        while(j < total && Date.now() < endTime) {
            x = await instance.postMediation(j, web3.utils.asciiToHex("a"), {from: mediator}).then((result) => {
                console.log(result)
                j++
                return result
            }).catch(err => {
                console.log('error', err);
            });
            let y = x.receipt.blockNumber;

            let z = await web3.eth.getBlock(y).then((result) => {
                    return result
            }).catch(err => {
                console.log('error', err);
            });
            console.log(z)
        }

        console.log("End Time: " + Date.now())
        console.log("Total postMediation functions called: " + j);
        total = j;
        j = 0;
        endTime = Date.now() + 600000;
        console.log("Method: clearMarket\tStart Time: " + Date.now())
        while(j < total && Date.now() < endTime) {
            x = await instance.clearMarket(j,{from: customer}).then((result) => {
                console.log(result)
                j++
                return result
            }).catch(err => {
                console.log('error', err);
            });
            let y = x.receipt.blockNumber;

            let z = await web3.eth.getBlock(y).then((result) => {
                    return result
            }).catch(err => {
                console.log('error', err);
            });
            console.log(z)
        }

        console.log("End Time: " + Date.now())
        console.log("Total clearMarket functions called: " + j);

        x = await extendedPause().then((result) => {
            console.log(result)
            return result
        }).catch(err => {
            console.log('error', err);
        });
        
        }
    catch(error) {
        console.log(error);
    }
    callback();
}