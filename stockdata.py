import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
import pymysql
import urllib.parse
import textwrap

# ---------------- Database Config ----------------
DB_USER = "root"
DB_PASSWORD_RAW = "Nive#1029@"  # original password
DB_PASSWORD = urllib.parse.quote_plus(DB_PASSWORD_RAW)
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "stockdata"

# ---------------- Data Loader ----------------
def load_data(table_name):
    try:
        engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
        query = f"SELECT * FROM `{table_name}`"  # backticks fix naming issues
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Database error while loading '{table_name}': {e}")
        return None

# ---------------- Tab 1: Volatility ----------------
def show_volatility():
    st.subheader("Top 10 Most Volatile Stocks")
    df = load_data("stock_volatility")

    if df is not None and not df.empty:
        df.columns = df.columns.str.strip()
        top_10 = df.sort_values(by="Volatility", ascending=False).head(10)
        st.dataframe(top_10)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(top_10['Stock'], top_10['Volatility'], color='orange')
        ax.set_xlabel("Stock")
        ax.set_ylabel("Volatility (Standard Deviation)")
        ax.set_title("Top 10 Most Volatile Stocks")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.warning("No data found in 'stock_volatility' table.")

# ---------------- Tab 2: Cumulative Returns ----------------
def show_cumulative_returns():
    st.subheader("Cumulative Return for Top 5 Performing Stocks")
    df = load_data("stock_cumulative_return")

    if df is not None and not df.empty:
        df.columns = df.columns.str.strip()
        required_columns = ["date", "stock", "cumulative_return"]
        if not all(col in df.columns for col in required_columns):
            st.warning(f"Missing one of the required columns: {required_columns}")
            return

        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.sort_values(by=['stock', 'date'])
        last_day = df.groupby("stock")["date"].transform("max") == df["date"]
        final_returns = df[last_day]

        top_5 = final_returns.sort_values(by="cumulative_return", ascending=False).head(5)
        top_5_stocks = top_5["stock"]
        top_5_df = df[df["stock"].isin(top_5_stocks)]

        st.dataframe(top_5[["stock", "date", "cumulative_return"]].reset_index(drop=True))

        fig, ax = plt.subplots(figsize=(12, 6))
        for stock in top_5_df["stock"].unique():
            stock_data = top_5_df[top_5_df["stock"] == stock]
            ax.plot(stock_data["date"], stock_data["cumulative_return"], label=stock)

        ax.set_title("Cumulative Return Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Cumulative Return")
        ax.legend(title="Stock")
        ax.grid(True)
        plt.xticks(rotation=45)

        st.pyplot(fig)

    else:
        st.warning("No data found in 'stock_cumulative_return' table.")

# ---------------- Tab 3: Sector Returns ----------------
def show_sector_returns():
    st.subheader("Average Yearly Return by Sector")
    df = load_data("sector_returns")

    if df is not None and not df.empty:
        required_columns = ["sector", "cumulative_return"]
        if not all(col in df.columns for col in required_columns):
            st.warning(f"Missing one of the required columns: {required_columns}")
            return

        df = df.sort_values(by="cumulative_return", ascending=False)
        st.dataframe(df)

        df["wrapped_sector"] = df["sector"].apply(lambda x: "\n".join(textwrap.wrap(x, width=10)))

        fig, ax = plt.subplots(figsize=(14, 6))
        bars = ax.bar(df["wrapped_sector"], df["cumulative_return"], color="teal")
        ax.set_xlabel("Sector")
        ax.set_ylabel("Average Yearly Cumulative Return")
        ax.set_title("Average Yearly Return by Sector")
        ax.set_xticks(range(len(df["wrapped_sector"])))
        ax.set_xticklabels(df["wrapped_sector"], rotation=45, ha="right", fontsize=9)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.warning("No data found in 'sector_returns' table.")

# ---------------- Tab 4: Correlation ----------------
def show_correlation():
    st.subheader("Stock Price Correlation Matrix")
    df = load_data("stock_price_correlation")

    if df is not None and not df.empty:
        if 'stock_name' in df.columns:
            df_numeric = df.drop(columns=['stock_name'])
        else:
            df_numeric = df

        if len(df_numeric) == 1:
            corr_df = df_numeric.T
            corr_df.columns = ['Correlation']
            corr_df.index.name = 'Stock'
            corr_df = corr_df.sort_values(by='Correlation', ascending=False)
            st.write("Correlation with Reference Stock:")
            st.dataframe(corr_df)

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.bar(corr_df.index, corr_df['Correlation'], color='purple')
            ax.set_title("Stock Correlation with Reference Stock")
            ax.set_ylabel("Correlation Coefficient")
            ax.set_xlabel("Stock")
            plt.xticks(rotation=90)
            st.pyplot(fig)

        else:
            corr_df = df_numeric.corr()
            st.write("Stock Price Correlation Matrix:")
            st.dataframe(corr_df)

            fig, ax = plt.subplots(figsize=(14, 10))
            sns.heatmap(
                corr_df,
                annot=False,
                cmap="coolwarm",
                center=0,
                ax=ax,
                cbar_kws={'label': 'Correlation Coefficient'}
            )
            ax.set_title("Stock Correlation Heatmap")
            st.pyplot(fig)

    else:
        st.warning("No data found in 'stock_price_correlation' table.")

# ---------------- Tab 5: Monthly Gainers & Losers ----------------
def show_monthly_gainers_losers():
    st.subheader("Monthly Top 5 Gainers & Losers")
    df = load_data("monthly_top_5_gainers_losers")

    if df is not None and not df.empty:
        df['month'] = pd.to_datetime(df['month'], errors='coerce')
        df['stock'] = df['stock'].astype(str)
        df['type'] = df['type'].astype(str)

        months = df['month'].dt.strftime('%B %Y').unique()

        for month in months:
            st.markdown(f"### {month}")
            month_df = df[df['month'].dt.strftime('%B %Y') == month]

            fig, axs = plt.subplots(1, 2, figsize=(16, 6))

            gainers = month_df[month_df['type'] == 'Top Gainer'].sort_values(by='stock_rank').head(5)
            axs[0].bar(gainers['stock'], gainers['monthly_return'], color='green')
            axs[0].set_title("Top 5 Gainers")
            axs[0].set_ylabel("Monthly Return (%)")
            axs[0].tick_params(axis='x', rotation=45)

            losers = month_df[month_df['type'] == 'Top Loser'].sort_values(by='stock_rank').head(5)
            axs[1].bar(losers['stock'], losers['monthly_return'], color='red')
            axs[1].set_title("Top 5 Losers")
            axs[1].set_ylabel("Monthly Return (%)")
            axs[1].tick_params(axis='x', rotation=45)

            st.pyplot(fig)
    else:
        st.warning("No data found in 'monthly_top_5_gainers_losers' table.")

# ---------------- Main App ----------------
def main():
    st.set_page_config(page_title="Stock Analytics Dashboard", layout="wide")
    st.title("📈 Stock Analytics Dashboard")

    # Fixed sidebar navigation labels
    selection = st.sidebar.radio(
        "Navigation",
        [
            "Volatility",
            "Cumulative Returns",
            "Sector Returns",
            "Correlation Matrix",
            "Monthly Gainers & Losers"
        ]
    )

    if selection == "Volatility":
        show_volatility()
    elif selection == "Cumulative Returns":
        show_cumulative_returns()
    elif selection == "Sector Returns":
        show_sector_returns()
    elif selection == "Correlation Matrix":
        show_correlation()
    elif selection == "Monthly Gainers & Losers":
        show_monthly_gainers_losers()

if __name__ == "__main__":
    main()
