#!/usr/bin/env python3
import pandas as pd
import argparse
import os

def load_csv(file_path):
    """
    Loads a CSV file into a DataFrame.
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return None

def cross_reference_logs(publisher_csv, subscriber_csvs, grace_period):
    """
    Compares publisher messages against multiple subscriber messages to identify dropped messages.
    """
    publisher_df = load_csv(publisher_csv)
    if publisher_df is None:
        print(f"Failed to load publisher CSV: {publisher_csv}")
        return

    # Filter only published messages from publisher CSV
    publisher_df = publisher_df[publisher_df['action'] == 'published']
    published_messages = set(publisher_df['message'])

    print(f"Publisher logged {len(published_messages)} messages.")

    for subscriber_csv in subscriber_csvs:
        subscriber_df = load_csv(subscriber_csv)
        if subscriber_df is None:
            print(f"Skipping subscriber CSV: {subscriber_csv}")
            continue

        # Filter only received messages
        subscriber_df = subscriber_df[subscriber_df['action'] == 'received']
        received_messages = set(subscriber_df['message'])

        publisher_times = publisher_df['time'].astype(float)
        received_times = subscriber_df['time'].astype(float)

        # Apply grace period
        valid_messages = published_messages.copy()
        for pub_time, pub_msg in zip(publisher_times, publisher_df['message']):
            if any(abs(pub_time - sub_time) <= args.grace_period for sub_time in received_times):
                valid_messages.discard(pub_msg)

        dropped_messages = valid_messages - received_messages
        print(f"Subscriber {subscriber_csv}: {len(dropped_messages)} messages dropped.")

        # Optional: Save dropped messages to a file
        if dropped_messages:
            output_file = os.path.splitext(subscriber_csv)[0] + "_dropped.csv"
            dropped_df = pd.DataFrame(list(dropped_messages), columns=['message'])
            dropped_df.to_csv(output_file, index=False)
            print(f"Dropped messages saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross-reference MQTT logs for dropped messages.")
    parser.add_argument("publisher_csv", help="Path to the publisher's CSV log file.")
    parser.add_argument("subscriber_csvs", nargs='+', help="Paths to the subscribers' CSV log files.")
    parser.add_argument("--grace-period", type=float, default=0, help="Grace period in seconds for late messages.")

    args = parser.parse_args()

    cross_reference_logs(args.publisher_csv, args.subscriber_csvs, args.grace_period)
