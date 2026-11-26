
# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
PATH = "../../"

data = pd.read_csv(PATH + "data/clean_data/regression_data.csv")
data.describe()

#%% 
# historgram of the target variable
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(data["turnout_mean"], bins=30, edgecolor="white")
ax.axvline(data["turnout_mean"].mean(), color="red", linestyle="--", label="Mean")

ax.set_xlabel("Average turnout 2015-2023 (%)")
ax.set_ylabel("Number of municipalities")
ax.set_title("Distribution of voter turnout across Swiss municipalities")
ax.legend()
fig.savefig(PATH + "figures/hist_turnout.png", dpi=150, bbox_inches="tight")
plt.show()

# most municipalities have a turnout between 40% and 60%, with a mean of 50.2%. There are some municipalities with a turnout above 70%, which are outliers.
# the distribution is slightly right skewed, whith a long tail of municipalities with a turnout above 65%. 


# %%
# search for outliers
outliers = data[data["turnout_mean"] > 70]
print(outliers[["GDENR", "turnout_mean", "canton"]])
# why are alomst every one from Schaffhausen?

# %%
# compare canton with a boxplot
#sorts cantons by median turnout
order = data.groupby("canton")["turnout_mean"].median().sort_values().index

#creats a list for list with turnout values for each canton
groups = []
for canton in order:
    groups.append(data.loc[data["canton"] == canton, "turnout_mean"].dropna())

#plot it in the boxplot
fig, ax = plt.subplots(figsize=(9, 9))
ax.boxplot(groups, tick_labels=order, orientation="horizontal")
ax.set_xlabel("Average turnout 2015-2023 (%)")
ax.set_title("Voter turnout by canton")
fig.savefig(PATH + "figures/boxplot_turnout_canton.png", dpi=150, bbox_inches="tight")
plt.show()
# %%
#  divide turnout into two groups: Schaffhausen and the rest of Switzerland
sh = data[data["canton"] == "Schaffhausen"]["turnout_mean"]
rest = data[data["canton"] != "Schaffhausen"]["turnout_mean"].dropna()

fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(rest, bins=40, edgecolor="white", label="Other cantons")
ax.hist(sh, bins=10, edgecolor="white", color="orange", label="Schaffhausen (compulsory voting)")
ax.set_xlabel("Average turnout 2015-2023 (%)")
ax.set_ylabel("Number of municipalities")
ax.set_title("Schaffhausen explains most of the high-turnout tail")
ax.legend()
fig.savefig(PATH + "figures/hist_turnout_schaffhausen.png", dpi=150, bbox_inches="tight")
plt.show()
# %%
# %%
# Distributions of all explanatory variables
variables = ["population", "population_density", "share_age_0_19", "share_age_65plus",
             "share_foreign", "share_primary_sector", "share_tertiary",
             "income_median", "income_gini", "social_assistance_rate"]

fig, axes = plt.subplots(nrows=2, ncols=5, figsize=(16, 6))
axes = axes.flatten()

for i, var in enumerate(variables):
    axes[i].hist(data[var].dropna(), bins=40, edgecolor="white")
    axes[i].set_title(var)

fig.suptitle("Distributions of the explanatory variables")
fig.tight_layout()
fig.savefig(PATH + "figures/hist_explanatory_variables.png", dpi=150, bbox_inches="tight")
plt.show()

# Some extreme outliers in population and population density might have a strong influence on the regression results.
# create log for population
data["log_population"] = np.log(data["population"])
# create log for population density
data["log_population_density"] = np.log(data["population_density"])
# %%
#scatter plots of explanatory variables against turnout

# define newe 
fig, axes = plt.subplots(nrows=2, ncols=5, figsize=(18, 7), sharey=True)
axes = axes.flatten()
for i, var in enumerate(variables):
    axes[i].scatter(rest[var], rest["turnout_mean"], s=5, alpha=0.3, label="Other cantons")
    axes[i].scatter(sh[var], sh["turnout_mean"], s=8, color="orange", label="Schaffhausen")
    axes[i].set_xlabel(var)
axes[0].set_ylabel("Average turnout (%)")
axes[5].set_ylabel("Average turnout (%)")
axes[0].legend()
fig.suptitle("Voter turnout vs. explanatory variables")
fig.tight_layout()
fig.savefig(PATH + "figures/scatter_turnout_variables.png", dpi=150, bbox_inches="tight")
plt.show()
# %%
