#!/usr/bin/env python3
import pandas as pd
import argparse
import os
import sys
import logging
import tarfile
import shutil
from tqdm import tqdm

MENTORED_READY=None
ATTACK_START=None
ATTACK_END=None
logger = logging.getLogger()
temp_dir = ".tmp_exp_analyzer"

def extract_experiment_data(expfile, temp_dir):
    """
    Extracts the MQTT-related CSV files from a tar.gz experiment file.
    """
    os.makedirs(temp_dir, exist_ok=True)
    logger.debug(f"Extracting {expfile} into {temp_dir}")
    with tarfile.open(expfile, "r:gz") as tar:
        tar.extractall(temp_dir, members=(m for m in tar if "mqtt" in m.name))
    logger.debug(f"Contents of {temp_dir}: {os.listdir(temp_dir)}")
    with tarfile.open(expfile, "r:gz") as tar:
        for member in tar.getmembers():
            if "MENTORED_READY.txt" in member.name:
                f = tar.extractfile(member)
                content = f.read()
                logger.debug(f"MENTORED_READY.txt content: {content}")
                # Convert content from unix timestamp to datetime
                global MENTORED_READY
                MENTORED_READY = pd.to_datetime(int(content), unit="s")
                break
    for root, _, files in os.walk(temp_dir):
        for file in files:
            if file.endswith(".tar"):
                tar_path = os.path.join(root, file)
                with tarfile.open(tar_path, "r") as tar:
                    tar.extractall()
                
                mqtt_client = "app/results/mqtt_client.csv"
                if os.path.exists(mqtt_client):
                    new_csv_name = f"{tar_path}.csv"
                    os.rename(mqtt_client, new_csv_name)
                
                # Clean up the extracted app directory
                if os.path.exists("app"):
                    shutil.rmtree("app")

def cleanup_experiment_data(temp_dir):
    """
    Cleans up the temporary directory used for extraction.
    """
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

def find_csv_files(directory, node):
    """
    Finds publisher and subscriber CSV files in the extracted data.
    """
    publisher_csv = None
    subscriber_csvs = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".csv"):
                file_path = os.path.join(root, file)
                if f"mqtt-pub-node-{node}" in file:
                    publisher_csv = file_path
                elif f"mqtt-sub-node-{node}" in file:
                    subscriber_csvs.append(file_path)

    if not publisher_csv:
        logger.error("Publisher CSV file not found!")
    if not subscriber_csvs:
        logger.error("No subscriber CSV files found!")

    return publisher_csv, subscriber_csvs

