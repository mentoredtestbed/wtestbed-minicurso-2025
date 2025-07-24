#  Atividades Práticas em Cibersegurança com o Testbed Mentored do Projeto MENTORED: Da Modelagem à Experimentação - Predizendo e detectando ataques DDoS e zero-day

> A seguir são descritos os passos necessários para reproduzir e analisar os experimentos realizados no MENTORED Testbed executados no WTESTBEDS 2025

## Objetivos

1. Familiarizar o leitor com o MENTORED _testbed_

2. Exemplificar uma análise os resultados de um experimento executado no MENTORED Testbed

3. Examinar dados coletados para avaliar a efetividade dos ataques performados

3.1. Identificar a disponibilidade de serviço observada pelo cliente antes, durante e depois do ataque
3.2. Comparar a vazão do tráfego de rede com a quantidade de requisições HTTP observadas durante expierimento.
3.3. Utilizar o arquivo de tráfego de rede e os logs estruturados com registros de atividades para criar um dataset rotulado, e avaliar algoritmos de aprendizado de máquina para implementar sistemas de intrusão de detecção no cenário explorado.


## Instalando dependências

A seguir, serão instaladas as bibliotecas `evalml`, `scipy`, `pandas` e `numpy`, que serão utilizadas para analisar os dados coletados.

## Ataque Slowloris

O experimento executado no MENTORED Testbed consiste em um ataque de negação de serviço (DoS) denominado Slowloris, o qual é um ataque de camada 7 (camada de aplicação) que visa manter conexões HTTP abertas por longos períodos, esgotando os recursos do servidor web e impedindo que clientes legítimos acessem o serviço. No experimento, 16 atacantes foram utillizados para simular um ataque DDoS de uma botnet contra um servidor web Apache, enquanto clientes legítimos realizam requisições periódicas ao servidor.

### Entidades

1) Servidor Web Apache: servindo uma página Web estática para clientes via HTTP 1.1

2) Clientes Web: um cliente HTTP 1.1 escrito em Python 3 executando requisições periódicas ao servidor web

3) Atacante: um nó realizando o ataque de negação de serviço Layer 7 (camada de aplicação) denominado Slowloris contra o servidor Web

### Fluxo / Timeline

* Duração 300 segundos
* [0-59s] Clientes legítimos realizam requisições normalmente contra o servidor Web

* [120-180s] Atacantes performam um ataque durando 60s contra o servidor

* [180-300s] Apenas clientes legítimos e o servidor Web estão ativos


### Dados coletados por entidade

* Todos:
  
  * Logs do script de inicialização (arquivo `experiment_logs_<xyz>.tar`)
  
  * IPs de cada nó (`MENTORED_IP_LIST.yaml`)
  
  * Tempo de inicialização do experimento (`MENTORED_READY.txt`)

  * Definição usada para executar o experimento (`EXPERIMENT_DEFINITION_EXECUTION_X.yaml`)

* Servidor Web:
  
  * Captura de tráfego de rede (`/app/results/packets.pcapng`, arquivo assim como arquivo `hosts` na mesma pasta)
  
  * Logs do Apache 2 (`/app/results/access.log` e `error.log` na mesma pasta)

* Cliente:

  * Registro (timestamp) do início das requisições(`/app/results/MENTORED_REGISTRY.yaml`)
  
  * CSV contando a latência de cada requisição ou um erro demarcando falha na conexão (`/app/results/client_delay.csv`)

* Atacante:
  
  * Registro (timestamp) do início e fim do ataque (`/app/results/MENTORED_REGISTRY.yaml`)


## Analisando os dados

A estrutura do arquivo de experimentação anteriormente baixado é a seguinte:

