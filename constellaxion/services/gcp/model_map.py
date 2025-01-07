model_map = {
    "TinyLlama-1B": {
        "dir": "tinyllama_1b",
        "lora": "../../models/tinyllama_1b/gcp/lora.py",
        "infra": {
            "container_uri": "europe-docker.pkg.dev/vertex-ai/training/tf-gpu.2-14.py310:latest",
            "requirements": [
                "trl==0.12.0",
                "transformers",
                "dataset",
                "peft",
                "google-cloud-storage"
            ],
            "machine_type": "g2-standard-4",
            "accelerator_type": "NVIDIA_L4",
            "accelerator_count": 1,
            "replica_count": 1
        }
    }
}
