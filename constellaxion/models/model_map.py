"""Configuration mapping for supported foundation models and their infrastructure requirements."""

model_map = {
    # "TinyLlama-1B": {
    #     "dir": "tinyllama_1b",
    #     "namespace": "TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T",
    #     "lora": "../../models/tinyllama_1b/gcp/lora.py",
    #     "infra": {
    #         "train_image_uri": "europe-docker.pkg.dev/vertex-ai/training/tf-gpu.2-14.py310:latest",
    #         "serve_image_uri": "europe-west2-docker.pkg.dev/constellaxion/serving-images/completion-model:latest",
    #         "requirements": [
    #             "constellaxion-utils==0.1.3",
    #             "trl",
    #             "transformers",
    #             "dataset",
    #             "peft",
    #             "google-cloud-storage",
    #             "python-json-logger",
    #             "watchdog",
    #             "gcsfs"
    #         ],
    #         "machine_type": "g2-standard-4",
    #         "accelerator_type": "NVIDIA_L4",
    #         "accelerator_count": 1,
    #         "replica_count": 1
    #     }
    # },
    "@tinyllama-bnb-4bit": {
        "base_model": "unsloth/tinyllama-bnb-4bit",
        "dtype": None,
        "max_seq_length": 4096,
        "gcp_infra": {
            "machine_type": "g2-standard-8",
            "accelerator_type": "NVIDIA_L4",
            "accelerator_count": 1,
            "replica_count": 1,
            "images": {
                "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model:latest",
                "finetune": "europe-west2-docker.pkg.dev/constellaxion/finetuning/unsloth-base-model:latest",
            },
        },
        "aws_infra": {
            "instance_type": "ml.g4dn.xlarge",
            "accelerator_type": "NVIDIA_TESLA_T4",
            "accelerator_count": 1,
            "min_replica_count": 1,
            "max_replica_count": 2,
            "images": {
                "serve": "567326753429.dkr.ecr.eu-north-1.amazonaws.com/constellaxion/serving-images:foundation-model-v1",
                "finetune": "",
            },
        },
    },
    "@Mistral-7B-v0.1": {
        "base_model": "mistralai/Mistral-7B-v0.1",
        "gcp_infra": {
            "machine_type": "n1-highmem-8",
            "accelerator_type": "NVIDIA_TESLA_T4",
            "accelerator_count": 1,
            "replica_count": 1,
            "dtype": "float16",
        },
        "images": {
            "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model:latest",
            "finetune": "",
        },
        "aws_infra": {
            "instance_type": "ml.g4dn.xlarge",
            "accelerator_type": "NVIDIA_TESLA_T4",
            "accelerator_count": 1,
            "min_replica_count": 1,
            "max_replica_count": 2,
            "dtype": "float16",
            "images": {
                "serve": "public.ecr.aws/n6b1s4s0/constellaxion/serving:foundation-model-v1",
                "finetune": "",
            },
        },
    },
    "@Mixtral-8x7B": {
        "base_model": "mistralai/Mixtral-8x7B",
        "gcp_infra": {
            "machine_type": "n1-highmem-16",
            "accelerator_type": "NVIDIA_A100_40GB",
            "accelerator_count": 2,
            "replica_count": 1,
        },
        "images": {
            "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model",
            "finetune": "",
        },
        "aws_infra": {
            "instance_type": "ml.p4d.24xlarge",
            "accelerator_type": "NVIDIA_A100_40GB",
            "accelerator_count": 2,
            "min_replica_count": 1,
            "max_replica_count": 2,
            "images": {
                "serve": "public.ecr.aws/n6b1s4s0/constellaxion/serving:foundation-model-v1",
                "finetune": "",
            },
        },
    },
    "@Qwen1.5-7B": {
        "base_model": "Qwen/Qwen1.5-7B",
        "gcp_infra": {
            "machine_type": "n1-highmem-8",
            "accelerator_type": "NVIDIA_TESLA_T4",
            "accelerator_count": 1,
            "replica_count": 1,
            "images": {
                "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model:latest",
                "finetune": "",
            },
        },
        "aws_infra": {
            "instance_type": "ml.g4dn.xlarge",
            "accelerator_type": "NVIDIA_TESLA_T4",
            "accelerator_count": 1,
            "min_replica_count": 1,
            "max_replica_count": 2,
            "images": {
                "serve": "public.ecr.aws/n6b1s4s0/constellaxion/serving:foundation-model-v1",
                "finetune": "",
            },
        },
    },
    "@Qwen1.5-14B": {
        "base_model": "Qwen/Qwen1.5-14B",
        "gcp_infra": {
            "machine_type": "n1-highmem-16",
            "accelerator_type": "NVIDIA_A100_40GB",
            "accelerator_count": 2,
            "replica_count": 1,
            "images": {
                "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model:latest",
                "finetune": "",
            },
        },
        "aws_infra": {
            "instance_type": "ml.p4d.24xlarge",
            "accelerator_type": "NVIDIA_A100_40GB",
            "accelerator_count": 2,
            "min_replica_count": 1,
            "max_replica_count": 2,
            "images": {
                "serve": "public.ecr.aws/n6b1s4s0/constellaxion/serving:foundation-model-v1",
                "finetune": "",
            },
        },
    },
    "@Llama-2-7b-chat-hf": {
        "base_model": "meta-llama/Llama-2-7b-chat-hf",
        "gcp_infra": {
            "machine_type": "g2-standard-8",
            "accelerator_type": "NVIDIA_L4",
            "accelerator_count": 1,
            "replica_count": 1,
            "images": {
                "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model:latest",
                "finetune": "",
            },
        },
        "aws_infra": {
            "instance_type": "ml.g5.xlarge",
            "accelerator_type": "NVIDIA_L4",
            "accelerator_count": 1,
            "min_replica_count": 1,
            "max_replica_count": 2,
            "images": {
                "serve": "public.ecr.aws/n6b1s4s0/constellaxion/serving:foundation-model-v1",
                "finetune": "",
            },
        },
    },
    "@Llama-2-13b-hf": {
        "base_model": "meta-llama/Llama-2-13b-hf",
        "gcp_infra": {
            "machine_type": "n1-highmem-16",
            "accelerator_type": "NVIDIA_A100_40GB",
            "accelerator_count": 1,
            "replica_count": 1,
            "images": {
                "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model:latest",
                "finetune": "",
            },
        },
        "aws_infra": {
            "instance_type": "ml.p4d.24xlarge",
            "accelerator_type": "NVIDIA_A100_40GB",
            "accelerator_count": 1,
            "min_replica_count": 1,
            "max_replica_count": 2,
            "images": {
                "serve": "public.ecr.aws/n6b1s4s0/constellaxion/serving:foundation-model-v1",
                "finetune": "",
            },
        },
    },
    "@Llama-2-70b-chat-hf": {
        "base_model": "meta-llama/Llama-2-70b-chat-hf",
        "gcp_infra": {
            "machine_type": "n1-highmem-64",
            "accelerator_type": "NVIDIA_A100_80GB",
            "accelerator_count": 8,
            "replica_count": 1,
        },
        "images": {
            "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model",
            "finetune": "",
        },
        "aws_infra": {
            "instance_type": "ml.p4de.24xlarge",
            "accelerator_type": "NVIDIA_A100_80GB",
            "accelerator_count": 8,
            "min_replica_count": 1,
            "max_replica_count": 2,
            "images": {
                "serve": "public.ecr.aws/n6b1s4s0/constellaxion/serving:foundation-model-v1",
                "finetune": "",
            },
        },
    },
    "@falcon-7b-instruct": {
        "base_model": "tiiuae/falcon-7b-instruct",
        "gcp_infra": {
            "machine_type": "g2-standard-8",
            "accelerator_type": "NVIDIA_L4",
            "accelerator_count": 1,
            "replica_count": 1,
            "images": {
                "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model:latest",
                "finetune": "",
            },
        },
        "aws_infra": {
            "instance_type": "ml.g5.xlarge",
            "accelerator_type": "NVIDIA_L4",
            "accelerator_count": 1,
            "min_replica_count": 1,
            "max_replica_count": 2,
            "images": {
                "serve": "001939129420.dkr.ecr.eu-west-1.amazonaws.com/constellaxion/serving-images:foundation-model-v1",
                "finetune": "",
            },
        },
    },
    "@falcon-40b-instruct": {
        "base_model": "tiiuae/falcon-40b-instruct",
        "gcp_infra": {
            "machine_type": "n1-highmem-32",
            "accelerator_type": "NVIDIA_A100_40GB",
            "accelerator_count": 4,
            "replica_count": 1,
            "images": {
                "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model:latest",
                "finetune": "",
            },
        },
        "aws_infra": {
            "instance_type": "ml.p4d.24xlarge",
            "accelerator_type": "NVIDIA_A100_40GB",
            "accelerator_count": 4,
            "min_replica_count": 1,
            "max_replica_count": 2,
            "images": {
                "serve": "public.ecr.aws/n6b1s4s0/constellaxion/serving:foundation-model-v1",
                "finetune": "",
            },
        },
    },
    "@gemma-3-4b-it": {
        "base_model": "google/gemma-3-4b-it",
        "gcp_infra": {
            "machine_type": "g2-standard-8",
            "accelerator_type": "NVIDIA_L4",
            "accelerator_count": 1,
            "replica_count": 1,
            "images": {
                "serve": "europe-west2-docker.pkg.dev/constellaxion/serving-images/foundation-model:latest",
                "finetune": "",
            },
        },
        "aws_infra": {
            "instance_type": "ml.g5.xlarge",
            "accelerator_type": "NVIDIA_L4",
            "accelerator_count": 1,
            "min_replica_count": 1,
            "max_replica_count": 2,
            "images": {
                "serve": "public.ecr.aws/n6b1s4s0/constellaxion/serving:foundation-model-v1",
                "finetune": "",
            },
        },
    },
}
