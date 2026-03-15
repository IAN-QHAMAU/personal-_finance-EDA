from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "Personal_Finance_Dataset.csv"
VISUALS_DIR = BASE_DIR / "visuals"
REPORT_PATH = BASE_DIR / "README.md"


def setup_style() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams["figure.figsize"] = (14, 8)
    plt.rcParams["axes.titlesize"] = 18
    plt.rcParams["axes.labelsize"] = 13


def load_and_clean_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Transaction Description"] = df["Transaction Description"].astype(str).str.strip()
    df["Category"] = df["Category"].astype(str).str.strip()
    df["Type"] = df["Type"].astype(str).str.strip().str.title()

    # Keep only rows with required fields
    df = df.dropna(subset=["Date", "Category", "Amount", "Type"]).copy()

    # Coerce amount and remove invalid entries
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df = df.dropna(subset=["Amount"]).copy()

    # Signed amount: expenses as negative, income as positive
    df["SignedAmount"] = df["Amount"]
    df.loc[df["Type"] == "Expense", "SignedAmount"] = -df.loc[df["Type"] == "Expense", "Amount"]

    # Time features
    df["YearMonth"] = df["Date"].dt.to_period("M").astype(str)
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Day"] = df["Date"].dt.day
    df["Weekday"] = df["Date"].dt.day_name()

    return df.sort_values("Date")


def save_plot(output_name: str) -> None:
    VISUALS_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(VISUALS_DIR / output_name, dpi=220, bbox_inches="tight")
    plt.close()


def plot_income_expense_trend(df: pd.DataFrame) -> None:
    monthly = (
        df.groupby(["YearMonth", "Type"], as_index=False)["Amount"].sum()
        .pivot(index="YearMonth", columns="Type", values="Amount")
        .fillna(0)
    )

    for column in ["Income", "Expense"]:
        if column not in monthly.columns:
            monthly[column] = 0

    monthly["Net"] = monthly["Income"] - monthly["Expense"]

    fig, ax = plt.subplots()
    monthly[["Income", "Expense"]].plot(ax=ax, marker="o", linewidth=2.4)
    ax.set_title("Monthly Income vs Expense")
    ax.set_xlabel("Year-Month")
    ax.set_ylabel("Amount")
    ax.tick_params(axis="x", rotation=45)
    save_plot("01_monthly_income_vs_expense.png")

    fig, ax = plt.subplots()
    sns.barplot(x=monthly.index, y=monthly["Net"].values, ax=ax, color="#4C72B0")
    ax.axhline(0, color="black", linewidth=1)
    ax.set_title("Monthly Net Cashflow (Income - Expense)")
    ax.set_xlabel("Year-Month")
    ax.set_ylabel("Net Amount")
    ax.tick_params(axis="x", rotation=45)
    save_plot("02_monthly_net_cashflow.png")


def plot_category_breakdown(df: pd.DataFrame) -> None:
    expense = (
        df[df["Type"] == "Expense"]
        .groupby("Category", as_index=False)["Amount"]
        .sum()
        .sort_values("Amount", ascending=False)
        .head(10)
    )

    income = (
        df[df["Type"] == "Income"]
        .groupby("Category", as_index=False)["Amount"]
        .sum()
        .sort_values("Amount", ascending=False)
        .head(10)
    )

    if not expense.empty:
        fig, ax = plt.subplots()
        sns.barplot(data=expense, x="Amount", y="Category", ax=ax, color="#C44E52")
        ax.set_title("Top Expense Categories")
        ax.set_xlabel("Total Spent")
        ax.set_ylabel("Category")
        save_plot("03_top_expense_categories.png")

    if not income.empty:
        fig, ax = plt.subplots()
        sns.barplot(data=income, x="Amount", y="Category", ax=ax, color="#55A868")
        ax.set_title("Top Income Categories")
        ax.set_xlabel("Total Income")
        ax.set_ylabel("Category")
        save_plot("04_top_income_categories.png")


