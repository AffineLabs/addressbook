# AffineLabs Addressbook
 
This repository contains a collection of static files that provide information about the deployed contract addresses 
and application binary interfaces (ABIs) of the Affine protocol.

## CLI

The CLI is equipped with helper functions to either generate addressbook static files from s3 or patching existing addressbook

### Commands
__Build addressbook for specific version__
```
python3 cli.py build_from_s3 --version=v1.0-beta
```

__Patch a contract address__
```
python3 cli.py patch_address --version=v1.0-beta --contract_name=EthAlpSave --new_address='"0x7C9414Ad01Db4C50F8fa8C233ff6869284FFF648"'
```

__Patch a contract ABI__
```
python3 cli.py patch_abi --version=v1.0-beta --contract_type=L2Vault --contract_abi_repo_branch=master
```

__Add a new contract to addressbook__
```
python3 cli.py new_contract --version=v1.0-beta --network_id=1 --contract_name=EthEntryVault --contract_address='"0x7C9414Ad01Db4C50F8fa8C233ff6869284FFF648"' --contract_type=Vault --contract_abi_repo_branch=master
```
