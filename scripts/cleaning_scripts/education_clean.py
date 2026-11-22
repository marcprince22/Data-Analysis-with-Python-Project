# %%
import pandas as pd

PATH = "C:/Users/marcp/Data-Analysis-with-Python-Project/"

# %%
educ = pd.read_csv(
    PATH + "data/raw_data/socioeconomic_factors/education_factors.csv", sep=";")
educ.head()

# %%
# Keeping only the columns we are interested in
columns = [
    "GDENR",
    "BBTOT25_64",
    "COMPULSORY",
    "SECONDARYII",
    "TERTIARY",
    "IMPUTATION"
]

educ = educ[columns]
educ.head()
# %%
corr = pd.read_csv(
    PATH + "data/raw_data/geographic_reference/bfs_municipalities/BFS_Gemeindekorrespondenz_2021-2026.csv")
corr = corr[["InitialCode", "TerminalCode"]]

educ = educ.merge(corr, how="left", left_on="GDENR", right_on="InitialCode")
print(educ["TerminalCode"].isnull().sum())
# 14 communities were created after 2021 and therefore have no TerminalCode. We will use the GDENR as the code for 2026 for these communities.
# %%
# if terminalCode is null, use GDENR as the code for 2026
educ["GDENR_2026"] = educ["TerminalCode"].fillna(educ["GDENR"]).astype(int)

print(educ["GDENR_2026"].nunique())
educ.head()

# %%
proportion_columns = ["COMPULSORY", "SECONDARYII", "TERTIARY", "IMPUTATION"]

# calculate in absolute numbers the proportion columns by multiplying them with the total number of people aged 25-64 and dividing by 100
for col in proportion_columns:
    educ[col] = educ[col] * educ["BBTOT25_64"] / 100

values = ["BBTOT25_64"] + proportion_columns

# sum the values by GDENR_2026
educ_new = educ.groupby("GDENR_2026")[values].sum(skipna=False)

educ_new.head()
# %%
# calulating back to proportions

for col in proportion_columns:
    educ_new[col] = educ_new[col] / educ_new["BBTOT25_64"] * 100

educ_new.loc[4095]
# %%

educ_new.index.name = "GDENR"
educ_new.head()
educ_new.to_csv(PATH + "data/clean_data/education_gdenr_2026.csv")
# %%
