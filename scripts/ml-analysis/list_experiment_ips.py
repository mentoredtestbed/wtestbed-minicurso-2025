#!/bin/python

import pandas as pd
import numpy as np
import argparse
import yaml
import os

def load_ip_data(directory, iname='net1', silent=False):
    '''
    Load the IP data from the csv file
    '''
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

    ip_list = []
    for na in data:
        for i, replica in enumerate(data[na]):
            for na_ip, _, na_iname in replica:
                if na_iname == iname:
                    ip_list.append(na_ip)
                    break
    
    ip_list = sorted(list(set(ip_list)))

    return ip_list

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-d', '--dir', dest='dir', type=str,
                        required=True)
    parser.add_argument('-i', dest='iname', default='net1', type=str)
    parser.add_argument('-s', dest='silent', action='store_true')

    parser.set_defaults(silent=False)

    args = parser.parse_args()

    ip_list = load_ip_data(args.dir, args.iname, args.silent)

    print(" ".join(ip_list))

if __name__ == "__main__":
    main()