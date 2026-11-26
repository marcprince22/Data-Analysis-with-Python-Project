from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.nonparametric.smoothers_lowess import lowess
from statsmodels.stats.outliers_influence import variance_inflation_factor

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = PROJECT_ROOT / "data" / "clean_data" / "zh_regression_panel.csv"
VIF_FILE = PROJECT_ROOT / "figures" / "zh_vif.csv"
PLOT_FILE = PROJECT_ROOT / "figures" / "zh_regression_assumption_check.png"


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

    X = sm.add_constant(df[factors])

    vif_values = []
    for i in range(1, len(factors) + 1):
        vif_values.append(variance_inflation_factor(X.values, i))

    vif = pd.DataFrame({"variable": factors, "VIF": vif_values})

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
    if vif["VIF"].max() > 5:
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
    ax.scatter(diag["leverage"], diag["std_resid"], s=8, alpha=0.4)
    smooth = lowess(diag["std_resid"], diag["leverage"])
    ax.plot(smooth[:, 0], smooth[:, 1], color="red")
    ax.axhline(0, color="grey", linestyle="--")
    ax.set_xlabel("Leverage")
    ax.set_ylabel("Standardized residuals")
    ax.set_title("Residuals vs Leverage")

    vif.round(2).to_csv(VIF_FILE, index=False)
    fig.savefig(PLOT_FILE, dpi=150, bbox_inches="tight")

    print(vif.round(2))
    print("Largest Cook's distance:", round(diag["cooks"].max(), 3))
    print("Rows with Cook's distance above 1:", (diag["cooks"] > 1).sum())
    print("Saved", VIF_FILE.name, "and", PLOT_FILE.name)


if __name__ == "__main__":
    main()
