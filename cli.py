import datetime
import fire
import json
import os
import requests

def time_now():
    datetime_now = datetime.datetime.now(datetime.timezone.utc)
    return datetime_now.strftime('%a, %d %b %Y %H:%M:%S GMT')

def safe_mkdir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def read_json(file_path):
    f = open(file_path)
    return json.load(f)

def write_json(dir, file_name, json_object):
    f = os.path.join(dir, file_name)
    with open(f, "w") as outfile:
        outfile.write(json_object)

class CLI:
    def build_from_s3(self, version):
        # Read the s3 addressbook object
        s3_addressbook_url = f'https://sc-abis.s3.us-east-2.amazonaws.com/{version}/addressbook.json'
        s3_addressbook_response = requests.get(s3_addressbook_url)
        s3_addressbook = s3_addressbook_response.json()
        contracts = s3_addressbook.keys()

        # Write the old format addressbook in version directory.
        root_dir = os.getcwd()
        version_dir = os.path.join(root_dir, version)
        safe_mkdir(version_dir)
        write_json(version_dir, "addressbook.json", str(s3_addressbook_response.content, 'utf-8'))

        # Create new minified addressbook
        new_addressbook = {}
        for contract_name in contracts:
            contract = s3_addressbook[contract_name]
            network_id = contract["network_id"]
            if not network_id in new_addressbook:
                new_addressbook[network_id] = {}
            new_addressbook[network_id][contract_name] = {
                "address": contract["address"],
                "lastUpdated": contract["lastUpdated"],
                "contractType": contract["contractType"],
                "abiPath": f'{version}/{network_id}/{contract["contractType"]}.json'
            }
            network_dir = os.path.join(version_dir, str(network_id))
            safe_mkdir(network_dir)
            write_json(network_dir, f'{contract["contractType"]}.json', json.dumps(contract["abi"], indent = 2))


        new_addressbook_dump = json.dumps(new_addressbook, indent = 2)
        write_json(version_dir, "addressbook.minified.json", new_addressbook_dump)


    def patch_address(self, version, contract_name, new_address):
        time_now_gmt = time_now()
        root_dir = os.getcwd()
        version_dir = os.path.join(root_dir, version)

        # Update legacy addressbook
        legacy_addressbook_path = os.path.join(version_dir, "addressbook.json")
        legacy_addressbook = read_json(legacy_addressbook_path)
        if contract_name in legacy_addressbook:
            legacy_addressbook[contract_name]["address"] = new_address
            legacy_addressbook[contract_name]["lastUpdated"] = time_now_gmt
        legacy_addressbook_dump = json.dumps(legacy_addressbook, indent = 2)
        write_json(version_dir, "addressbook.json", legacy_addressbook_dump)

        # Update new addressbook
        new_addressbook_path = os.path.join(version_dir, "addressbook.minified.json")
        new_addressbook = read_json(new_addressbook_path)
        for network_id in new_addressbook.keys():
            if contract_name in new_addressbook[network_id]:
                new_addressbook[network_id][contract_name]["address"] = new_address
                new_addressbook[network_id][contract_name]["lastUpdated"] = time_now_gmt
        new_addressbook_dump = json.dumps(new_addressbook, indent = 2)
        write_json(version_dir, "addressbook.minified.json", new_addressbook_dump)

    def patch_abi(self, version, contract_type, contract_abi_repo_branch):
        new_abi_address = f'https://raw.githubusercontent.com/AffineLabs/contracts/{contract_abi_repo_branch}/abi/{contract_type}.json'
        new_abi = requests.get(new_abi_address)

        time_now_gmt = time_now()
        root_dir = os.getcwd()
        version_dir = os.path.join(root_dir, version)

        # Update legacy addressbook
        legacy_addressbook_path = os.path.join(version_dir, "addressbook.json")
        legacy_addressbook = read_json(legacy_addressbook_path)
        for contract_name in legacy_addressbook.keys():
            if legacy_addressbook[contract_name]["contractType"] == contract_type:
                legacy_addressbook[contract_name]["abi"] = new_abi.json()
                legacy_addressbook[contract_name]["lastUpdated"] = time_now_gmt
        legacy_addressbook_dump = json.dumps(legacy_addressbook, indent = 2)
        write_json(version_dir, "addressbook.json", legacy_addressbook_dump)

        # Update new addressbook
        new_addressbook_path = os.path.join(version_dir, "addressbook.minified.json")
        new_addressbook = read_json(new_addressbook_path)
        for network_id in new_addressbook.keys():
            for contract_name in legacy_addressbook[network_id].keys():
                if legacy_addressbook[network_id][contract_name]["contractType"] == contract_type:
                    new_addressbook[network_id][contract_name]["lastUpdated"] = time_now_gmt
                    # Update the ABI file
                    write_json(os.path.join(version_dir, network_id), f'{contract_type}.json', str(new_abi.content, 'utf-8'))
        new_addressbook_dump = json.dumps(new_addressbook, indent = 2)
        write_json(version_dir, "addressbook.minified.json", new_addressbook_dump)

    def new_contract(self, version, network_id, contract_name, contract_address, contract_type, contract_abi_repo_branch):
        abi_address = f'https://raw.githubusercontent.com/AffineLabs/contracts/{contract_abi_repo_branch}/abi/{contract_type}.json'
        abi = requests.get(abi_address)

        time_now_gmt = time_now()
        root_dir = os.getcwd()
        version_dir = os.path.join(root_dir, version)
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
        legacy_addressbook_path = os.path.join(version_dir, "addressbook.json")
        legacy_addressbook = read_json(legacy_addressbook_path)
        legacy_addressbook[contract_name] = {
            "blockchain": network_mapping[network_id]["blockchain"],
            "deployment_net": network_mapping[network_id]["deployment_net"],
            "network_id": network_id,
            "address": contract_address,
            "lastUpdated": time_now_gmt,
            "contractType": contract_type,
            "abi": abi.json()
        }
        legacy_addressbook_dump = json.dumps(legacy_addressbook, indent = 2)
        write_json(version_dir, "addressbook.json", legacy_addressbook_dump)

        # Update new addressbook
        new_addressbook_path = os.path.join(version_dir, "addressbook.minified.json")
        new_addressbook = read_json(new_addressbook_path)
        new_addressbook[str(network_id)][contract_name] = {
            "address": contract_address,
            "lastUpdated": time_now_gmt,
            "contractType": contract_type,
            "abiPath": f'{version}/{network_id}/{contract_type}.json'
        }
        new_addressbook_dump = json.dumps(new_addressbook, indent = 2)
        write_json(version_dir, "addressbook.minified.json", new_addressbook_dump)

        # Update the ABI file
        write_json(os.path.join(version_dir, str(network_id)), f'{contract_type}.json', str(abi.content, 'utf-8'))
if __name__ == '__main__': 
    fire.Fire(CLI) 
