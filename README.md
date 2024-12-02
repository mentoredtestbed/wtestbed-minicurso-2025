# Guia de Experimentos IoT - MENTORED TESTBED 2024

> [!IMPORTANT]
> É recomendado a leitura dos [tutoriais](https://portal.mentored.ccsc-research.org/tutorial/pt/) do projeto primeiramente. Além disso recomenda-se como ferramentas o Wireshark, um editor de texto como VSCode, assim como um leitor de arquivos compactados como 7zip ou Peazip.


## Objetivos

1. Familiarizar o leitor com o MENTORED _testbed_

2. Executar experimentos pré-existentes

3. Examinar dados coletados para avaliar a efetividade dos ataques performados

### Cenário 1) Ataque Slowloris / Hello World

Esse cenário, descrito em `Cenario1.yaml` pretende demonstrar o funcionamento básico do testbed, sendo de rápida execução e fácil análise.
#### Entidades

1) Servidor Web Apache: servindo uma página Web estática para clientes via HTTP 1.1

2) Clientes Web: um cliente HTTP 1.1 escrito em Python 3 executando requisições periódicas ao servidor web

3) Atacante: um nó realizando o ataque de negação de serviço Layer 7 (camada de aplicação) denominado Slowloris contra o servidor Web

#### Fluxo / Timeline

* Duração 300 segundos
* [0-59s] Clientes legítimos realizam requisições normalmente contra o servidor Web

* [60-240s] Atacante performa um ataque durando 180s contra o servidor

* [240-300s] Apenas clientes legítimos e o servidor Web estão ativos

#### Dados coletados por entidade

* Todos:
  
  * Logs do script de inicialização
  
  * IPs de cada nó
  
  * Tempo de inicialização do experimento

* Servidor Web:
  
  * Captura de tráfego de rede
  
  * Logs do Apache 2

* Cliente:
  
  * CSV contando a latência de cada requisição ou um erro demarcando falha na conexão

* Atacante:
  
  * Registro (timestamp) do início e fim do ataque

#### Resultados esperados

* Funcionamento normal pré-ataque

* Experiência de acesso dos clientes degradada, demonstrada pela elevação no tempo de resposta elevado durante o ataque

* Restauração parcial ou total da conectividade dos clientes

#### Executando o ataque

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

8) Aguarde o período de Warm-up finalizar (~30 segundos), e em seguida clique no ícone de monitor para inspecionar a execução do experimento. Nessa tela, busque o cliente, clique para selecionar o mesmo, e então no terminal criado execute o comando para ver o conteúdo do arquivo de log sendo gerado: `tail -f /app/result/client_delay.csv`

![alt text](img/Criação-de-Experimento-06.png)

![alt text](img/Criação-de-Experimento-07.png)

9) (Opcional) Observe os outros nós durante a execução do experimento, notando que a pasta raiz (`/`) e a pasta de resultados (`/app/results`) contem arquivos de interesse normalmente.

10) Com o experimento finalizado (demarcado pelo sinal de 100%), baixe os arquivos gerados por aquela execução. 

![alt text](img/Criação-de-Experimento-08.png)


#### Analisando os dados

A estrutura do arquivo de experimentação anteriormente baixado é a seguinte:

```
.
├── attacker-http
│   └── attacker-http-0_attacker.tar
├── client-http
│   ├── client-http-0_client-static.tar
│   ├── client-http-1_client-static.tar
│   ├── client-http-2_client-static.tar
│   ├── client-http-3_client-static.tar
│   ├── client-http-4_client-static.tar
│   ├── client-http-5_client-static.tar
│   ├── client-http-6_client-static.tar
│   ├── client-http-7_client-static.tar
│   ├── client-http-8_client-static.tar
│   └── client-http-9_client-static.tar
├── experiment_logs_844.tar
├── MENTORED_IP_LIST.json
├── MENTORED_IP_LIST.yaml
├── MENTORED_READY.txt
└── server-http
    ├── server-http-0_server.tar
    └── server-http-0_tshark.tar
```

Isto é, cada entidade (node-actor) é uma pasta, e dentro desta cada réplica da entidade possui um arquivo TAR associado. Além disso os logs da aplicação principal (PID1) de cada experimento está no arquivo `experiment_logs_xxx.tar`. Por fim, o timestamp de quando o experimento finaliza o warmup está em MENTORED_READY.txt e os IPs de cada entidade estão em `MENTORED_IP_LIST.yaml`. 

Desta maneira, para analisar a efetividade do ataque basta abrir o arquivo TAR associado a um cliente, por exemplo `client/client-http-0_client-static.tar`está associado a primeira réplica do node-actor `client`. Dentro deste arquivo há dois arquivos de interesse: o `MENTORED_REGISTRY.yaml` e o `client_delay.csv`, contendo respectivamente o timestamp de início das requisições e a latência de acesso à página servida pelo servidor.

Como o cliente está programado para realizar uma requisição a cada segundo, espera-se que entre 60 à 240 segundos haja uma degradação do serviço. E de fato, por exemplo, por latências elevadas na segunda coluna de `client_delay.csv` ou mesmo erros ao acessar a página. Por exemplo, o trecho abaixo demonstra esta degradação:


|time|delay (seconds)|
|----|----|
|53.9360294342041|0.013|
|54.94859051704407|0.012|
|55.961687088012695|0.013|
|61.97136688232422|ERROR:timed out|
|67.98534560203552|ERROR:timed out|
|73.99811601638794|ERROR:timed out|
|80.00763893127441|ERROR:timed out|
|[...]|[...]|
|218.30777311325073|ERROR:timed out|
|224.31763625144958|ERROR:timed out|
|230.3426206111908|ERROR:timed out|
|235.40070056915283|4.058|
|236.41171741485596|0.010|
|237.42081928253174|0.009|


Notando que a execução iniciada no segundo 235 foi respondida 4 segundos após, ou seja, aproximadamente 240s a partir do início do experimento, coincidindo com o período onde o ataque é finalizado. Também é possível analisar os registros de cada cliente utilizando os scripts em `scripts/client-analysis` ([baseados no minicurso 2024 SBRC](https://github.com/mentoredtestbed/minicurso-sbrc-2024-testbeds)). Além disso, experimente analisar estes e co-relacionar os mesmos, como observar o tráfego de um node actor até o servidor, o início das requisições de cada nó, etc. 

Por fim, experimente repetir execuções do experimento para verificar sua reprodutibilidade, ou modifique parâmetros do experimento como o número de réplicas de entidades, seu posicionamento, o comando de ataque executado (recomenda-se a leitura das imagens Docker em `docker-images`), etc.

### Cenário 2) Ataque DDoS Layer3 volumétrico

# TODO