def load_csv(file_path):
    """
    Loads a CSV file into a DataFrame.
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        return None

def cross_reference_logs(publisher_csv, subscriber_csvs, attack_start, post_attack):
    """
    Compares publisher messages against multiple subscriber messages to identify dropped messages
    and calculate average delays.
    """
    publisher_df = load_csv(publisher_csv)
    if publisher_df is None:
        logger.error(f"Failed to load publisher CSV: {publisher_csv}")
        return

    # Filter only published messages
    publisher_df = publisher_df[publisher_df['action'] == 'published']
    publisher_df["time"] = pd.to_datetime(publisher_df["time"], unit="s")
    publisher_df["message"] = publisher_df["message"].astype(str)

    logger.debug(f"Publisher logged {len(publisher_df)} messages.")
    
    total_dropped_stats = {"pre_attack": 0, "during_attack": 0, "post_attack": 0}
    total_delay_stats = {"pre_attack": [], "during_attack": [], "post_attack": []}

    for subscriber_csv in subscriber_csvs:
        subscriber_df = load_csv(subscriber_csv)
        if subscriber_df is None:
            logger.warning(f"Skipping subscriber CSV: {subscriber_csv}")
            continue

        # Filter only received messages
        subscriber_df = subscriber_df[subscriber_df['action'] == 'received']
        subscriber_df["time"] = pd.to_datetime(subscriber_df["time"], unit="s")
        subscriber_df["message"] = subscriber_df["message"].astype(str)

        # Merge DataFrames on message
        merged_df = pd.merge(publisher_df, subscriber_df, on="message", how="left", suffixes=("_pub", "_sub"))

        # Calculate delay and exclude invalid values
        merged_df["delay"] = (merged_df["time_sub"] - merged_df["time_pub"]).dt.total_seconds()
        valid_delay_df = merged_df[~merged_df["delay"].isna() & (merged_df["delay"] >= 0)]

        # Determine attack timelines
        pre_attack = valid_delay_df[valid_delay_df["time_pub"] < ATTACK_START]
        during_attack = valid_delay_df[
            (valid_delay_df["time_pub"] >= ATTACK_START) & (valid_delay_df["time_pub"] <= ATTACK_END)
        ]
        post_attack = valid_delay_df[valid_delay_df["time_pub"] > ATTACK_END]

        # Collect delays
        total_delay_stats["pre_attack"].extend(pre_attack["delay"])
        total_delay_stats["during_attack"].extend(during_attack["delay"])
        total_delay_stats["post_attack"].extend(post_attack["delay"])

        # Identify dropped messages
        dropped_df = merged_df[merged_df["time_sub"].isna()]
        dropped_pre_attack = dropped_df[dropped_df["time_pub"] < ATTACK_START]
        dropped_during_attack = dropped_df[
            (dropped_df["time_pub"] >= ATTACK_START) & (dropped_df["time_pub"] <= ATTACK_END)
        ]
        dropped_post_attack = dropped_df[dropped_df["time_pub"] > ATTACK_END]

        # Update dropped stats
        total_dropped_stats["pre_attack"] += len(dropped_pre_attack)
        total_dropped_stats["during_attack"] += len(dropped_during_attack)
        total_dropped_stats["post_attack"] += len(dropped_post_attack)

        # Save dropped messages to CSV
        def save_dropped_messages(df, suffix):
            if not df.empty:
                file_path = os.path.splitext(subscriber_csv)[0] + f"_{suffix}_dropped.csv"
                df[["message"]].to_csv(file_path, index=False)
                logger.debug(f"{suffix.capitalize()} dropped messages saved to {file_path}")

        save_dropped_messages(dropped_pre_attack, "pre_attack")
        save_dropped_messages(dropped_during_attack, "during_attack")
        save_dropped_messages(dropped_post_attack, "post_attack")

    # Calculate overall average delays
    avg_delay_stats = {
        group: (sum(delays) / len(delays)) if delays else None
        for group, delays in total_delay_stats.items()
    }

    delay_95_percentile = {
        group: (pd.Series(delays).quantile(0.95) if delays else None)  # Default to None if no delays
        for group, delays in total_delay_stats.items()
    }

    logger.debug(f"Total dropped messages: {total_dropped_stats}")
    logger.debug(f"Average delays: {avg_delay_stats}")
    logger.debug(f"95th percentile delays: {delay_95_percentile}")

    # Merge DataFrames stats into a single DataFrame
    stats_df = pd.DataFrame({
        "group": ["pre_attack", "during_attack", "post_attack"],
        "dropped": [total_dropped_stats["pre_attack"], total_dropped_stats["during_attack"], total_dropped_stats["post_attack"]],
        "avg_delay (in seconds)": [avg_delay_stats["pre_attack"], avg_delay_stats["during_attack"], avg_delay_stats["post_attack"]],
        "95_percentile_delay (in seconds)": [delay_95_percentile["pre_attack"], delay_95_percentile["during_attack"], delay_95_percentile["post_attack"]]
    })

    return stats_df

def get_groups_of_csvs(nodes):
    """
    Analyzes all nodes in the experiment directory.
    """
    # Locate publisher and subscriber CSVs
    for node in nodes:
        publisher_csv, subscriber_csvs = find_csv_files(temp_dir, node)

        # Cross-reference logs
        if publisher_csv and subscriber_csvs:
            all_stats = cross_reference_logs(publisher_csv, subscriber_csvs, args.attack_start, args.post_attack)
            # Save all stats to a file
            file_path = os.path.splitext(args.experiment_file)[0] + f"_stats.csv"
            all_stats.to_csv(file_path, index=False)
            logger.debug(f"Stats saved to {file_path}")
            # Pretty print the results as a table
            print("\nSummary:")
            print(all_stats)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross-reference MQTT logs for dropped messages.")
    parser.add_argument("experiment_file", help="Path to the experiment tar.gz file.")
    # parser.add_argument("--grace-period", type=float, default=0, help="Grace period in seconds for late messages.")
    parser.add_argument("--attack-start", type=float, required=True, help="Timestamp of the attack start.")
    parser.add_argument("--post-attack", type=float, required=True, help="Duration of the attack in seconds.")
    parser.add_argument("-n", "--node", type=int, required=False, help="Node number.")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode.")
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(levelname)s - %(message)s")
    if args.debug:
        logger.setLevel(logging.DEBUG)

    try:
        # Extract experiment data
        extract_experiment_data(args.experiment_file, temp_dir)
        # Fill in the other timestamps too
        ATTACK_START = MENTORED_READY + pd.Timedelta(seconds=int(args.attack_start))
        ATTACK_END = MENTORED_READY + pd.Timedelta(seconds=int(args.post_attack))
        nodes = []
        if args.node:
            nodes = [args.node]
        else:
            nodes = range(1, 4)
        get_groups_of_csvs(nodes)



    finally:
        input("Press Enter to clean up temporary files")
        cleanup_experiment_data(temp_dir)

