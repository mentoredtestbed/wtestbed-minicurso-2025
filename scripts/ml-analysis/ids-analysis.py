from create_and_analyse_ml_dataset import CreateAndAnalyseMLDataset
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge datasets")
    parser.add_argument(
        "--files", type=str, nargs="+", help=".tar.gz Files to merge", required=True)
    args = parser.parse_args()
    files = args.files

    for exp in args.files:
        c = CreateAndAnalyseMLDataset(
            0, # Mandatory ID. Not used, so it can be any number
            "CreateAndAnalyseMLDataset",
            exp,
            ignore_classes=["attack-sshbruteforce"])
        c.post_process()
