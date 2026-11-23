# %%

import pandas as pd
PATH = "../../"

columns = ["GDENR", "Beteiligung in %", "Jahr", "Datum", "Rechtsform_Code",
           "Geografietyp", "Sonderfall", "Stimmberechtigte"]

turnout = pd.read_csv(
    PATH + "data/clean_data/voting_turnout_swissvotes_joined.csv.zip",
    usecols=columns,
    low_memory=False
)

turnout.head()
# %%
# only want to keep municipalities and not special cases
turnout = turnout[(turnout["Geografietyp"] == "Gemeinde") & (turnout["Sonderfall"] == False)]

# change '...' to NaN
turnout["Beteiligung"] = pd.to_numeric(turnout["Beteiligung in %"], errors="coerce") # coerce will turn non-numeric values into NaN

# data missing
print(turnout.shape)
print(turnout["Beteiligung"].isna().sum())
# %%
# taking 2015-2013
turnout = turnout[(turnout["Jahr"] >= 2015) & (turnout["Jahr"] <= 2023)]
print(turnout.shape)



# %%
turnout_mean = turnout.groupby("GDENR")["Beteiligung"].agg(["mean", "count"])
turnout_mean.head()

# %%
# rename to english
turnout_mean.columns = ["turnout_mean", "n_votes"]

turnout_mean.index = turnout_mean.index.astype(int)

print(turnout_mean.head())

# %%
turnout_mean.to_csv(PATH + "data/clean_data/turnout_gdenr_2026.csv")
# %%
