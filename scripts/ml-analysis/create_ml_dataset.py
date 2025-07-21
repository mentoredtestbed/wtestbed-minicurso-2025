from list_experiment_ips import load_ip_data

import subprocess
import os
import time
from pathlib import Path
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

def run_command(command):
    """Runs a shell command and returns its output."""
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result

def create_csv(input_pcap, output_csv, limit_attempts=1, verbose=0):
    logs = ""
    """Creates a CSV file from a PCAP file using argus and ra commands."""

    # Measure the size of pcap
    if verbose > 1:
        pcap_size = os.path.getsize(input_pcap)
        print(f"PCAP size for {input_pcap}: {pcap_size/1024/1024:.2f} MB")
        print(f"Size in bytes: {pcap_size}")
        logs += f"PCAP size for {input_pcap}: {pcap_size/1024/1024:.2f} MB"
        logs += f"Size in bytes: {pcap_size}"

    max_attempts = limit_attempts

    # timestamp + input_pcap hash
    unique_name = f"{int(time.time())}_{hash(input_pcap)}"
    
    while max_attempts > 0:
        # run_command(f"argus -F argus.conf -r {input_pcap} -w .flows_tmp.argus")
        run_command(f"argus -r {input_pcap} -w .{unique_name}.argus")
        result = run_command(f"ra -n -c , -M dsrs=-fuser,-duser -r .{unique_name}.argus -u -s srcid,stime,ltime,sstime,dstime,sltime,dltime,saddr,daddr,sport,dport,trans,seq,flgs,dur,avgdur,stddev,mindur,maxdur,proto,stos,dtos,sdsb,ddsb,sco,dco,sttl,dttl,sipid,dipid,smpls,dmpls,svlan,dvlan,svid,dvid,svpri,dvpri,spkts,dpkts,sbytes,dbytes,sappbytes,dappbytes,sload,dload,sloss,dloss,sploss,dploss,srate,drate,smac,dmac,dir,sintpkt,dintpkt,sit,dit,state,suser,duser,swin,dwin,trans,srng,erng,stcpb,dtcpb,tcprtt,inode,offset,smaxsz,dmaxsz,sminsz,dminsz > {output_csv}")
        # result = run_command(f"ra -T 6 -c , -M dsrs=-fuser,-duser -r .flows_tmp.argus -u -s srcid,stime,ltime,sstime,dstime,sltime,dltime,saddr,daddr,sport,dport,trans,seq,flgs,dur,avgdur,stddev,mindur,maxdur,proto,stos,dtos,sdsb,ddsb,sco,dco,sttl,dttl,sipid,dipid,smpls,dmpls,svlan,dvlan,svid,dvid,svpri,dvpri,spkts,dpkts,sbytes,dbytes,sappbytes,dappbytes,sload,dload,sloss,dloss,sploss,dploss,srate,drate,smac,dmac,dir,sintpkt,dintpkt,sit,dit,state,suser,duser,swin,dwin,trans,srng,erng,stcpb,dtcpb,tcprtt,inode,offset,smaxsz,dmaxsz,sminsz,dminsz > {output_csv}")

        if result.returncode == 0:
            if verbose > 0:
                msg = f"CSV created successfully: {output_csv}"
                print(msg)
                logs += f'\n{msg}'
            break
        else:
            if verbose > 0:
                msg = f"Warning: ra command failed for {input_pcap}"
                print(msg)
                logs += f'\n{msg}'

            if max_attempts > 1:
                if verbose > 0:
                    msg = f"Retrying in 1 second..."
                    print(msg)
                    logs += f'\n{msg}'
                time.sleep(1)

        max_attempts -= 1

    if max_attempts == 0:
        msg = f"Error: ra command failed for {input_pcap}"
        print(msg)
        logs += f'\n{msg}'
    
    if os.path.exists(f".{unique_name}.argus"):
        os.remove(f".{unique_name}.argus")

    return logs

