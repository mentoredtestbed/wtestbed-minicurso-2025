#!/bin/python

import pandas as pd
import numpy as np
import argparse
import yaml
import os
import json

def load_ip_data(directory, silent=False):
    '''
    Load the IP data from the csv file
    '''
    iname = 'net1'
    fname = 'MENTORED_IP_LIST.yaml'
    path = directory + '/' + fname
    if not os.path.exists(path):
        print(f"File {path} not found")
        return None
    
    with open(path, 'r') as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    
    for na in data:
        for i, replica in enumerate(data[na]):
            data[na][i] = [x for x in replica if x[2] == iname][0][0]
    result = {}

    # for each directory in the directory, check if it is in the IP list
    for root, dirs, files in os.walk(directory):
        for d in dirs:
            for na in data:
                if na in d:
                    result[d] = data[na]
    
    # Sort the replicas by the number and map according to the IP list order
    result_for_replicas = {}
    for na in data:
        na_replicas = sorted([x for x in result if na in x],
                                                 key=lambda x: int(x.split('_')[-2].split("-")[-1]))
        
        if len(na_replicas) != len(data[na]):
            n_containers = int(len(na_replicas)/len(data[na]))
            replica_ip_list = []
            for replica in data[na]:
                replica_ip_list += [replica]*n_containers
        else:
            replica_ip_list = data[na]

        for d, ip in zip(na_replicas, replica_ip_list):
            result_for_replicas[d] = ip
    
    return result_for_replicas

def unify_registry(directory, silent=False):
    '''
    Recursively find each MENTORED_REGISTRY.yaml file in the directory and unify them into a single yaml file
    '''

    result = {
        'registry': [], 'version': 0
    }

    # Read MENTORED_READY.txt file and get initial timestamp
    with open(directory+"/MENTORED_READY.txt", 'r') as file:
        ready_timestamp = float(file.read().strip())
    # na_ip = load_ip_data(directory, silent)

    for root, dirs, files in os.walk(directory):
        print(f"Reading {root}/{file}")
        for file in files:
            if file == 'MENTORED_REGISTRY.yaml':
                path = root+"/"+file
                with open(path, 'r') as stream:
                    try:
                        data = yaml.safe_load(stream)
                        for r in data['registry']:
                            r['nodeactor'] = path.replace(directory, "").split("/")[2]
                            # r['ip'] = na_ip[r['nodeactor']]
                            r['relative_timestamp_as_int'] = float(r['timestamp_as_int']) - ready_timestamp
                            r['relative_timestamp_as_float'] = float(r['timestamp_as_float']) - ready_timestamp
                        result['registry'] += data['registry']
                        result['version'] = max(result['version'], data['version'])
                        
                    except yaml.YAMLError as exc:
                        print(exc)

    # Fix nodeactor name
    for r in result['registry']:
        r['nodeactor'] = r['nodeactor'].split(".")[0]
        # Remove the last _* part (container name)
        r['nodeactor'] = "_".join(r['nodeactor'].split("_")[:-1])
        
    if not silent:
        print(json.dumps(result, indent=4))
    
    # Sort by date
    result['registry'] = sorted(result['registry'], key=lambda x: x['timestamp_as_float'])
    
    if result['registry']:
        with open(directory+"/UNIFIED_MENTORED_REGISTRY.yaml", 'w') as outfile:
            yaml.dump(result, outfile, default_flow_style=False)

    return None

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-d', '--dir', dest='dir', type=str,
                                            required=True)
    parser.add_argument('-s', dest='silent', action='store_true')

    parser.set_defaults(silent=False)
    
    args = parser.parse_args()

    unify_registry(args.dir, args.silent)

if __name__ == "__main__":
    main()