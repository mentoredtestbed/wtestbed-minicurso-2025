from unify_registry import unify_registry
from add_labels import create_labeled_file
from create_ml_dataset import create_argus_flows_csv
from ml_analysis import create_dataset_analysis

import os
import tarfile
import tempfile
import shutil
import time
import os

PROCESS_LOGS_SUBPATH = "post_process_logs"

class ExperimentPostProcessor():
    def __init__(self, function_id: int, name: str, experiment_targz_path: str = None):
        self.function_id = function_id
        self.name = name
        self.experiment_targz_path = experiment_targz_path
        self.temp_dir = None
        self.logs = ""

    def set_experiment_targz_path(self, experiment_targz_path):
        self.experiment_targz_path = experiment_targz_path
    
    def post_process(self):
        raise NotImplementedError("Method not implemented")

    def initialize(self):
        if self.experiment_targz_path is None:
            raise ValueError("Experiment tar.gz path not set")
        temp_dir = self.extract_to_temp()
        return temp_dir

    def extract_to_temp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Load the experiment tar.gz file and extract it to a temporary directory
        with tarfile.open(self.experiment_targz_path, "r:gz") as tar:
            tar.extractall(self.temp_dir)

        return self.temp_dir

    def extract_na_data(self, temp_dir):
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(".tar"):
                    file_path = os.path.join(root, file)
                    dir_name = os.path.splitext(file)[0]
                    dir_path = os.path.join(root, dir_name)
                    print(f"Extracting {file_path} to {dir_path}")
                    self.add_log_text(f"Extracting {file_path} to {dir_path}")
                    os.makedirs(dir_path, exist_ok=True)
                    with tarfile.open(file_path, "r:") as tar:
                        tar.extractall(dir_path)
                    os.remove(file_path)

    def update_modification_logs(self, temp_dir):
        # Update the modification logs
        timestamp = int(time.time())
        timestmap_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
        log_path = f"{temp_dir}/{PROCESS_LOGS_SUBPATH}"
        # Ensure the logs directory exists
        os.makedirs(log_path, exist_ok=True)
        with open(f"{log_path}/modification_logs.txt", "a") as f:
            f.write(f"{timestmap_str}: Executed function with ID {self.function_id} ({self.name})\n")
            f.write(self.logs)

    def add_log_text(self, text):
        self.logs += text + "\n"

    def finalize(self, temp_dir):
        new_targz_path = self.experiment_targz_path.replace(".tar.gz", "_post_processed.tar.gz")

        self.update_modification_logs(temp_dir)

        # Create a new tar.gz file with the contents of the temporary directory
        with tarfile.open(new_targz_path, "w:gz") as tar:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=temp_dir)
                    tar.add(file_path, arcname=arcname)

        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)

        # Replace
        shutil.move(new_targz_path, self.experiment_targz_path)

        return self.experiment_targz_path


class CreateAndAnalyseMLDataset(ExperimentPostProcessor):
    def __init__(self, *args, ignore_classes: list, **kwargs):
        super().__init__(*args, **kwargs)
        self.ignore_classes = ignore_classes
    
    def post_process(self):
        temp_dir = self.initialize()
        self.extract_na_data(temp_dir)

        try:
            unify_registry(temp_dir)
            self.add_log_text("Unified registries. Creating UNIFIED_MENTORED_REGISTRY.yaml\n")
        except Exception as e:
            print(f"Error unifying registries: {e}\n")
            self.add_log_text(f"Error unifying registries: {e}\n")

        flows_path = os.path.join(temp_dir, "flows.csv")
        labeled_flows_path = os.path.join(temp_dir, "labeled_flows.csv")

        self.add_log_text(create_argus_flows_csv(temp_dir, flows_path))
        self.add_log_text(
            create_labeled_file(
                flows_path,
                labeled_flows_path,
                base_path=temp_dir))
        
        self.add_log_text(create_dataset_analysis(labeled_flows_path, ignore_classes=self.ignore_classes))

        # Finalize the post-processing
        self.finalize(temp_dir)
