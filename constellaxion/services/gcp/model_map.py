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
    },
    "mistralai/Mistral-7B": {
        "gcp_infra": {
            "machine_type": "n1-highmem-8",
            "accelerator_type": "NVIDIA_TESLA_T4",
            "accelerator_count": 1,
            "replica_count": 1
     },
     "images": {
        "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model",
        "finetune": ""
     }
  },
  "mistralai/Mixtral-8x7B": {
    "gcp_infra": {
      "machine_type": "n1-highmem-16",
      "accelerator_type": "NVIDIA_A100_40GB",
      "accelerator_count": 2,
      "replica_count": 1
    },
    "images": {
        "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model",
        "finetune": ""
     }

  },
  "Qwen/Qwen1.5-7B": {
    "gcp_infra": {
      "machine_type": "n1-highmem-8",
      "accelerator_type": "NVIDIA_TESLA_T4",
      "accelerator_count": 1,
      "replica_count": 1
    },
    "images": {
        "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model",
        "finetune": ""
     }
  },
  "Qwen/Qwen1.5-14B": {
    "gcp_infra": {
      "machine_type": "n1-highmem-16",
      "accelerator_type": "NVIDIA_A100_40GB",
      "accelerator_count": 2,
      "replica_count": 1
    },
    "images": {
        "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model",
        "finetune": ""
     }
  },
  "meta-llama/Llama-2-7b-chat-hf": {
    "gcp_infra": {
      "machine_type": "n1-highmem-8",
      "accelerator_type": "NVIDIA_TESLA_T4",
      "accelerator_count": 1,
      "replica_count": 1
    },
    "images": {
        "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model",
        "finetune": ""
     }
  },
  "meta-llama/Llama-2-13b-chat-hf": {
    "gcp_infra": {
      "machine_type": "n1-highmem-16",
      "accelerator_type": "NVIDIA_A100_40GB",
      "accelerator_count": 2,
      "replica_count": 1
    },
    "images": {
        "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model",
        "finetune": ""
     }
  },
  "meta-llama/Llama-2-70b-chat-hf": {
    "gcp_infra": {
      "machine_type": "n1-highmem-64",
      "accelerator_type": "NVIDIA_A100_80GB",
      "accelerator_count": 8,
      "replica_count": 1
    },
    "images": {
        "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model",
        "finetune": ""
     }
  },
  "tiiuae/falcon-7b-instruct": {
    "gcp_infra": {
      "machine_type": "n1-highmem-8",
      "accelerator_type": "NVIDIA_TESLA_T4",
      "accelerator_count": 1,
      "replica_count": 1
    },
    "images": {
        "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model",
        "finetune": ""
     }
  },
  "tiiuae/falcon-40b-instruct": {
    "gcp_infra": {
      "machine_type": "n1-highmem-32",
      "accelerator_type": "NVIDIA_A100_40GB",
      "accelerator_count": 4,
      "replica_count": 1
    },
    "images": {
        "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model",
        "finetune": ""
     }
  },
  "google/gemma-7b": {
    "gcp_infra": {
      "machine_type": "n1-highmem-8",
      "accelerator_type": "NVIDIA_TESLA_T4",
      "accelerator_count": 1,
      "replica_count": 1
    },
    "images": {
        "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model",
        "finetune": ""
     }
  },
  "google/gemma-2b": {
    "gcp_infra": {
      "machine_type": "n1-standard-4",
      "accelerator_type": "NVIDIA_TESLA_T4",
      "accelerator_count": 1,
      "replica_count": 1
    },
    "images": {
        "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model",
        "finetune": ""
     }
  }
}