def plot_distribution_and_timing(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots()
    sns.boxplot(data=df, x="Type", y="Amount", ax=ax, hue="Type", legend=False, palette="Set2")
    ax.set_title("Transaction Amount Distribution by Type")
    ax.set_xlabel("Transaction Type")
    ax.set_ylabel("Amount")
    save_plot("05_amount_distribution_by_type.png")

    weekday_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    spending_weekday = (
        df[df["Type"] == "Expense"]
        .groupby("Weekday", as_index=False)["Amount"]
        .sum()
        .set_index("Weekday")
        .reindex(weekday_order)
        .reset_index()
    )

    fig, ax = plt.subplots()
    sns.barplot(data=spending_weekday, x="Weekday", y="Amount", ax=ax, color="#DD8452")
    ax.set_title("Total Spending by Weekday")
    ax.set_xlabel("Weekday")
    ax.set_ylabel("Total Spent")
    ax.tick_params(axis="x", rotation=30)
    save_plot("06_spending_by_weekday.png")


def plot_expense_heatmap(df: pd.DataFrame) -> None:
    expense = df[df["Type"] == "Expense"].copy()
    if expense.empty:
        return

    pivot = (
        expense.groupby(["Category", "YearMonth"], as_index=False)["Amount"]
        .sum()
        .pivot(index="Category", columns="YearMonth", values="Amount")
        .fillna(0)
    )

    top_categories = expense.groupby("Category")["Amount"].sum().sort_values(ascending=False).head(10).index
    pivot = pivot.loc[top_categories]

    fig, ax = plt.subplots(figsize=(18, 9))
    sns.heatmap(pivot, cmap="YlOrRd", linewidths=0.2, ax=ax)
    ax.set_title("Expense Intensity Heatmap (Top 10 Categories by Month)")
    ax.set_xlabel("Year-Month")
    ax.set_ylabel("Category")
    save_plot("07_expense_heatmap_top_categories.png")


def summarize_insights(df: pd.DataFrame) -> str:
    total_income = df.loc[df["Type"] == "Income", "Amount"].sum()
    total_expense = df.loc[df["Type"] == "Expense", "Amount"].sum()
    net = total_income - total_expense

    monthly = (
        df.groupby(["YearMonth", "Type"], as_index=False)["Amount"].sum()
        .pivot(index="YearMonth", columns="Type", values="Amount")
        .fillna(0)
    )

    for column in ["Income", "Expense"]:
        if column not in monthly.columns:
            monthly[column] = 0

    monthly["Net"] = monthly["Income"] - monthly["Expense"]

    best_month = monthly["Net"].idxmax()
    worst_month = monthly["Net"].idxmin()

    top_expense_cat = (
        df[df["Type"] == "Expense"].groupby("Category")["Amount"].sum().sort_values(ascending=False)
    )
    top_income_cat = (
        df[df["Type"] == "Income"].groupby("Category")["Amount"].sum().sort_values(ascending=False)
    )

    expense_share = (total_expense / (total_income + 1e-9)) * 100 if total_income > 0 else float("nan")

    largest_expense = df[df["Type"] == "Expense"].nlargest(3, "Amount")
    largest_income = df[df["Type"] == "Income"].nlargest(3, "Amount")

    lines = []
    lines.append("# Personal Finance EDA - Key Insights\n")
    lines.append(f"- Transactions analyzed: **{len(df):,}**")
    lines.append(f"- Date range: **{df['Date'].min().date()}** to **{df['Date'].max().date()}**")
    lines.append(f"- Total income: **{total_income:,.2f}**")
    lines.append(f"- Total expense: **{total_expense:,.2f}**")
    lines.append(f"- Net cashflow: **{net:,.2f}**")
    lines.append(f"- Expense-to-income ratio: **{expense_share:.2f}%**\n")

    if not top_expense_cat.empty:
        lines.append("## Spending Drivers")
        lines.append(
            f"- Top expense category: **{top_expense_cat.index[0]}** ({top_expense_cat.iloc[0]:,.2f})"
        )
        lines.append(
            f"- Top 3 expense categories account for **{top_expense_cat.head(3).sum() / total_expense * 100:.2f}%** of total spending\n"
        )

    if not top_income_cat.empty:
        lines.append("## Income Drivers")
        lines.append(
            f"- Top income category: **{top_income_cat.index[0]}** ({top_income_cat.iloc[0]:,.2f})"
        )
        lines.append(
            f"- Top 3 income categories account for **{top_income_cat.head(3).sum() / total_income * 100:.2f}%** of total income\n"
        )

    lines.append("## Cashflow Momentum")
    lines.append(f"- Best month by net cashflow: **{best_month}** ({monthly.loc[best_month, 'Net']:,.2f})")
    lines.append(f"- Worst month by net cashflow: **{worst_month}** ({monthly.loc[worst_month, 'Net']:,.2f})")
    positive_months = int((monthly["Net"] > 0).sum())
    lines.append(
        f"- Positive net months: **{positive_months}/{len(monthly)}** ({positive_months / len(monthly) * 100:.1f}%)\n"
    )

    lines.append("## High-Value Transactions")
    if not largest_expense.empty:
        lines.append("- Largest expenses:")
        for _, row in largest_expense.iterrows():
            lines.append(
                f"  - {row['Date'].date()} | {row['Category']} | {row['Amount']:,.2f} | {row['Transaction Description'][:70]}"
            )

    if not largest_income.empty:
        lines.append("- Largest incomes:")
        for _, row in largest_income.iterrows():
            lines.append(
                f"  - {row['Date'].date()} | {row['Category']} | {row['Amount']:,.2f} | {row['Transaction Description'][:70]}"
            )

    lines.append("\n## Final Takeaways")
    lines.append("- Track and cap the biggest expense category first; it offers the largest savings leverage.")
    lines.append("- Replicate behavior from the best cashflow month to improve consistency.")
    lines.append("- Build a monthly guardrail: keep expenses under a fixed percentage of income.")
    lines.append("- Review top outlier transactions weekly to avoid silent budget drift.")

    return "\n".join(lines)


def main() -> None:
    setup_style()
    df = load_and_clean_data(DATA_PATH)
    plot_income_expense_trend(df)
    plot_category_breakdown(df)
    plot_distribution_and_timing(df)
    plot_expense_heatmap(df)

    report = summarize_insights(df)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print("EDA complete")
    print(f"Rows analyzed: {len(df):,}")
    print(f"Visuals saved to: {VISUALS_DIR}")
    print(f"Report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
