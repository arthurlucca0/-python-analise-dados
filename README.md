# Fintech - Pipeline de Transações e Detecção de Anomalias

Aplicação em Python/Pandas criada para limpar, transformar, consolidar e analisar dados financeiros gerados pelo script `criar_dados.py`.

## Requisitos atendidos

- Leitura de `transacoes.csv` com `encoding="latin1"`.
- Imputação dos valores ausentes de `valor` pela **mediana por estado**.
- Criação da coluna estática `plataforma = "Mobile"`.
- Conversão de `data_transacao` para `datetime64[ns]` e aplicação do fuso `America/Sao_Paulo`.
- Criação das colunas `dia_semana` e `mes` com o acessor `.dt`.
- Remoção de duplicatas mantendo a primeira ocorrência.
- Filtro vetorizado com operadores bitwise `&` e `|` para:
  - mês de setembro;
  - estado SP ou RJ;
  - valor acima de R$ 5.000.
- Mapeamento de risco por cliente com `.map()`.
- `pivot_table` por mês e nível de risco com `margins=True`.
- Cálculo vetorizado do Z-Score por estado, sem laço `for`.
- Identificação de potenciais anomalias com `Z-Score > 2.5`.
- Gráfico Matplotlib usando a API orientada a objetos (`fig, ax = plt.subplots()`).
- Série do total diário e média móvel de 7 dias com `.rolling(7).mean()`.
- Eixo Y iniciado em zero com `ax.set_ylim(bottom=0)`.
- Consolidação complementar das transações com `cotacoes.csv` pela data.

## Estrutura

```text
fintech_analise_github/
├── app.py
├── criar_dados.py
├── requirements.txt
├── README.md
├── .gitignore
└── output/
```

Após a execução, a pasta `output/` recebe:

- `transacoes_tratadas.csv`
- `filtro_setembro_sp_rj_maior_5000.csv`
- `pivot_risco.csv`
- `anomalias_zscore.csv`
- `transacoes_com_cotacao.csv`
- `serie_diaria_media_movel.csv`
- `relatorio_transacoes.png`

## Como executar

### 1. Clone o repositório

```bash
git clone URL_DO_SEU_REPOSITORIO
cd fintech_analise_github
```

### 2. Crie um ambiente virtual

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Gere os dados

```bash
python criar_dados.py
```

O script cria `transacoes.csv` e `cotacoes.csv`.

### 5. Execute a aplicação

```bash
python app.py
```

Os resultados serão salvos automaticamente na pasta `output/`.

## Dicionário de risco usado

```python
RISCO_DICT = {
    "C100": "Baixo",
    "C101": "Alto",
    "C102": "Médio",
    "C103": "Baixo",
    "C104": "Alto",
}
```

Caso o professor forneça outro dicionário, basta alterar a constante `RISCO_DICT` no início de `app.py`.

## Envio pelo GitHub

Exemplo de comandos:

```bash
git init
git add .
git commit -m "Entrega do projeto de análise de transações"
git branch -M main
git remote add origin URL_DO_SEU_REPOSITORIO
git push -u origin main
```

> Substitua `URL_DO_SEU_REPOSITORIO` pelo endereço do seu repositório no GitHub.
