# Análise de dados do cliente

> ![IMPORTANT] Os comandos abaixo presumem um ambiente Linux com Python3, para essa finalidade uma imagem de container para as ferramentas de análise é provida no passo 3. Usuário avançados podem também optar por instalar as dependencias Python3 diretamente num ambiente Linux como Ubuntu 24.04.

1) Baixe o arquivo `.tar.gz` e copie o mesmo para esta pasta

```bash
MY_ATTACK_START=60
MY_ATTACK_END=240
MY_EXP_FILE=experiment_847.tar.gz
cp ~/Downloads/$MY_EXP_FILE .

```

2) Utilize um ambiente com Python3 e execute o script de análise

> [!NOTE] Abaixo um exemplo utilizando a imagem Docker pré-construída

```bash
sudo docker run --rm -it \
    -v .:/app ghcr.io/khalilsantana/dataset-mentored-iot-2024 \
    python3 /app/scripts/clients-analysis/client_metrics.py \
    ../../$MY_EXP_FILE -a $MY_ATTACK_START -p $MY_ATTACK_END
```

3) Observe os resultados, a exemplo abaixo:

```
Processing CSV files: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████| 40/40 [00:00<00:00, 4302.51it/s]
Average time for client response (Before 60 seconds)    : 0.043 - 29 errors
Average time for client response (60 - 240 seconds)      : 0.698 - 1991 errors
Average time for client response (After 240 seconds)     : 0.013 - 0 errors
Experiment analyzer finished
```

Neste caso, a latência média no periodo pré-ataque foi de 0.043 segundos (43ms) e existiram 29 erros de conectividade. Já durante o ataque há uma latência média de aproximadamente 700ms e foram registrados 1991 erros de conectividade.


# (BONUS) MQTT

Para analisar tráfego MQTT no testbed você pode utilizar o comando abaixo:

```
MY_ATTACK_START=60
MY_ATTACK_END=240
MY_EXP_FILE=experiment_847.tar.gz
cp ~/Downloads/$MY_EXP_FILE .
sudo docker run --rm -it \
    -v .:/app ghcr.io/khalilsantana/dataset-mentored-iot-2024 \
    python3 /app/scripts/clients-analysis/mqtt.py \
../../$MY_EXP_FILE --attack-start $MY_ATTACK_START --post-attack $MY_ATTACK_END -n 1
```