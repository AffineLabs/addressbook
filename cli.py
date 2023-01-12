from collections import defaultdict
from datetime import datetime

import fire
import json
import os
import requests

def time_now():
    datetime_now = datetime.utcnow()
    return datetime_now.strftime('%a, %d %b %Y %H:%M:%S GMT')

def safe_mkdir(dir):
    os.makedirs(dir, exist_ok=True)

def read_json(file_path):
    return json.load(open(file_path))

def write_json(dir, file_name, json_dict):
    with open(os.path.join(dir, file_name), "w") as outfile:
       json.dump(json_dict, outfile, indent = 2)

class CLI:
    def build_from_s3(self, version):
        # Read the s3 addressbook object
        s3_addressbook = requests.get(f'https://sc-abis.s3.us-east-2.amazonaws.com/{version}/addressbook.json').json()

        # Write the old format addressbook in version directory.
        version_dir = os.path.join(os.getcwd(), version)
        safe_mkdir(version_dir)
        write_json(version_dir, "addressbook.json", s3_addressbook)

        # Create new minified addressbook
        new_addressbook = defaultdict(lambda: defaultdict(None))
        for contract_name, contract in s3_addressbook.items():
            network_id = contract["network_id"]
            new_addressbook[network_id][contract_name] = {
                "address": contract["address"],
                "lastUpdated": contract["lastUpdated"],
                "contractType": contract["contractType"],
                "abiPath": f'{version}/{network_id}/{contract["contractType"]}.json'
            }
            network_dir = os.path.join(version_dir, str(network_id))
            safe_mkdir(network_dir)
            write_json(network_dir, f'{contract["contractType"]}.json', contract["abi"])
        write_json(version_dir, "addressbook.minified.json", new_addressbook)


    def patch_address(self, version, contract_name, new_address):
        time_now_gmt = time_now()
        version_dir = os.path.join(os.getcwd(), version)

        # Update legacy addressbook
        legacy_addressbook = read_json(os.path.join(version_dir, "addressbook.json"))
        if contract_name in legacy_addressbook:
            legacy_addressbook[contract_name]["address"] = new_address
            legacy_addressbook[contract_name]["lastUpdated"] = time_now_gmt
        write_json(version_dir, "addressbook.json", legacy_addressbook)

        # Update new addressbook
        new_addressbook = read_json(os.path.join(version_dir, "addressbook.minified.json"))
        for network_id, contracts in new_addressbook.items():
            if contract_name in contracts:
                contracts[contract_name]["address"] = new_address
                contracts[contract_name]["lastUpdated"] = time_now_gmt
        write_json(version_dir, "addressbook.minified.json", new_addressbook)

    def patch_abi(self, version, contract_type, contract_abi_repo_branch):
        new_abi = requests.get(f'https://raw.githubusercontent.com/AffineLabs/contracts/{contract_abi_repo_branch}/abi/{contract_type}.json').json()

        time_now_gmt = time_now()
        version_dir = os.path.join(os.getcwd(), version)

        # Update legacy addressbook
        legacy_addressbook = read_json(os.path.join(version_dir, "addressbook.json"))
        for contract_name, contract in legacy_addressbook.items():
            if contract["contractType"] == contract_type:
                contract["abi"] = new_abi
                contract["lastUpdated"] = time_now_gmt
        write_json(version_dir, "addressbook.json", legacy_addressbook)

        # Update new addressbook
        new_addressbook = read_json(os.path.join(version_dir, "addressbook.minified.json"))
        for network_id, contracts in new_addressbook.items():
            for contract_name in contracts.keys():
                if contracts[contract_name]["contractType"] == contract_type:
                    contracts[contract_name]["lastUpdated"] = time_now_gmt
                    # Update the ABI file
                    write_json(os.path.join(version_dir, network_id), f'{contract_type}.json', new_abi)
        write_json(version_dir, "addressbook.minified.json", new_addressbook)

    def new_contract(self, version, network_id, contract_name, contract_address, contract_type, contract_abi_repo_branch):
        abi = requests.get(f'https://raw.githubusercontent.com/AffineLabs/contracts/{contract_abi_repo_branch}/abi/{contract_type}.json').json()

        time_now_gmt = time_now()
        version_dir = os.path.join(os.getcwd(), version)
        network_mapping = {
            1: {
                "blockchain": "Ethereum",
                "deployment_net": "Mainnet",
            },
            137: {
                "blockchain": "Polygon",
                "deployment_net": "Mainnet",
            }
        }
        # Update legacy addressbook
        legacy_addressbook = read_json(os.path.join(version_dir, "addressbook.json"))
        legacy_addressbook[contract_name] = {
            "blockchain": network_mapping[network_id]["blockchain"],
            "deployment_net": network_mapping[network_id]["deployment_net"],
            "network_id": network_id,
            "address": contract_address,
            "lastUpdated": time_now_gmt,
            "contractType": contract_type,
            "abi": abi
        }
        write_json(version_dir, "addressbook.json", legacy_addressbook)

        # Update new addressbook
        new_addressbook = read_json(os.path.join(version_dir, "addressbook.minified.json"))
        new_addressbook[str(network_id)][contract_name] = {
            "address": contract_address,
            "lastUpdated": time_now_gmt,
            "contractType": contract_type,
            "abiPath": f'{version}/{network_id}/{contract_type}.json'
        }
        write_json(version_dir, "addressbook.minified.json", new_addressbook)

        # Update the ABI file
        write_json(os.path.join(version_dir, str(network_id)), f'{contract_type}.json', abi)
if __name__ == '__main__': 
    fire.Fire(CLI) 
