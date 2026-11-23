# %%
import pandas as pd
PATH = "../../"

# %%

# Load the four prepared datasets 
turnout = pd.read_csv(PATH + "data/clean_data/turnout_gdenr_2026.csv")
socio = pd.read_csv(PATH + "data/clean_data/socio_comnr_2026.csv")
education = pd.read_csv(PATH + "data/clean_data/education_gdenr_2026.csv")
income = pd.read_csv(PATH + "data/clean_data/income_gdenr_2026.csv")

# look at data shape
for df in [turnout, socio, education, income]:
    print(df.shape)
    print(df.head())
# %%
# merge the datasets on GDENR
data = turnout.merge(socio, on="GDENR", how="left")
data = data.merge(education, on="GDENR", how="left")
data = data.merge(income, on="GDENR", how="left")
data.shape # (2110, 21)

# %%
#shorter english name columns

data = data.rename(columns={
    "Population - Residents": "population",
    "Population - Share of age group 0-19 years": "share_age_0_19",
    "Population - Share of age group 65+ years": "share_age_65plus",
    "Population - Foreign nationals": "share_foreign",
    "Social security - Social assistance rate": "social_assistance_rate",
    "Population density": "population_density",
    "Share primary sector": "share_primary_sector",
    "TERTIARY": "share_tertiary",
    "Median_2015": "income_median",
    "Gini_2015": "income_gini",
    "Kanton": "canton"
})

# %%
# keep only variables for the analysis
keep = ["GDENR", "turnout_mean", "n_votes",
        "population", "population_density",
        "share_age_0_19", "share_age_65plus", "share_foreign",
        "share_primary_sector", "share_tertiary",
        "income_median", "income_gini", "social_assistance_rate", "canton"]
data = data[keep]

print(data.shape)  # (2110, 13
data.head()
# %%
print(data.isna().sum())
# %%
data.to_csv(PATH + "data/clean_data/regression_data.csv", index=False)

