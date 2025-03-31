from create_and_analyse_ml_dataset import CreateAndAnalyseMLDataset


# experiment_targz_path = "C1-2025-v1-EXP1205.tar.gz"
# experiment_targz_path = "C2-2025-v1-EXP1206.tar.gz"
# experiment_targz_path = "C3-2025-v2-EXP1210.tar.gz"
# experiment_targz_path = "C4-2025-v4-EXP1268.tar.gz"
experiment_targz_path = "MERGED-DS"

exp_list = [
    "C1-2025-v1-EXP1205.tar.gz",
    "C2-2025-v1-EXP1206.tar.gz",
    "C3-2025-v2-EXP1210.tar.gz",
    "C4-2025-v4-EXP1268.tar.gz",
    # "MERGED-DS.tar.gz"
]

for exp in exp_list:
    c = CreateAndAnalyseMLDataset(
        0,
        "CreateAndAnalyseMLDataset",
        exp,
        ignore_classes=["attack-sshbruteforce"])
    c.post_process()
