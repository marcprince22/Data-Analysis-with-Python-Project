# %%
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
from statsmodels.nonparametric.smoothers_lowess import lowess
PATH = "../../"

data = pd.read_csv(PATH + "data/clean_data/regression_data.csv")

# %%
# Prepare variables for regression
data["log_population"] = np.log(data["population"])
data["log_population_density"] = np.log(data["population_density"])
data["income_median_1000"] = data["income_median"] / 1000 #income in 1000 CHF
data["income_gini_100"] = data["income_gini"] * 100 #gini index in percentage
data["compulsory_voting"] = (data["canton"] == "Schaffhausen").astype(int)

# %% 
# create main regression model
formula = ("turnout_mean ~ share_tertiary + income_median_1000 + income_gini_100"
           " + log_population + log_population_density"
           " + share_age_0_19 + share_age_65plus + share_foreign + share_primary_sector"
           " + compulsory_voting")


model1 = sm.OLS.from_formula(formula, data=data).fit()
with open(PATH + "figures/model1_summary.txt", "w") as f:
    f.write(model1.summary().as_text())
    
    
print(model1.summary())

# %%
# plot residuals of the regression model
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# values we need for the plots
fitted = model1.fittedvalues                      # predicted values
resid = model1.resid                              # residuals
influence = model1.get_influence()
std_resid = influence.resid_studentized_internal  # standardized residuals
leverage = influence.hat_matrix_diag              # leverage of each municipality
cooks = influence.cooks_distance[0]               # Cook's distance

# Residuls vs Fitted -> linearity
ax = axes[0, 0]
ax.scatter(fitted, resid, s=8, alpha=0.4)
smooth = lowess(resid, fitted)
ax.plot(smooth[:, 0], smooth[:, 1], color="red")
ax.axhline(0, color="grey", linestyle="--")
ax.set_xlabel("Fitted values")
ax.set_ylabel("Residuals")
ax.set_title("Residuals vs Fitted")

#Normal Q-Q plot -> normality of residuals
ax = axes[0, 1]
sm.qqplot(std_resid, line="45", ax=ax)
ax.set_ylabel("Standardized residuals")
ax.set_title("Normal Q-Q")

# Scale-Location plot -> equal variance of residuals
ax = axes[1, 0]
sqrt_std_resid = np.sqrt(np.abs(std_resid))
ax.scatter(fitted, sqrt_std_resid, s=8, alpha=0.4)
smooth = lowess(sqrt_std_resid, fitted)
ax.plot(smooth[:, 0], smooth[:, 1], color="red")
ax.set_xlabel("Fitted values")
ax.set_ylabel("√|Standardized residuals|")
ax.set_title("Scale-Location")

#cooks distance plot -> influential observations
ax = axes[1, 1]
ax.scatter(leverage, std_resid, s=8, alpha=0.4)
smooth = lowess(std_resid, leverage)
ax.plot(smooth[:, 0], smooth[:, 1], color="red")
ax.axhline(0, color="grey", linestyle="--")
ax.set_xlabel("Leverage")
ax.set_ylabel("Standardized residuals")
ax.set_title("Residuals vs Leverage")

fig.savefig(PATH + "figures/regression_assumption_check.png",
            dpi=150, bbox_inches="tight")


# %%
# checking for multicollinearity using VIF (problematic if values are above 5)
from statsmodels.stats.outliers_influence import variance_inflation_factor

X = model1.model.exog            # explanatory variables of the model
names = model1.model.exog_names

vif_values = []
for i, name in enumerate(names):
    if name != "Intercept":
        vif_values.append({"variable": name, "VIF": round(variance_inflation_factor(X, i), 2)})

vif_table = pd.DataFrame(vif_values).sort_values("VIF", ascending=False)
vif_table.to_csv(PATH + "figures/model1_vif.csv", index=False)
vif_table   

# %%
