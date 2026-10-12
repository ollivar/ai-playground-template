# %%
import pandas as pd

data = {
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [25, 30, 35],
    "City": ["New York", "Los Angeles", "Chicago"],
}

df = pd.DataFrame(data)
print(df)

df.head(2)

# %%

print("Hello from Jupyter!")

var1 = 55
var3 = 5.4
print(var1 + var3)

df.replace("Alice", "Booger")
# %%
