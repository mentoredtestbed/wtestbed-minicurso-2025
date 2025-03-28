from experiments.post_process_functions import ExperimentPostProcessor
from experiments.post_process_functions.utils import unify_registry

class UnifyRegistries(ExperimentPostProcessor):
    def post_process(self):
        temp_dir = self.initialize()
        self.extract_na_data(temp_dir)
        
        try:
            unify_registry(temp_dir)
            self.add_log_text("Unified registries. Creating UNIFIED_MENTORED_REGISTRY.yaml\n")
        except Exception as e:
            self.add_log_text(f"Error unifying registries: {e}\n")

        # Finalize the post-processing
        self.finalize(temp_dir)
