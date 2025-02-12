# Bachelorprojekt

### 1. Oprettelse af virtuelt miljø
For at oprette et nyt virtuelt miljø med conda til Python, skal du følge nedenstående trin:

1. Åbn en terminal eller kommandoprompt.
2. Naviger til den mappe, hvor du vil oprette det virtuelle miljø.
3. Kør følgende kommando for at oprette et nyt virtuelt miljø med Python:

    ```sh
    conda create --name myenv python=3.11
    ```

    Her opretter vi et virtuelt miljø kaldet `myenv` med Python version 3.11. Du kan vælge et andet navn eller Python version, hvis du ønsker det.

4. Aktiver det virtuelle miljø:

    ```sh
    conda activate myenv
    ```

5. Når det virtuelle miljø er aktiveret, vil du se navnet på miljøet i terminalprompten. Nu kan du installere de nødvendige afhængigheder ved hjælp af `conda` eller `pip`.

    ```sh
    pip install -r requirements.txt
    ```

    Sørg for, at du har en `requirements.txt`-fil i din projektmappe, som indeholder alle de nødvendige afhængigheder.

Når du er færdig med at arbejde i det virtuelle miljø, kan du deaktivere det ved at køre:

```sh
conda deactivate
```
