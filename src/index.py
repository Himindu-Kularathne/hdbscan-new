import pandas as pd

path = "data/monolithic/jpetstore-6/semantic_data/class_word_count.parquet"
df = pd.read_parquet(path)

print("columns:", df.columns.tolist())
print("index name:", df.index.name)
print("index sample:", list(df.index[:10]))

df2 = df.reset_index()
print("reset_index columns:", df2.columns.tolist())
print(df2.head(3))
