<a name="readme-top"></a>

<div align="center">
  <img src="./assets/icon_light_bg.svg" alt="Logo" width="200">
  <h1 align="center">constellaXion CLI: Automated LLM Deployments for your private cloud</h1>
</div>

<div align="center">
  <a href="https://constellaxion.ai"><img src="https://img.shields.io/badge/Project-Page-blue?style=for-the-badge&color=A0C7FE&logo=homepage&logoColor=white" alt="Project Page"></a>
  <a href="https://constellaxion.github.io"><img src="https://img.shields.io/badge/Documentation-000?logo=googledocs&logoColor=A0C7FE&style=for-the-badge" alt="Check out the documentation"></a>
  <hr>
</div>



The fastest way to **Train, Deploy and Serve** Open Source Language Models to your Cloud environment

# ⚡️ Features
Configure and access the most popular open source LLMs with a few simple commands

- 📄 YAML-based configuration

- ⚙️ Fine-tune LLMs with your own data and cloud resources

- 🚀 Deploy models to your private cloud environment

- 🤖 Serve your models with ease

- 💬 Prompt your models with ease


# 📚 The Stack
<div align="center">
  <table>
    <tr>
      <td align="center"><img src="https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg" width="100"/></td>
      <td align="center"><img src="https://www.vectorlogo.zone/logos/google_cloud/google_cloud-ar21.svg" width="140"/></td>
    </tr>
    <tr>
      <td align="center"><img src="https://huggingface.co/front/assets/huggingface_logo-noborder.svg" width="100"/></td>
      <td align="center"><img src="https://docs.vllm.ai/en/latest/_images/vllm-logo-text-light.png" width="150"/></td>
      <td align="center"><img src="https://raw.githubusercontent.com/deepjavalibrary/djl/master/website/img/djl.png" width="100"/></td>
    </tr>
  </table>

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
    location: europe-west2
```

model (required): The ID of the model you want to use.

base (required): The base model you want to use (HuggingFace path).

dataset (required for finetuning): The path to your training, validation, and test data.
- All 3 datasets must be provided as CSV files with the following columns: `prompt`, `response`.

training (required for finetuning): The number of epochs and batch size for training.

deploy (required for deployment): The Deployment target. Currently only GCP is supported.
- gcp:
  - project_id: The GCP project ID.
  - location: The GCP region to deploy the model to.

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
