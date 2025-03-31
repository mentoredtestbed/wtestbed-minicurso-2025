import pandas as pd
import numpy as np
import argparse
import time
import yaml
import json

def is_registry_label(registry):
    # return "attack" in registry["action_name"]
    return registry["action_name"].startswith("attack-")

def get_registry_pairs(registries):
    reg_names = [r["action_name"] for r in registries]
    pairs = []
    for i, reg1 in enumerate(registries):
        # if reg1["action_name"].startswith("end-"):
        if reg1["action_name"].startswith("attack-stop"):
            continue

        reg_name = reg1["action_name"]
        label_name = reg_name.split("attack-")[-1]
        target_reg = None
        for j, reg2 in enumerate(registries):
            reg2_name = reg2["action_name"]
            # if i != j and (reg_name in reg2_name) and reg2_name.startswith("stop-"):
            if i != j and (label_name in reg2_name) and reg2_name.startswith("attack-stop"):
                target_reg = reg2
                break

        pairs.append((reg1, target_reg))
    
    return pairs

def create_labeled_file(input_file, output_file, base_path='.', iname='net1', convert_ts_to_date=False):

    logs = ""

    # Open MENTORED_READY file
    with open(f"{base_path}/MENTORED_READY.txt", 'r') as file:
        lines = "\n".join(file.readlines())
        timestamp_offset = float(lines)
    
    # Open UNIFIED_MENTORED_REGISTRY file
    with open(f"{base_path}/UNIFIED_MENTORED_REGISTRY.yaml", 'r') as file:
        unified_registry = yaml.safe_load(file)

    # Open MENTORED_IP_LIST file
    with open(f"{base_path}/MENTORED_IP_LIST.yaml", 'r') as file:
        ip_list = yaml.safe_load(file)
    
    na2ip = {}
    for na in ip_list:
        for i, replica in enumerate(ip_list[na]):
            for na_ip, _, na_iname in replica:
                if na_iname == iname:
                    na2ip[f'{na}-{i}'] = na_ip
                    break
    
    df = pd.read_csv(input_file, low_memory=False)

    # Drop times before 2000-01-01 (invalid timestamps)
    year2020 = time.strptime('2000-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    df = df[df['StartTime'] > time.mktime(year2020)]
    # df = df[df['StartTime'] < time.time()-24*60*60]

    time_cols = ['StartTime', 'LastTime', 'SrcStartTime', 'DstStartTime', 'SrcLastTime', 'DstLastTime']

    # Add label column with default value 'Normal'
    df['Label'] = 'Normal'

    for na, na_ip in na2ip.items():
        na_registries = [r for r in unified_registry["registry"] if r["nodeactor"] == na]
        na_registries = [r for r in na_registries if is_registry_label(r)]
        for pairs in get_registry_pairs(na_registries):
            ts1 = pairs[0]["timestamp_as_float"]

            # If there is no stop- action, use the current timestamp (action never ended)
            ts2 = pairs[1]["timestamp_as_float"] if pairs[1] is not None else time.time()
            msg = f'Trying to label {na} from {ts1} to {ts2} as {pairs[0]["action_name"]}...'
            print(msg, end=' ')
            logs += f'\n{msg}'
            mask = (df['StartTime'] > ts1) & (df['StartTime'] < ts2 ) & (df['SrcAddr'] == na_ip)
            msg = f'Found {mask.sum()} entries'
            print(msg)
            logs += f'\n{msg}'

            df.loc[mask, 'Label'] = pairs[0]["action_name"]


    print("Label distribution:")
    logs += "\nLabel distribution:"
    print(df['Label'].value_counts())
    logs += f"\n{df['Label'].value_counts()}"

    # Convert int to date
    if convert_ts_to_date:
        for col in time_cols:
            min_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(df[col].min()))
            max_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(df[col].max()))
            df[col] = df[col].apply(lambda x: time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x)))

    df.to_csv(output_file, index=False)

    return logs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, required=True)
    parser.add_argument('--output', type=str, required=True)
    parser.add_argument('--iname', type=str, default='net1')
    parser.add_argument('--convert_ts_to_date', action='store_true')
    
    args = parser.parse_args()
    create_labeled_file(args.input, args.output, args.iname, args.convert_ts_to_date)

if __name__ == '__main__':
    main()