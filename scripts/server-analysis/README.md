# Análise de dados do servidor

> ![IMPORTANT] Os comandos abaixo presumem um ambiente Linux com Python3, para essa finalidade uma imagem de container para as ferramentas de análise é provida no passo 3. Usuário avançados podem também optar por instalar as dependencias Python3 diretamente num ambiente Linux como Ubuntu 24.04.

1) Baixe o arquivo `.tar.gz` e copie o mesmo para esta pasta

```bash
MY_EXP_DURATION=300
MY_EXP_FILE=experiment_847.tar.gz
cp ~/Downloads/$MY_EXP_FILE .

```

2) Utilize um ambiente com Python3 e execute o script de análise

> [!NOTE] Abaixo um exemplo utilizando a imagem Docker pré-construída

```bash
sudo docker run --rm -it \
    -v .:/app ghcr.io/khalilsantana/dataset-mentored-iot-2024 \
    /app/scripts/server-analysis/experiment_analyzer.sh ../../$MY_EXP_FILE $MY_EXP_DURATION
```

3) Observe os resultados, em `scripts/server-analysis/output_Second.png`


![alt text](../../img/C2-Vazão-e-pacotes.png)