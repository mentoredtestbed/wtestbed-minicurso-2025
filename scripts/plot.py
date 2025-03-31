import pandas as pd
import matplotlib.pyplot as plt
import glob

# Load all CSV files in the current directory
csv_files = glob.glob("*.csv")

dataframes = []
for file in csv_files:
    df = pd.read_csv(file)
    df['Source'] = file  # Add a column to identify the source file
    dataframes.append(df)

# Combine all dataframes
combined_df = pd.concat(dataframes)

# Plot settings
plt.figure(figsize=(10, 6))

# Plot AUC with standard deviation
for source, df in combined_df.groupby('Source'):
    plt.errorbar(df['Train data ratio'], df['AUC'], yerr=df['STD AUC'], label=f"AUC - {source}", capsize=5, marker='o', linestyle='--')

plt.xlabel("% Dataset Utilizado no treino")
plt.ylabel("AUC")
plt.title("AUC com Desvio Padrão")
plt.legend()
plt.grid(False)
# plt.show()
plt.savefig("AUC_STD.png")

# Plot F1-Score with standard deviation
plt.figure(figsize=(10, 6))
for source, df in combined_df.groupby('Source'):
    plt.errorbar(df['Train data ratio'], df['F1-Score'], yerr=df['STD F1-Score'], label=f"F1-Score - {source}", capsize=5, marker='s', linestyle='--')

plt.xlabel("% Dataset Utilizado no treino")
plt.ylabel("F1-Score")
plt.title("F1-Score com Desvio Padrão")
plt.legend()
plt.grid(False)
# plt.show()
plt.savefig("F1-Score_STD.png")


# Plot Precision with standard deviation
plt.figure(figsize=(10, 6))
for source, df in combined_df.groupby('Source'):
    plt.errorbar(df['Train data ratio'], df['Precision'], yerr=df['STD Precision'], label=f"Precision - {source}", capsize=5, marker='s', linestyle='--')

plt.xlabel("% Dataset Utilizado no treino")
plt.ylabel("Precision")
plt.title("Precision com Desvio Padrão")
plt.legend()
plt.grid(False)
# plt.show()
plt.savefig("Precision_STD.png")

# Plot Precision with standard deviation
plt.figure(figsize=(10, 6))
for source, df in combined_df.groupby('Source'):
    plt.errorbar(df['Train data ratio'], df['Recall'], yerr=df['STD Recall'], label=f"Recall - {source}", capsize=5, marker='s', linestyle='--')

plt.xlabel("% Dataset Utilizado no treino")
plt.ylabel("Recall")
plt.title("Recall com Desvio Padrão")
plt.legend()
plt.grid(False)
# plt.show()
plt.savefig("Recall_STD.png")

# Sumarize/round, each value in the csv and output a markdown table of them
for df in dataframes:
    df = df.round(3)
    markdown_table = df.to_markdown(index=False)
    print(markdown_table)

