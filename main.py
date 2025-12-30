import yfinance as yf
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt


def calculate_capm(tickers, benchmark='SPY', period='5y', monthly=True):
    """
    Calculates Alpha and Beta for a list of tickers relative to a benchmark.

    Args:
        tickers (list): List of stock symbols.
        benchmark (str): Benchmark symbol (default S&P 500 ETF 'SPY').
        period (str): Data period to download (default '5y' for monthly analysis).

    Returns:
        pd.DataFrame: DataFrame containing Alpha, Beta, and R-squared values.
    """

    # Download Data
    print(f"Downloading data for {len(tickers)} tickers + benchmark...")
    # combining lists to download in one go for efficiency
    all_symbols = tickers + [benchmark]
    # Add auto_adjust=False to get the 'Adj Close' column explicitly
    data = yf.download(all_symbols, period=period, progress=False, auto_adjust=False)['Adj Close']

    # Resample to Monthly Data (Month End)
    if monthly:
        data = data.resample('M').last()

    # Calculate Monthly Returns
    # Drop NaN values usually found in the first row after pct_change
    returns = data.pct_change().dropna()

    # Define Risk-Free Rate (Approximate)
    # Using a fixed 4% annual risk-free rate for simplicity.
    rf_annual = 0.04
    if monthly:
        rf_monthly = rf_annual / 12
    else:
        rf_monthly = rf_annual / 252

    results = []

    # Perform Linear Regression for each stock
    for stock in tickers:
        # Calculate Excess Returns (Return - Risk Free Rate)
        stock_excess_ret = returns[stock] - rf_monthly
        market_excess_ret = returns[benchmark] - rf_monthly

        # Linear Regression: Y = Alpha + Beta * X
        # X = Market Excess Return, Y = Stock Excess Return
        beta, alpha, r_value, p_value, std_err = stats.linregress(market_excess_ret, stock_excess_ret)

        # Convert Alpha to annualized percentage (Monthly * 12)
        if monthly:
            alpha_annual = alpha * 12
        else:
            alpha_annual = alpha * 252

        results.append({
            'Stock': stock,
            'Beta': round(beta, 2),
            'Alpha (Annualized)': round(alpha_annual, 4),
            'R-Squared': round(r_value ** 2, 2)})

    return pd.DataFrame(results).set_index('Stock')

# Main Execution

# Top 10 Stocks by approx Market Cap (as of late 2024/2025)
top_10_stocks = [
    'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN',
    'META', 'TSLA', 'BRK-B', 'LLY', 'AVGO']

df_results = calculate_capm(top_10_stocks)

print("\n--- CAPM Analysis Results (vs SPY) ---")
print(df_results.sort_values(by='Beta', ascending=False))

# VISUALIZATION SECTION

# Select the stock
selected_stock = 'GOOGL'
benchmark = 'SPY'

# Fetch 2025 specific data for the plot
print(f"\nFetching 2025 data for plotting {selected_stock} vs {benchmark}...")
plot_data = \
yf.download([selected_stock, benchmark], start="2020-12-31", end="2025-12-31", progress=False, auto_adjust=False)[
    'Adj Close']

# Process Data for Plots
# Normalize prices to start at 100 for better visual comparison in the time series
normalized_price = (plot_data / plot_data.iloc[0]) * 100

# Calculate returns for the scatter plot
# We resample the plot data to Monthly to match the new CAPM methodology
plot_data_monthly = plot_data.resample('M').last()
plot_returns = plot_data_monthly.pct_change().dropna()
rf_monthly = 0.04 / 12

x_excess = plot_returns[benchmark] - rf_monthly
y_excess = plot_returns[selected_stock] - rf_monthly

# Recalculate regression specifically for this 2025 slice to get the fit line
beta_plot, alpha_plot, r_sq_plot, _, _ = stats.linregress(x_excess, y_excess)
line_fit = beta_plot * x_excess + alpha_plot

# Create the 2x1 Plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
plt.subplots_adjust(hspace=0.3)

# Top Plot: Time Series (2025)
# Keeping this Daily so the chart looks smooth and detailed
ax1.plot(normalized_price.index, normalized_price[selected_stock], label=selected_stock, linewidth=2)
ax1.plot(normalized_price.index, normalized_price[benchmark], label=benchmark, color='orange', linestyle='--',
         linewidth=2)
ax1.set_title(f'2020 to 2025 Performance Comparison: {selected_stock} vs {benchmark} (Normalized to 100)')
ax1.set_ylabel('Normalized Price')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Bottom Plot: Excess Returns Scatter + Fit Line
# This now uses Monthly data points
ax2.scatter(x_excess, y_excess, alpha=0.5, label='Monthly Returns')
ax2.plot(x_excess, line_fit, color='red', linewidth=2, label=f'Fit Line (Beta={beta_plot:.2f})')

# Annotate Alpha and Beta
text_str = '\n'.join((
    r'$\alpha$ (Monthly) = %.5f' % (alpha_plot,),
    r'$\beta$ = %.2f' % (beta_plot,),
    r'$R^2$ = %.2f' % (r_sq_plot ** 2,)))

# Place a text box in upper left in axes coords
props = dict(boxstyle='round', facecolor='white', alpha=0.8)
ax2.text(0.05, 0.95, text_str, transform=ax2.transAxes, fontsize=12,
         verticalalignment='top', bbox=props)

ax2.set_title(f'CAPM Regression: {selected_stock} Excess Returns vs {benchmark} Excess Returns')
ax2.set_xlabel(f'{benchmark} Excess Returns')
ax2.set_ylabel(f'{selected_stock} Excess Returns')
ax2.legend(loc='lower right')
ax2.grid(True, alpha=0.3)

plt.savefig('googl.png')