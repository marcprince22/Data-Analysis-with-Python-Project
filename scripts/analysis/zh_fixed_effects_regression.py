from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = PROJECT_ROOT / "data" / "clean_data" / "zh_regression_panel.csv"
OUTPUT_FOLDER = PROJECT_ROOT / "data" / "results"
COEF_FILE = OUTPUT_FOLDER / "zh_regression_coefficients.csv"
PVALUE_FILE = OUTPUT_FOLDER / "zh_regression_pvalues.csv"


def main():
    panel = pd.read_csv(INPUT_FILE)

    formula = "turnout ~ foreigner_rate + social_assistance_rate + unemployment_rate + log_median_income + old_age_ratio + log_population_density"
    factors = [
        "foreigner_rate",
        "social_assistance_rate",
        "unemployment_rate",
        "log_median_income",
        "old_age_ratio",
        "log_population_density",
    ]

    df = panel[panel["year"] >= 2011]
    df = df[df["year"] <= 2022]
    df = df.drop(columns=["tertiary_share"])
    df = df.dropna()
    df["log_median_income"] = np.log(df["median_income"])
    df["log_population_density"] = np.log(df["population_density"])

    model1 = smf.ols(formula, data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["GDENR"]}
    )

    model2 = smf.ols(formula + " + C(GDENR)", data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["GDENR"]}
    )

    model3 = smf.ols(formula + " + C(GDENR) + C(year)", data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["GDENR"]}
    )

    df_long = panel[panel["year"] >= 1999]
    df_long = df_long[df_long["year"] <= 2022]
    df_long = df_long[
        [
            "GDENR",
            "year",
            "turnout",
            "foreigner_rate",
            "median_income",
            "old_age_ratio",
            "population_density",
        ]
    ]
    df_long = df_long.dropna()
    df_long["log_median_income"] = np.log(df_long["median_income"])
    df_long["log_population_density"] = np.log(df_long["population_density"])

    factors_long = [
        "foreigner_rate",
        "log_median_income",
        "old_age_ratio",
        "log_population_density",
    ]
    formula_long = "turnout ~ foreigner_rate + log_median_income + old_age_ratio + log_population_density"

    model4 = smf.ols(formula_long + " + C(GDENR) + C(year)", data=df_long).fit(
        cov_type="cluster", cov_kwds={"groups": df_long["GDENR"]}
    )

    df5 = panel[panel["year"] >= 2017]
    df5 = df5[df5["year"] <= 2022]
    df5 = df5.dropna()
    df5["log_median_income"] = np.log(df5["median_income"])
    df5["log_population_density"] = np.log(df5["population_density"])

    model5 = smf.ols(formula + " + tertiary_share + C(GDENR) + C(year)", data=df5).fit(
        cov_type="cluster", cov_kwds={"groups": df5["GDENR"]}
    )

    df6 = df[df["GDENR"] < 291]

    model6 = smf.ols(formula + " + C(GDENR) + C(year)", data=df6).fit(
        cov_type="cluster", cov_kwds={"groups": df6["GDENR"]}
    )

    coefficients = pd.DataFrame(
        {
            "Model 1 (OLS)": model1.params[factors],
            "Model 2 (+ municipality FE)": model2.params[factors],
            "Model 3 (+ year FE)": model3.params[factors],
            "Model 4 (1999-2022)": model4.params[factors_long],
            "Model 5 (+ education)": model5.params[factors + ["tertiary_share"]],
            "Model 6 (without merged)": model6.params[factors],
        }
    )
    pvalues = pd.DataFrame(
        {
            "Model 1 (OLS)": model1.pvalues[factors],
            "Model 2 (+ municipality FE)": model2.pvalues[factors],
            "Model 3 (+ year FE)": model3.pvalues[factors],
            "Model 4 (1999-2022)": model4.pvalues[factors_long],
            "Model 5 (+ education)": model5.pvalues[factors + ["tertiary_share"]],
            "Model 6 (without merged)": model6.pvalues[factors],
        }
    )

    coefficients.loc["observations"] = [
        len(df),
        len(df),
        len(df),
        len(df_long),
        len(df5),
        len(df6),
    ]

    if len(df) != 1677:
        raise ValueError("The main sample does not contain 1677 rows")
    if coefficients.shape[1] != 6:
        raise ValueError("The results table does not contain 6 models")

    OUTPUT_FOLDER.mkdir(exist_ok=True)
    coefficients.to_csv(COEF_FILE)
    pvalues.to_csv(PVALUE_FILE)

    print("Saved", COEF_FILE.name, coefficients.shape)
    print("Saved", PVALUE_FILE.name, pvalues.shape)


if __name__ == "__main__":
    main()
