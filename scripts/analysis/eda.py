
# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PATH = "../../"

data = pd.read_csv(PATH + "data/clean_data/regression_data.csv")
data.describe()

# %%
# historgram of the target variable
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(data["turnout_mean"], bins=30, edgecolor="white")
ax.axvline(data["turnout_mean"].mean(), color="red",
           linestyle="--", label="Mean")

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
# sorts cantons by median turnout
order = data.groupby("canton")["turnout_mean"].median().sort_values().index

# creats a list for list with turnout values for each canton
groups = []
for canton in order:
    groups.append(data.loc[data["canton"] == canton, "turnout_mean"].dropna())

# plot it in the boxplot
fig, ax = plt.subplots(figsize=(9, 9))
ax.boxplot(groups, tick_labels=order, orientation="horizontal")
ax.set_xlabel("Average turnout 2015-2023 (%)")
ax.set_title("Voter turnout by canton")
fig.savefig(PATH + "figures/boxplot_turnout_canton.png",
            dpi=150, bbox_inches="tight")
plt.show()
# %%
#  divide turnout into two groups: Schaffhausen and the rest of Switzerland
sh = data[data["canton"] == "Schaffhausen"]["turnout_mean"]
rest = data[data["canton"] != "Schaffhausen"]["turnout_mean"].dropna()

fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(rest, bins=40, edgecolor="white", label="Other cantons")
ax.hist(sh, bins=10, edgecolor="white", color="orange",
        label="Schaffhausen (compulsory voting)")
ax.set_xlabel("Average turnout 2015-2023 (%)")
ax.set_ylabel("Number of municipalities")
ax.set_title("Schaffhausen explains most of the high-turnout tail")
ax.legend()
fig.savefig(PATH + "figures/hist_turnout_schaffhausen.png",
            dpi=150, bbox_inches="tight")
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
fig.savefig(PATH + "figures/hist_explanatory_variables.png",
            dpi=150, bbox_inches="tight")
plt.show()

# Some extreme outliers in population and population density might have a strong influence on the regression results.
# create log for population
data["log_population"] = np.log(data["population"])
# create log for population density
data["log_population_density"] = np.log(data["population_density"])
# %%
# scatter plots of explanatory variables against turnout

variables = ["log_population", "log_population_density", "share_age_0_19", "share_age_65plus",
             "share_foreign", "share_primary_sector", "share_tertiary",
             "income_median", "income_gini", "social_assistance_rate"]

sh = data[data["canton"] == "Schaffhausen"]
rest = data[data["canton"] != "Schaffhausen"]


fig, axes = plt.subplots(nrows=2, ncols=5, figsize=(18, 7), sharey=True)
axes = axes.flatten()
for i, var in enumerate(variables):
    axes[i].scatter(rest[var], rest["turnout_mean"], s=5,
                    alpha=0.3, label="Other cantons")
    axes[i].scatter(sh[var], sh["turnout_mean"], s=8,
                    color="orange", label="Schaffhausen")
    axes[i].set_xlabel(var)
axes[0].set_ylabel("Average turnout (%)")
axes[5].set_ylabel("Average turnout (%)")
axes[0].legend()
fig.suptitle("Voter turnout vs. explanatory variables")
fig.tight_layout()
fig.savefig(PATH + "figures/scatter_turnout_variables.png",
            dpi=150, bbox_inches="tight")
plt.show()
# %%
# creating a correlation matrix for the explanatory variables
corr_variables = ["turnout_mean"] + variables
corr = data[corr_variables].corr()

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)

ax.set_xticks(range(len(corr_variables)))
ax.set_xticklabels(corr_variables, rotation=45, ha="right")
ax.set_yticks(range(len(corr_variables)))
ax.set_yticklabels(corr_variables)

for i in range(len(corr_variables)):
    for j in range(len(corr_variables)):
        ax.text(j, i, round(corr.iloc[i, j], 2),
                ha="center", va="center", fontsize=8)

fig.colorbar(im, ax=ax, label="Correlation")
ax.set_title("Correlation matrix")
fig.tight_layout()
fig.savefig(PATH + "figures/correlation_matrix.png",
            dpi=150, bbox_inches="tight")
plt.show()

# as we saw in the scatter plots turnout and share_tertiary are highly correlated, which is also reflected in the correlation matrix.
# Risk of Multicollinearity in the regression model. (share_age_0_19 and share_age_65plus) (log_population and log_population_density) (log_population and share_primary_sector), (share_tertiary and income_median)
# %%
