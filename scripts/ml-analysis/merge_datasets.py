import matplotlib.pyplot as plt
import os
import pandas as pd

import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge datasets")
    parser.add_argument(
        "--files", type=str, nargs="+", help=".tar.gz Files to merge", default=[])
    parser.add_argument(
        "--output", type=str, help="Output file", default="labeled_flows.csv")
    parser.add_argument(
        "--target_path", type=str, help="Output directory", default="MERGED-DS")    
    args = parser.parse_args()

    files = args.files
    target_path = args.target_path
    out_fname = args.output

    df_list = []
    # for each directory in the current directory
    # for root, dirs, files in os.walk("."):
    os.mkdir(".tmp")
    for f in files:
        # Print file names and paths
        print(f"{f}")
        # Get the file from the .tar.gz
        os.system(f"tar -C .tmp -xzvf {f} {out_fname}")

        # If it contains a file named
        fname = f".tmp/{out_fname}"
        if os.path.isfile(fname):
            df = pd.read_csv(fname, low_memory=False)
            df_list.append(df)
        else:
            print(f"File {fname} not found")
        
    os.system(f"rm -rf .tmp")
    print(df_list)
    

    os.makedirs(target_path, exist_ok=True)
    df = pd.concat(df_list, ignore_index=True)
    df.to_csv(f"{target_path}/{out_fname}", index=False)

    # Create a tar.gz from the output file
    # Ignore root
    os.system(f"tar -czvf {target_path}.tar.gz -C {target_path}/ .")
    # Remove the directory
    os.system(f"rm -rf {target_path}")
