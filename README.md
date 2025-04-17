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

## ⚡️ Features
Configure and access the most popular open source LLMs with a few simple commands

- 📄 YAML-based configuration

- ⚙️ Fine-tune LLMs with your own data and cloud resources

- 🚀 Deploy models to your private cloud environment

- 🤖 Serve your models with ease

- 💬 Prompt your models with ease


## Installation

Install the package:

```sh
pip install constellaxion
```

## 🧾 YAML Configuration Format

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

base (required): The base model you want to use.

dataset (required for finetuning): The path to your training, validation, and test data.
- All 3 datasets must be provided as CSV files with the following columns: `prompt`, `response`.

training (required for finetuning): The number of epochs and batch size for training.

deploy (required for deployment): The Deployment target. Currently only GCP is supported.
- gcp:
  - project_id: The GCP project ID.
  - location: The GCP region to deploy the model to.

## Usage
1. Initialize your project:

    ```sh
    constellaXion init
    ```

2. Print the current training and serving configuration from your YAML file:

    ```sh
    constallaXion model view
    ```

3. Run training job (only if you have provided a dataset):

    ```sh
    constallaXion model train
    ```

4. Serve model (for finetuned models only):

    ```sh
    constallaXion model serve
    ```

5. Deploy a foundation model without finetuning:

    ```sh
    constellaXion model deploy
    ```

6. Prompt model:

    ```sh
    constallaXion model prompt
    ```



## 💡 Example Workflow
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