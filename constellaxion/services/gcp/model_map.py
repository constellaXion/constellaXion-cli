model_map = {
    "TinyLlama-1B": {
        "dir": "tinyllama_1b",
        "namespace": "TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T",
        "lora": "../../models/tinyllama_1b/gcp/lora.py",
        "infra": {
            "train_image_uri": "europe-docker.pkg.dev/vertex-ai/training/tf-gpu.2-14.py310:latest",
            "serve_image_uri": "europe-west2-docker.pkg.dev/constellaxion/serving-images/completion-model:latest",
            "requirements": [
                "constellaxion-utils==0.1.3",
                "trl",
                "transformers",
                "dataset",
                "peft",
                "google-cloud-storage",
                "python-json-logger",
                "watchdog",
                "gcsfs"
            ],
            "machine_type": "g2-standard-4",
            "accelerator_type": "NVIDIA_L4",
            "accelerator_count": 1,
            "replica_count": 1
        }
    }
}
