# Intern

This project is to build an agent that can help with your daily work tasks


# Local development
This project uses uv for dependency management, environment management, and running the project. To install uv, run:


## Install UV
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
````

### Understanding UV
See https://www.saaspegasus.com/guides/uv-deep-dive/#advanced-usage for a great intro to UV.


## Install dependencies

To install the dependencies, run:

```bash
uv sync
```
This command will:

1. Find or download an appropriate Python version to use.
2. Create and set up your environment in the .venv folder.
3. Build your complete dependency list and write to your uv.lock file.
4. Sync your project dependencies into your virtual environment.


## Run the project
You can run the project with the following command:

```bash
uv run streamlit run app.py
```

which is equivalent to

```bash
uv sync
source .venv/bin/activate
python streamlit run app.py
```

# Potential design

- Filter button grabs relevant data 
  - Based off source & destination postcodes

- Generate predictions using back tests

# Trim down packages in uv

I've added the packages for training a model to the deployment which aren't needed