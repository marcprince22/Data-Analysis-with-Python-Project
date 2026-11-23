# %%
import pandas as pd

PATH = "C:/Users/marcp/Data-Analysis-with-Python-Project/"

income = pd.read_excel(
    PATH + "data/raw_data/socioeconomic_factors/Einkommen.xls",
    sheet_name="Gemeinden",
    header=None,
    skiprows=4,
    nrows=2324,  # not reading footer note
    usecols=[1, 2, 7, 9, 10]
)

income.columns = ["Municipality", "GDENR",
                  "Taxable_Population_2015", "Median_2015", "Gini_2015"]
income.head()
# %%
corr = pd.read_csv(
    PATH + "data/raw_data/geographic_reference/bfs_municipalities/BFS_Gemeindekorrespondenz_2015-2026.csv")
print(corr["InitialCode"].nunique())  # Municipalities 2015
print(corr["TerminalCode"].nunique())  # Municipalities 2026

corr.head()

# %%
corr = corr[["InitialCode", "TerminalCode"]]

income = income.merge(corr, how="left", left_on="GDENR",
                      right_on="InitialCode")
print(income["TerminalCode"].isnull().sum())
income.head()
# %%
values = ["Median_2015", "Gini_2015"]

# creating weighted values for Median and Gini by multiplying them with the Taxable_Population_2015
# This is an approximation, as the Median and Gini are not linear measures, but it is the best we can do with the data we have.
for col in values:
    income[col] = income[col] * income["Taxable_Population_2015"]

# sum up by 2026 municipalities
numbers = ["Taxable_Population_2015"] + values
income_new = income.groupby("TerminalCode")[numbers].sum(skipna=False)

# back to Median and Gini by dividing the weighted values by the Taxable_Population_2015
for col in values:
    income_new[col] = income_new[col] / income_new["Taxable_Population_2015"]

income_new.head()

# %%
income_new.index.name = "MUNNR"
income_new.to_csv(PATH + "data/clean_data/income_gdenr_2026.csv")
print(income_new.shape)  # 2110 is correct
# %%
