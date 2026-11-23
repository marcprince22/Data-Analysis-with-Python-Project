# %%

import pandas as pd
PATH = "../../"

columns = ["GDENR", "Beteiligung in %", "Jahr", "Datum", "Rechtsform_Code",
           "Geografietyp", "Sonderfall", "Stimmberechtigte"]

turnout = pd.read.csv(
    PATH + "data/clean_data/voting_turnout_swissvotes_joined.csv.zip"
    usecols=columns
    low_memory=False
)

turnout.head()
# %%
