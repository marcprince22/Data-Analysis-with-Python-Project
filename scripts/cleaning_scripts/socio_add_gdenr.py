# %%
import pandas as pd

# %%
# loading the Data
PATH = "C:/Users/marcp/Data-Analysis-with-Python-Project/"
socio = pd.read_csv(PATH + "data/clean_data/socioeconomics_factors.csv")
corr = pd.read_csv(
    PATH + "data/raw_data/geographic_reference/bfs_municipalities/BFS_Gemeindekorrespondenz_2021-2026.csv")

socio.head()
corr.head()


# %%
# take out observations that are older then 2015
# load appendix
appendix = pd.read_csv(
    PATH + "data/clean_data/socioeconomics_factors_APPENDIX.csv")

# take out last year "2004/2009" -> 2009
appendix["last_year"] = appendix["year"].str[-4:].astype(int)

# only keep the younger than 2015
recent = appendix[appendix["last_year"] >= 2010]
print(recent)
print(appendix[appendix["last_year"] < 2010][["ind_description", "year"]])


# %%
# taking them out from socio
columns = ["Community"] + list(recent["ind_description"])
socio = socio[columns]
socio.head(10)


# %%
# Chosen Variables (explenation in report)
columns = [
    "Community",
    "Population - Residents",
    "Population - Share of age group 0-19 years",
    "Population - Share of age group 65+ years",
    "Population - Foreign nationals",
    "Social security - Social assistance rate",
    "Economy - Employed, total",
    "Economy - Employed, primary sector",
    "Area - Area, total"
]

socio = socio[columns]
print(socio.shape)
print(socio.head)

# %%
# only taking 3 column we are interested
corr = corr[["TerminalName", "TerminalCode", "InitialName"]]
corr.head()


# %%
socio = socio.merge(corr, how="left", left_on="Community",
                    right_on="InitialName")
socio.head()

# %%
print(socio[["Community", "TerminalCode", "TerminalName"]].head(15))
socio["TerminalCode"].isna().sum()  # Municipalities without code


# %%
print(len(socio))
# have different lenth since some municiplaities merged
print(socio["TerminalCode"].nunique())


# -------Merge Communities socioeconomics factors to fit with Elections Data---------------------

# %%
# columns that are proportions in % -> can't be added up but weigthed

proportions = [
    "Population - Share of age group 0-19 years",
    "Population - Share of age group 65+ years",
    "Population - Foreign nationals",
    "Social security - Social assistance rate",
]

# change to absolute values to be able to add up
for column in proportions:
    socio[column] = socio[column] * socio["Population - Residents"] / 100


# %%
# taking all columns appart of communities
numbers = columns[1:]

# For every terminalcode create a group with corresponding values and sum them up.
socio_new = socio.groupby("TerminalCode")[numbers].sum(skipna=False)

print(socio_new)

# %%
# change back to proportions
for column in proportions:
    socio_new[column] = socio_new[column] / \
        socio_new["Population - Residents"] * 100

socio_new.head(10)

# %%
# recalculate the population density and proportions working sector 1.
socio_new["Population density"] = socio_new["Population - Residents"] / \
    socio_new["Area - Area, total"]
socio_new["Share primary sector"] = socio_new["Economy - Employed, primary sector"] / \
    socio_new["Economy - Employed, total"] * 100
# check for Brugg (4095) if the values are correct
socio_new.loc[4095]
# %%
# change name of index
socio_new.index.name = "BFS_NR"

# save as csv
socio_new.to_csv(PATH + "data/clean_data/socio_comnr_2026.csv", index=True)
