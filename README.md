# Bachelorprojekt

## Get Software

To get started, you must first download the folder to your computer.

## Create a Virtual Environment

1. Create a new Conda environment by running:

    ```bash
    conda create --name bachelorprojekt python=3.11  # Name and version is up to you.
    ```

2. Select your environment in VS Code. To do this, open the command palette using `ctrl+Shift+P`, type `Python: Select Interpreter`, and select your environment (`bachelorprojekt`) from the list. If it does not appear, select **Enter interpreter path** and navigate to it.

3. Navigate to the `bachelorprojekt` folder and run:

    ```bash
    conda install -c conda-forge --file requirements_conda.txt
    pip install -r requirements_pip.txt
    ```
```sh
conda deactivate
```
