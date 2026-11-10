"""Plotly chart builders (MEMBER 4). Each function takes a DataFrame and returns a figure."""
import plotly.express as px
import plotly.graph_objects as go

TEMPLATE = "plotly_white"
INCOME_COLOR = "#2E8B57"
EXPENSE_COLOR = "#D9534F"
PALETTE = ["#0F766E", "#12315C", "#F59E0B", "#D9534F", "#2E8B57", "#6366F1", "#14B8A6", "#EC4899", "#64748B", "#84CC16"]
FONT = {"family": "Inter, Segoe UI, sans-serif", "color": "#0F172A"}


def _style(figure):
    """Apply the shared look (fonts, transparent background, soft grid) to every chart."""
    figure.update_layout(
        font=FONT, colorway=PALETTE, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        title={"font": {"size": 18, "color": "#0B1F3A"}}, margin={"l": 30, "r": 20, "t": 60, "b": 30},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        hoverlabel={"font": {"family": "Inter, sans-serif"}},
    )
    figure.update_xaxes(gridcolor="#EEF2F7", zeroline=False)
    figure.update_yaxes(gridcolor="#EEF2F7", zeroline=False)
    return figure


def _empty_figure(title):
    figure = go.Figure()
    figure.update_layout(
        title=title, template=TEMPLATE, xaxis={"visible": False}, yaxis={"visible": False},
        annotations=[{"text": "No data to display", "xref": "paper", "yref": "paper",
                      "x": 0.5, "y": 0.5, "showarrow": False, "font": {"size": 16}}],
    )
    return _style(figure)


def monthly_expense_chart(monthly_expense_df):
    """Bar chart of expenses per month (columns: month, expense)."""
    title = "Monthly Spending"
    if monthly_expense_df.empty:
        return _empty_figure(title)
    figure = px.bar(monthly_expense_df, x="month", y="expense", title=title, template=TEMPLATE,
                    labels={"month": "Month", "expense": "Expense (₹)"}, text_auto=".2s")
    figure.update_traces(marker_color=EXPENSE_COLOR)
    return _style(figure)


def income_vs_expense_chart(summary_df):
    """Grouped bars: income and expense for every month (columns: month, income, expense)."""
    title = "Monthly Income vs Expense"
    if summary_df.empty:
        return _empty_figure(title)
    figure = go.Figure()
    figure.add_bar(x=summary_df["month"], y=summary_df["income"], name="Income", marker_color=INCOME_COLOR)
    figure.add_bar(x=summary_df["month"], y=summary_df["expense"], name="Expense", marker_color=EXPENSE_COLOR)
    figure.update_layout(title=title, template=TEMPLATE, barmode="group",
                         xaxis_title="Month", yaxis_title="Amount (₹)")
    return _style(figure)


def category_pie_chart(category_df):
    """Donut chart of spending per category (columns: category, expense)."""
    title = "Category-wise Expenses"
    if category_df.empty:
        return _empty_figure(title)
    figure = px.pie(category_df, names="category", values="expense", hole=0.45, title=title, template=TEMPLATE)
    figure.update_traces(textinfo="percent+label", marker={"line": {"color": "#FFFFFF", "width": 2}})
    return _style(figure)


def category_bar_chart(category_df):
    """Horizontal bar chart of spending per category."""
    title = "Spending by Category"
    if category_df.empty:
        return _empty_figure(title)
    figure = px.bar(category_df.sort_values("expense"), x="expense", y="category", orientation="h",
                    title=title, template=TEMPLATE, labels={"expense": "Expense (₹)", "category": "Category"},
                    text_auto=".2s")
    figure.update_traces(marker_color=EXPENSE_COLOR)
    return _style(figure)


def monthly_net_chart(summary_df):
    """Line chart of the net amount (income - expense) per month."""
    title = "Monthly Net Amount"
    if summary_df.empty:
        return _empty_figure(title)
    figure = px.line(summary_df, x="month", y="net", markers=True, title=title, template=TEMPLATE,
                     labels={"month": "Month", "net": "Net (₹)"})
    return _style(figure)


def account_comparison_chart(account_df):
    """Income vs expense of every account (columns: account_number, income, expense)."""
    title = "Income vs Expense by Account"
    if account_df.empty:
        return _empty_figure(title)
    figure = go.Figure()
    figure.add_bar(x=account_df["account_number"], y=account_df["income"], name="Income", marker_color=INCOME_COLOR)
    figure.add_bar(x=account_df["account_number"], y=account_df["expense"], name="Expense", marker_color=EXPENSE_COLOR)
    figure.update_layout(title=title, template=TEMPLATE, barmode="group",
                         xaxis_title="Account", yaxis_title="Amount (₹)", xaxis_type="category")
    return _style(figure)


def amount_histogram(df):
    """Histogram showing how transaction amounts are spread."""
    title = "Distribution of Transaction Amounts"
    if df.empty:
        return _empty_figure(title)
    return _style(px.histogram(df, x="amount", color="transaction_type", nbins=30, title=title, template=TEMPLATE,
                        labels={"amount": "Amount (₹)"},
                        color_discrete_map={"DEPOSIT": INCOME_COLOR, "WITHDRAWAL": EXPENSE_COLOR}))
