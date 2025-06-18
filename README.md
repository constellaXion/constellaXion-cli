<a name="readme-top"></a>

<div align="center">
  <img src="./assets/icon.svg" alt="Logo" width="200">
  <h1 align="center">constellaXion CLI: Automated LLM Deployments for your private cloud</h1>
</div>

<div align="center">
  <a href="https://constellaxion.ai"><img src="https://img.shields.io/badge/Project-Page-blue?style=for-the-badge&color=A0C7FE&logo=homepage&logoColor=white" alt="Project Page"></a>
  <a href="https://constellaxion.github.io"><img src="https://img.shields.io/badge/Documentation-000?logo=googledocs&logoColor=A0C7FE&style=for-the-badge" alt="Check out the documentation"></a>
  <hr>
</div>



The fastest way to **Train, Deploy and Serve** Open Source Language Models to your Private Cloud

# ⚡️ Features
Configure and access the most popular open source LLMs with a few simple commands

- 📄 YAML-based configuration

- ⚙️ Fine-tune LLMs with your own data and cloud resources

- 🚀 Deploy models to your private cloud

- 🤖 Serve your models with ease

- 💬 Prompt your models with ease


# 📚 The Stack
<div style="margin-bottom: 40px;">
  <div align="center" style="display: flex; gap: 10px; justify-content: center; align-items: center; margin-bottom: 20px;">
    <img src="./assets/gcp.png" width="150" height="150"/>
    <img src="./assets/aws.png" width="100" height="80"/>
  </div>
  <div align="center" style="display: flex; gap: 10px; justify-content: center; align-items: center; margin-bottom: 40px;">
    <img src="./assets/huggingface.svg" width="100"/>
    <img src="./assets/vllm.svg" width="150"/>
    <img src="./assets/djl.png" width="150"/>
  </div>
  <div align="center" style="display: flex; gap: 10px; justify-content: center; align-items: center">
    <img src="./assets/unsloth.png" width="300"/>
  </div>
</div>

  <p>
    ConstellaXion leverages industry-leading technologies to provide a seamless LLM deployment experience. Deploy to AWS or GCP, serve models efficiently with vLLM, access the latest models from Hugging Face, and utilize DJL's powerful serving capabilities.
  </p>
</div>


# 🔧 Quick Start

## Installation

Install the package:

```sh
pip install constellaxion
```

For Windows users: this package may compile dependencies (e.g., numpy) from source.
Please ensure you have the Microsoft C++ Build Tools installed:
https://visualstudio.microsoft.com/visual-cpp-build-tools/

Alternatively, install with prebuilt binaries:

```sh
pip install --prefer-binary constellaxion
```

## YAML Configuration Format

Create a `model.yaml` file to describe your project. Example:

```yaml
model:
  id: my-llm
  base: tiiuae/falcon-7b-instruct

dataset:
  train: ./train.csv # Path to your training data.
  val: ./val.csv # Path to your validation data
  test: ./test.csv # Path to your test data

training:
  epochs: 1
  batch_size: 4

deploy:
  gcp:
    project_id: my-gcp-project
    region: europe-west2
```

model (required): The ID of the model you want to use.

base (required): The base model you want to use (HuggingFace path).

dataset (required for finetuning): The path to your training, validation, and test data.
- All 3 datasets must be provided as CSV files with the following columns: `prompt`, `response`.

training (required for finetuning): The number of epochs and batch size for training.

deploy (required for deployment): The Deployment target. Currently only GCP is supported.
- gcp:
  - project_id: The GCP project ID.
  - region: The GCP region to deploy the model to.

## Usage
Initialize your project:

```sh
constellaXion init
```


View your current model configuration:
```sh
constallaXion model view
```


Deploy a foundation model without finetuning:
```sh
constellaXion model deploy
```


Run fine-tuninig job (Dataset and training configs required):
```sh
constallaXion model train
```


Serve a fine-tuned model:
```sh
constallaXion model serve
```

Prompt model:
```sh
constallaXion model prompt
```



## Example Workflow
Create model.yaml file: to fit your use case
```sh
constellaXion init
```

Print the current training and serving configuration from your YAML file:
```sh
constellaXion model view
```

Run training job:
```sh
constellaXion model train
constellaXion model serve
constellaXion model prompt
```