```
.
├── generic-botnet
|   ├── generic-botnet-0_botnet.tar
│    ...
│   └── generic-botnet-15_botnet.tar
├── generic-client
│   └── generic-client-0_client.tar
├── experiment_logs_X.tar
├── EXPERIMENT_DEFINITION_EXECUTION_2112.yaml
├── MENTORED_IP_LIST.json
├── MENTORED_IP_LIST.yaml
├── MENTORED_READY.txt
└── na-server
    ├── na-server-http-0_server.tar
    └── na-server-http-0_tshark.tar
```

Isto é, cada entidade (node-actor) é uma pasta, e dentro desta cada réplica da entidade possui um arquivo TAR associado. Além disso os logs da aplicação principal (PID1) de cada experimento está no arquivo `experiment_logs_xxx.tar`. Por fim, o timestamp de quando o experimento finaliza o warmup está em MENTORED_READY.txt e os IPs de cada entidade estão em `MENTORED_IP_LIST.yaml`. 

Desta maneira, para analisar a efetividade do ataque basta abrir o arquivo TAR associado a um cliente, por exemplo `client/generic-client-0_client-static.tar`está associado a primeira réplica do node-actor `client`. Dentro deste arquivo há dois arquivos de interesse: o `MENTORED_REGISTRY.yaml` e o `client_delay.csv`, contendo respectivamente o timestamp de início das requisições e a latência de acesso à página servida pelo servidor.



Para gerar as análises que usam intrusão de detecção, vamos usar o script `ml_analysis.py` para gerar os arquivos de saída.


Esse comando irá inserir utilizar cada base de dados para criar um problema de Intrusão de Detecção, utilizando a biblioteca EvalML para gerar os modelos de Machine Learning. Para cada base de dados, diferentes valores de f1-score, acurácia, precisão e recall são gerados considerando diferentes proporções de dados de treinamento, o que é representado em um gráfico onde o eixo x representa a proporção de dados de treinamento e o eixo y representa a métrica utilizada. Além desse gráfico, um arquivo CSV é gerado contendo os resultados de cada execução, a imagem que representa a soma das matrizes de confusão e uma representação bidimensional dos dados de cada base usando o algoritmo t-SNE.














## EXTRA: Executando o experimento no MENTORED Testbed

1) Inspecionar o YAML que define o experimento, notando as imagens em uso, assim como as variáveis de ambiente configuradas.

2) Acessar o Portal do [MENTORED Testbed](https://portal.mentored.ccsc-research.org/), realizar login com o usuário e senhas providos na rede Cafe Expresso

3) Navegar até o projeto pré-criado, criar uma nova definição de experimento

![alt text](img/Criação-de-Experimento-01.png)

4) Crie uma nova definição de experimento

![alt text](img/Criação-de-Experimento-02.png)

5) Crie um nome descritivo como Cenario1-Slowloris e então faça o upload do arquivo de definição de experimento provido (`Cenario1.yaml`)

![alt text](img/Criação-de-Experimento-03.png)

6) Você será retornado a tela anterior, então clique na definição de experimento.

![alt text](img/Criação-de-Experimento-04.png)

7) Instancie o experimento, no multi-cluster Karmada IoT provido e de 300 segundos de duração.


![alt text](img/Criação-de-Experimento-05.png)

8) Aguarde o período de Warm-up finalizar (~30 segundos), e em seguida clique no ícone de monitor para inspecionar a execução do experimento. Nessa tela, busque o cliente, clique para selecionar o mesmo, e então no terminal criado execute o comando para ver o conteúdo do arquivo de log sendo gerado: `tail -f /app/results/client_delay.csv`

![alt text](img/Criação-de-Experimento-06.png)

![alt text](img/Criação-de-Experimento-07.png)

9) (Opcional) Observe os outros nós durante a execução do experimento, notando que a pasta raiz (`/`) e a pasta de resultados (`/app/results`) contem arquivos de interesse normalmente.

10) Com o experimento finalizado (demarcado pelo sinal de 100%), baixe os arquivos gerados por aquela execução. 

![alt text](img/Criação-de-Experimento-08.png)