def create_argus_flows_csv(experiment_path, output_csv, input_pcap=None, use_arp=False):
    """Main function to process the PCAP file and create the final merged CSV."""
    # Get IP list from external script
    ip_list = load_ip_data(experiment_path)

    logs = ""

    if input_pcap is None:
        # Recursely find PCAP files in the experiment path
        pcap_files = list(Path(experiment_path).rglob("*.pcap")) + list(Path(experiment_path).rglob("*.pcapng"))
        if len(pcap_files) == 0:
            msg = f"Error: No PCAP files found in {experiment_path}"
            print(msg)
            logs += f'\n{msg}'
            return ""
        elif len(pcap_files) > 1:
            # msg = f"Warning: Multiple PCAP files found in {experiment_path} ({len(pcap_files)}). Using the largest one."
            # print(msg)
            # logs += f'\n{msg}'
            # pcap_sizes = [(file, os.path.getsize(file)) for file in pcap_files]
            # input_pcap = max(pcap_sizes, key=lambda x: x[1])[0]


            msg = f"Warning: Multiple PCAP files found in {experiment_path} ({len(pcap_files)}). Merging them."
            # Merge pcaps
            input_pcap = "tmp_merged_pcap.pcapng"
            merge_command = f"mergecap -w {input_pcap} {' '.join(str(file) for file in pcap_files)}"
            result = run_command(merge_command)
            if result.returncode != 0:
                msg = f"Error: Merging PCAP files failed for {experiment_path}"
                print(msg)
                # Print traceback
                print(result.stdout)
                print(result.stderr)
                logs += f'\n{msg}'
                return ""
        else:
            input_pcap = str(pcap_files[0])

        

    # If not using ARP, remove ARP packets from the PCAP
    if not use_arp:
        if input_pcap.endswith(".pcapng"):
            converted_pcap = input_pcap.replace(".pcapng", ".pcap")
            result = run_command(f"editcap {input_pcap} {converted_pcap}")
            if result.returncode != 0:
                msg = f"Error: Failed to convert {input_pcap} to {converted_pcap}"
                print(msg)
                print(result.stdout)
                print(result.stderr)
                logs += f"\n{msg}"
                return ""
            input_pcap = converted_pcap

        # Remove ARP packets
        result = run_command(f"tcpdump -r {input_pcap} -w tmp_no_arp_pcap -n not arp")
        if result.returncode != 0:
            msg = f"Error: Removing ARP packets failed for {input_pcap}"
            print(msg)
            print(result.stdout)
            print(result.stderr)
            logs += f'\n{msg}'
            return ""

        os.remove(input_pcap)
        input_pcap = "tmp_no_arp_pcap"
        print(f"[WARN] use_arp=False: Ignoring ARP packets in {input_pcap}")

    # Split PCAP by source IP
    def split_pcap_by_ip(ip):
        msg = f"Splitting {input_pcap} based on {ip}"
        print(msg)
        logs = f'\n{msg}'
        result = run_command(f"tcpdump -r {input_pcap} -w ./tmp_splited_pcap_{ip}.pcap -n \"src {ip}\"")
        if result.returncode != 0:
            msg = f"Error: Splitting failed for {ip}"
            print(msg)
            logs += f'\n{msg}'
            logs += f'\n{result.stdout}'
            logs += f'\n{result.stderr}'
        return logs

    with ThreadPoolExecutor() as executor:
        results = executor.map(split_pcap_by_ip, ip_list)

    for result in results:
        logs += result
        

    # Remove existing split CSV files
    for file in Path(".").glob("tmp_splited_pcap*.csv"):
        file.unlink()
    for file in Path(".").glob("pcap_segment*."):
        file.unlink()

    # Create CSVs from split PCAPs
    splited_pcap_list = list(Path(".").glob("tmp_splited_pcap*"))
    total_files = len(splited_pcap_list)

    for current_file, splited_pcap in enumerate(splited_pcap_list, start=1):
        # Split the current pcap in several segments of 10 seconds each
        split_command = f"editcap -i 10 '{splited_pcap}' 'pcap_segment_{splited_pcap}'"
        result = run_command(split_command)
        if result.returncode != 0:
            msg = f"Error: Splitting {splited_pcap} into segments failed"
            print(msg)
            logs += f'\n{msg}'
            continue
        
        fbasename = str(splited_pcap).replace('.pcap', '')
        segment_files = list(Path(".").glob(f"pcap_segment_{fbasename}_*.pcap"))
        print(f"Splited {splited_pcap} into {len(segment_files)} segments: {segment_files}")

        def process_segment(segment_file):
            return create_csv(str(segment_file), f"{segment_file}.csv")
        
        with ThreadPoolExecutor() as executor:
            results = executor.map(process_segment, segment_files)

        for result in results:
            logs += result
        

        
        print(f"Progress: {current_file}/{total_files}")

        # create_csv(str(splited_pcap), f"{splited_pcap}.csv")
        # print(f"Progress: {current_file}/{total_files}\r")

    # Merge CSVs
    csv_list = list(Path(".").glob("*tmp_splited_pcap*.csv"))
    df_list = []
    with open(output_csv, "w") as merged_csv:
        header_written = False
        for csv_file in csv_list:
            # with open(csv_file, "r") as f:
            #     lines = f.readlines()
            #     if not header_written:
            #         merged_csv.write(lines[0])  # Write header from the first file
            #         header_written = True
            #     merged_csv.writelines(lines[1:])  # Write remaining lines
            df = pd.read_csv(csv_file, encoding="ISO-8859-1", on_bad_lines='skip')
            print(f"Merging {csv_file} (Adding {len(df)} flows)")
            df_list.append(df)

        if df_list:
            df = pd.concat(df_list, ignore_index=True)
            df.to_csv(output_csv, index=False)
            msg = f"Merged {len(df_list)} CSV files into {output_csv}"
            print(msg)
            logs += f'\n{msg}'
        else:
            msg = f"No CSV files to merge."
            print(msg)
            logs += f'\n{msg}'

    # Clean up temporary files
    for file in Path(".").glob("tmp_splited_pcap*"):
        file.unlink()
    
    for file in Path(".").glob("pcap_segment*"):
        file.unlink()

    if input_pcap == "tmp_no_arp_pcap":
        os.remove("tmp_no_arp_pcap")
    if input_pcap == "tmp_merged_pcap.pcapng":
        os.remove("tmp_merged_pcap.pcapng")
    
    return logs
