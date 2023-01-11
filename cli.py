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

if __name__ == '__main__': 
    fire.Fire(CLI) 
