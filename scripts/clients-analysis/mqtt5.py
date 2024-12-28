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
logger = logging.getLogger()
temp_dir = ".tmp_exp_analyzer"

def extract_experiment_data(expfile, temp_dir):
    """
    Extracts the MQTT-related CSV files from a tar.gz experiment file.
    """
    os.makedirs(temp_dir, exist_ok=True)
    logger.info(f"Extracting {expfile} into {temp_dir}")
    with tarfile.open(expfile, "r:gz") as tar:
        tar.extractall(temp_dir, members=(m for m in tar if "mqtt" in m.name))
    logger.debug(f"Contents of {temp_dir}: {os.listdir(temp_dir)}")
    with tarfile.open(expfile, "r:gz") as tar:
        for member in tar.getmembers():
            if "MENTORED_READY.txt" in member.name:
                f = tar.extractfile(member)
                content = f.read()
                logger.info(f"MENTORED_READY.txt content: {content}")
                # Convert content from unix timestamp to datetime
                global MENTORED_READY
                MENTORED_READY=int(content)
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

def find_csv_files(directory):
    """
    Finds publisher and subscriber CSV files in the extracted data.
    """
    publisher_csv = None
    subscriber_csvs = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".csv"):
                file_path = os.path.join(root, file)
                if "mqtt-pub" in file:
                    publisher_csv = file_path
                elif "mqtt-sub" in file:
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

def cross_reference_logs(publisher_csv, subscriber_csvs, grace_period, attack_start, post_attack):
    """
    Compares publisher messages against multiple subscriber messages to identify dropped messages.
    """
    publisher_df = load_csv(publisher_csv)
    if publisher_df is None:
        logger.error(f"Failed to load publisher CSV: {publisher_csv}")
        return

    # Filter only published messages
    publisher_df = publisher_df[publisher_df['action'] == 'published']
    published_messages = publisher_df[['time', 'message']]

    logger.info(f"Publisher logged {len(published_messages)} messages.")
    dropped_stats = {
        "pre_attack": 0,
        "during_attack": 0,
        "post_attack": 0
    }

    for subscriber_csv in subscriber_csvs:
        subscriber_df = load_csv(subscriber_csv)
        if subscriber_df is None:
            logger.warning(f"Skipping subscriber CSV: {subscriber_csv}")
            continue

        # Filter only received messages
        subscriber_df = subscriber_df[subscriber_df['action'] == 'received']

        dropped_pre_attack = []
        dropped_during_attack = []
        dropped_post_attack = []

        for _, pub_row in published_messages.iterrows():
            pub_time = float(pub_row['time'])
            pub_msg = pub_row['message']

            # Check for received messages within the grace period
            within_grace = subscriber_df[(subscriber_df['message'] == pub_msg) &
                                         (abs(subscriber_df['time'].astype(float) - pub_time) <= grace_period)]

            if within_grace.empty:
                if pub_time < MENTORED_READY+attack_start:
                    dropped_pre_attack.append(pub_msg)
                elif MENTORED_READY+attack_start <= pub_time <= MENTORED_READY+post_attack:
                    dropped_during_attack.append(pub_msg)
                else:
                    dropped_post_attack.append(pub_msg)

        logger.info(f"Subscriber {subscriber_csv}:")
        logger.info(f"  Pre-attack dropped: {len(dropped_pre_attack)} messages.")
        logger.info(f"  During attack dropped: {len(dropped_during_attack)} messages.")
        logger.info(f"  Post-attack dropped: {len(dropped_post_attack)} messages.")

        # Save dropped messages to separate files
        if dropped_pre_attack:
            pre_attack_file = os.path.splitext(subscriber_csv)[0] + "_pre_attack_dropped.csv"
            pd.DataFrame(dropped_pre_attack, columns=['message']).to_csv(pre_attack_file, index=False)
            logger.info(f"Pre-attack dropped messages saved to {pre_attack_file}")

        if dropped_during_attack:
            during_attack_file = os.path.splitext(subscriber_csv)[0] + "_during_attack_dropped.csv"
            pd.DataFrame(dropped_during_attack, columns=['message']).to_csv(during_attack_file, index=False)
            logger.info(f"During-attack dropped messages saved to {during_attack_file}")

        if dropped_post_attack:
            post_attack_file = os.path.splitext(subscriber_csv)[0] + "_post_attack_dropped.csv"
            pd.DataFrame(dropped_post_attack, columns=['message']).to_csv(post_attack_file, index=False)
            logger.info(f"Post-attack dropped messages saved to {post_attack_file}")
    
    dropped_stats["pre_attack"] = dropped_stats["pre_attack"] + len(dropped_pre_attack),
    dropped_stats["during_attack"] = dropped_stats["during_attack"] + len(dropped_during_attack),
    dropped_stats["post_attack"] = dropped_stats["post_attack"] + len(dropped_post_attack)
    
    return dropped_stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross-reference MQTT logs for dropped messages.")
    parser.add_argument("experiment_file", help="Path to the experiment tar.gz file.")
    parser.add_argument("--grace-period", type=float, default=0, help="Grace period in seconds for late messages.")
    parser.add_argument("--attack-start", type=float, required=True, help="Timestamp of the attack start.")
    parser.add_argument("--post-attack", type=float, default=0, help="Duration of the attack in seconds.")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode.")
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(levelname)s - %(message)s")
    if args.debug:
        logger.setLevel(logging.DEBUG)

    try:
        # Extract experiment data
        extract_experiment_data(args.experiment_file, temp_dir)

        # Locate publisher and subscriber CSVs
        publisher_csv, subscriber_csvs = find_csv_files(temp_dir)

        # Cross-reference logs
        if publisher_csv and subscriber_csvs:
            stats = cross_reference_logs(publisher_csv, subscriber_csvs, args.grace_period, args.attack_start, args.post_attack)
            logger.info(f"Summary: {stats}")


    finally:
        print("Cleaning up temporary files")
        input("Press Enter to continue...")
        cleanup_experiment_data(temp_dir)

