from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.nonparametric.smoothers_lowess import lowess
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = PROJECT_ROOT / "data" / "clean_data" / "zh_regression_panel.csv"
VIF_FILE = PROJECT_ROOT / "figures" / "zh_vif.csv"
PLOT_FILE = PROJECT_ROOT / "figures" / "zh_regression_assumption_check.png"
TESTS_FILE = PROJECT_ROOT / "figures" / "zh_residual_tests.csv"


def main():

    df = pd.read_csv(INPUT_FILE)
    df = df[(df["year"] >= 2011) & (df["year"] <= 2022)]
    df = df.drop(columns="tertiary_share")
    df = df.dropna()
    df["log_median_income"] = np.log(df["median_income"])
    df["log_population_density"] = np.log(df["population_density"])

    formula = "turnout ~ foreigner_rate + social_assistance_rate + unemployment_rate + log_median_income + old_age_ratio + log_population_density"
    model3 = smf.ols(formula + " + C(GDENR) + C(year)", data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["GDENR"]}
    )

    factors = [
        "foreigner_rate",
        "social_assistance_rate",
        "unemployment_rate",
        "log_median_income",
        "old_age_ratio",
        "log_population_density",
    ]

    within = df[factors] - df.groupby("GDENR")[factors].transform("mean")
    within = within - within.groupby(df["year"]).transform("mean")

    X_pooled = sm.add_constant(df[factors])
    X_within = sm.add_constant(within)

    vif_pooled = []
    vif_within = []
    for i in range(1, len(factors) + 1):
        vif_pooled.append(variance_inflation_factor(X_pooled.values, i))
        vif_within.append(variance_inflation_factor(X_within.values, i))

    vif = pd.DataFrame({"variable": factors, "VIF pooled": vif_pooled, "VIF within": vif_within})

    df["resid"] = model3.resid
    df = df.sort_values(["GDENR", "year"])
    df["resid_lag"] = df.groupby("GDENR")["resid"].shift(1)
    autocorrelation = df["resid"].corr(df["resid_lag"])

    bp_stat, bp_pvalue, f_stat, f_pvalue = het_breuschpagan(model3.resid, X_pooled.loc[model3.resid.index])

    tests = pd.DataFrame({
        "test": ["Autocorrelation of residuals (lag 1)", "Breusch-Pagan p-value"],
        "value": [autocorrelation, bp_pvalue],
    })

    influence = model3.get_influence()

    diag = pd.DataFrame(
        {
            "fitted": model3.fittedvalues,
            "resid": model3.resid,
            "std_resid": influence.resid_studentized_internal,
            "leverage": influence.hat_matrix_diag,
            "cooks": influence.cooks_distance[0],
        }
    )

    diag = diag[diag["leverage"] < 0.99]

    if len(df) != 1677:
        raise ValueError("The main sample does not contain 1677 rows")
    if vif[["VIF pooled", "VIF within"]].max().max() > 5:
        raise ValueError("At least one VIF is above 5")

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    ax = axes[0, 0]
    ax.scatter(diag["fitted"], diag["resid"], s=8, alpha=0.4)
    smooth = lowess(diag["resid"], diag["fitted"])
    ax.plot(smooth[:, 0], smooth[:, 1], color="red")
    ax.axhline(0, color="grey", linestyle="--")
    ax.set_xlabel("Fitted values")
    ax.set_ylabel("Residuals")
    ax.set_title("Residuals vs Fitted")

    ax = axes[0, 1]
    sm.qqplot(diag["std_resid"], line="45", ax=ax)
    ax.set_ylabel("Standardized residuals")
    ax.set_title("Normal Q-Q")

    ax = axes[1, 0]
    sqrt_std_resid = np.sqrt(np.abs(diag["std_resid"]))
    ax.scatter(diag["fitted"], sqrt_std_resid, s=8, alpha=0.4)
    smooth = lowess(sqrt_std_resid, diag["fitted"])
    ax.plot(smooth[:, 0], smooth[:, 1], color="red")
    ax.set_xlabel("Fitted values")
    ax.set_ylabel("√|Standardized residuals|")
    ax.set_title("Scale-Location")

    ax = axes[1, 1]
    ax.scatter(range(len(diag)), diag["cooks"], s=8, alpha=0.4)
    ax.axhline(1, color="red", linestyle="--")
    ax.set_xlabel("Observation")
    ax.set_ylabel("Cook's distance")
    ax.set_title("Cook's distance")

    vif.round(2).to_csv(VIF_FILE, index=False)
    tests.round(3).to_csv(TESTS_FILE, index=False)
    fig.savefig(PLOT_FILE, dpi=150, bbox_inches="tight")

    print(vif.round(2))
    print("Largest Cook's distance:", round(diag["cooks"].max(), 3))
    print("Rows with Cook's distance above 1:", (diag["cooks"] > 1).sum())
    print(tests.round(3))
    print("Saved", VIF_FILE.name, TESTS_FILE.name, "and", PLOT_FILE.name)


if __name__ == "__main__":
    main()
