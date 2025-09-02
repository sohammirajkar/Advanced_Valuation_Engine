import streamlit as st
import requests
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
import time
from typing import Dict, List, Any

API_URL = "http://localhost:8000"

# Set page config
st.set_page_config(
    page_title="Advanced Valuation Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
.stMetric {
    background-color: white;
    padding: 1rem;
    border-radius: 0.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Advanced Valuation Engine")
st.markdown("*Powered by FastAPI, Celery, and Redis for high-performance financial computations*")

# Sidebar for global settings
with st.sidebar:
    st.header("Global Settings")
    risk_free_rate = st.number_input("Risk-free Rate (%)", value=5.0, min_value=0.0, max_value=20.0, step=0.1) / 100
    
    st.header("Cache Management")
    if st.button("Check Cache Stats"):
        try:
            cache_stats = requests.get(f"{API_URL}/tasks/cache-stats").json()
            st.json(cache_stats)
        except Exception as e:
            st.error(f"Error fetching cache stats: {e}")

# Create tabs for different functionalities
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Basic Valuation", "Options Pricing", "Exotic Options", 
    "Bond Analytics", "Portfolio Analysis", "Market Data"
])

# Tab 1: Basic Valuation
with tab1:
    st.header("💰 Basic NPV Calculator")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        cash_flows = st.text_area(
            "Enter cash flows (comma-separated)", 
            "100, 200, 300, 400, 500",
            help="Enter the expected cash flows for each period"
        )
        discount_rate = st.number_input(
            "Discount rate (%)", 
            value=10.0, 
            min_value=0.0, 
            max_value=50.0, 
            step=0.1,
            help="Annual discount rate for NPV calculation"
        ) / 100
        
        if st.button("Calculate NPV", type="primary"):
            try:
                cf_list = [float(x.strip()) for x in cash_flows.split(",")]
                res = requests.post(
                    f"{API_URL}/valuation/npv", 
                    json={"cash_flows": cf_list, "discount_rate": discount_rate}
                ).json()
                
                npv = res['npv']
                
                with col2:
                    st.metric("Net Present Value", f"${npv:,.2f}")
                    
                    if npv > 0:
                        st.success("✓ Positive NPV - Investment is attractive")
                    else:
                        st.error("✗ Negative NPV - Investment may not be worthwhile")
                
                # Create cash flow visualization
                periods = list(range(len(cf_list)))
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=periods,
                    y=cf_list,
                    name="Cash Flows",
                    marker_color="lightblue"
                ))
                fig.update_layout(
                    title="Cash Flow Timeline",
                    xaxis_title="Period",
                    yaxis_title="Cash Flow ($)",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error calculating NPV: {e}")


# Tab 2: Options Pricing
with tab2:
    st.header("🎯 Options Pricing Models")
    
    # Options parameters input
    col1, col2, col3 = st.columns(3)
    
    with col1:
        S = st.number_input("Current Stock Price ($)", value=100.0, min_value=0.1, step=1.0)
        K = st.number_input("Strike Price ($)", value=100.0, min_value=0.1, step=1.0)
    
    with col2:
        T = st.number_input("Time to Expiration (years)", value=1.0, min_value=0.01, max_value=10.0, step=0.01)
        sigma = st.number_input("Volatility (%)", value=20.0, min_value=0.1, max_value=200.0, step=0.1) / 100
    
    with col3:
        option_type = st.selectbox("Option Type", ["call", "put"])
        model_type = st.selectbox("Pricing Model", ["Black-Scholes", "Binomial Tree", "Monte Carlo"])
    
    if st.button("Calculate Option Price", type="primary"):
        col1, col2, col3 = st.columns(3)
        
        try:
            if model_type == "Black-Scholes":
                res = requests.post(f"{API_URL}/valuation/black-scholes", json={
                    "S": S, "K": K, "T": T, "r": risk_free_rate, "sigma": sigma, "option_type": option_type
                }).json()
                
                with col1:
                    st.metric("Option Price", f"${res['option_price']:.4f}")
                
                # Display Greeks
                with col2:
                    st.subheader("Greeks")
                    greeks = res['greeks']
                    st.metric("Delta", f"{greeks['delta']:.4f}")
                    st.metric("Gamma", f"{greeks['gamma']:.4f}")
                
                with col3:
                    st.metric("Theta", f"{greeks['theta']:.4f}")
                    st.metric("Vega", f"{greeks['vega']:.4f}")
                    st.metric("Rho", f"{greeks['rho']:.4f}")
            
            elif model_type == "Binomial Tree":
                steps = st.slider("Number of Steps", 10, 500, 100)
                american = st.checkbox("American Option", value=True)
                
                res = requests.post(f"{API_URL}/valuation/binomial-tree", json={
                    "S": S, "K": K, "T": T, "r": risk_free_rate, "sigma": sigma, 
                    "option_type": option_type, "steps": steps, "american": american
                }).json()
                
                with col1:
                    st.metric("Option Price", f"${res['option_price']:.4f}")
                    st.info(f"Model: {'American' if american else 'European'} Binomial Tree ({steps} steps)")
            
            elif model_type == "Monte Carlo":
                trials = st.slider("Number of Simulations", 1000, 100000, 10000, step=1000)
                
                # Submit async task
                task_res = requests.post(f"{API_URL}/tasks/montecarlo", params={
                    "trials": trials, "S0": S, "r": risk_free_rate, "sigma": sigma,
                    "T": T, "K": K, "option_type": option_type
                }).json()
                
                task_id = task_res["task_id"]
                st.info(f"Monte Carlo simulation started. Task ID: {task_id}")
                
                # Poll for results
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(30):  # Poll for 30 seconds max
                    time.sleep(1)
                    progress_bar.progress((i + 1) / 30)
                    
                    status_res = requests.get(f"{API_URL}/tasks/status/{task_id}").json()
                    
                    if status_res["status"] == "completed":
                        progress_bar.progress(1.0)
                        status_text.success("Simulation completed!")
                        
                        result = status_res["result"]
                        
                        with col1:
                            st.metric("Option Price", f"${result['option_price']:.4f}")
                            st.metric("Standard Error", f"{result['std_error']:.6f}")
                        
                        with col2:
                            st.subheader("Confidence Interval")
                            ci = result['confidence_interval']
                            st.write(f"95% CI: ${ci[0]:.4f} - ${ci[1]:.4f}")
                            st.metric("Computation Time", f"{result['computation_time_seconds']:.2f}s")
                        
                        with col3:
                            st.subheader("Final Price Statistics")
                            stats = result['final_prices_stats']
                            st.metric("Mean", f"${stats['mean']:.2f}")
                            st.metric("Std Dev", f"${stats['std']:.2f}")
                        
                        break
                    else:
                        status_text.info(f"Status: {status_res['status']}...")
                
                else:
                    st.warning("Simulation is taking longer than expected. Check status manually.")
                    
        except Exception as e:
            st.error(f"Error calculating option price: {e}")
    
    # Option Chain Generator
    st.subheader("🔗 Option Chain Generator")
    if st.button("Generate Option Chain"):
        try:
            res = requests.get(f"{API_URL}/valuation/option-chain", params={
                "S": S, "T": T, "r": risk_free_rate, "sigma": sigma
            }).json()
            
            chain_df = pd.DataFrame(res['option_chain'])
            
            # Display option chain table
            st.dataframe(
                chain_df.style.format({
                    'strike': '${:.2f}',
                    'call_price': '${:.4f}',
                    'put_price': '${:.4f}',
                    'call_delta': '{:.4f}',
                    'put_delta': '{:.4f}',
                    'gamma': '{:.4f}',
                    'theta': '{:.4f}',
                    'vega': '{:.4f}'
                }),
                use_container_width=True
            )
            
            # Plot option prices
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Option Prices', 'Delta', 'Gamma', 'Theta'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Option prices
            fig.add_trace(
                go.Scatter(x=chain_df['strike'], y=chain_df['call_price'], name='Call Price', line=dict(color='green')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=chain_df['strike'], y=chain_df['put_price'], name='Put Price', line=dict(color='red')),
                row=1, col=1
            )
            
            # Delta
            fig.add_trace(
                go.Scatter(x=chain_df['strike'], y=chain_df['call_delta'], name='Call Delta', line=dict(color='blue')),
                row=1, col=2
            )
            fig.add_trace(
                go.Scatter(x=chain_df['strike'], y=chain_df['put_delta'], name='Put Delta', line=dict(color='orange')),
                row=1, col=2
            )
            
            # Gamma
            fig.add_trace(
                go.Scatter(x=chain_df['strike'], y=chain_df['gamma'], name='Gamma', line=dict(color='purple')),
                row=2, col=1
            )
            
            # Theta
            fig.add_trace(
                go.Scatter(x=chain_df['strike'], y=chain_df['theta'], name='Theta', line=dict(color='brown')),
                row=2, col=2
            )
            
            fig.update_layout(height=600, showlegend=True, title_text="Option Chain Analysis")
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error generating option chain: {e}")



# Tab 3: Exotic Options
with tab3:
    st.header("🌊 Exotic Options Pricing")
    
    exotic_type = st.selectbox("Exotic Option Type", ["Asian", "Barrier", "Lookback"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        S_exotic = st.number_input("Stock Price ($)", value=100.0, key="exotic_S")
        K_exotic = st.number_input("Strike Price ($)", value=100.0, key="exotic_K")
        T_exotic = st.number_input("Time to Expiration (years)", value=1.0, key="exotic_T")
        sigma_exotic = st.number_input("Volatility (%)", value=20.0, key="exotic_vol") / 100
        option_type_exotic = st.selectbox("Option Type", ["call", "put"], key="exotic_type")
    
    with col2:
        num_paths = st.slider("Monte Carlo Paths", 1000, 50000, 10000, step=1000)
        steps = st.slider("Time Steps", 50, 500, 252)
        
        # Initialize variables to avoid unbound variable errors
        average_type = None
        barrier_level = None
        barrier_type = None
        lookback_type = None
        
        if exotic_type == "Asian":
            average_type = st.selectbox("Average Type", ["arithmetic", "geometric"])
        elif exotic_type == "Barrier":
            barrier_level = st.number_input("Barrier Level ($)", value=90.0)
            barrier_type = st.selectbox("Barrier Type", ["down_and_out", "up_and_out", "down_and_in", "up_and_in"])
        elif exotic_type == "Lookback":
            lookback_type = st.selectbox("Lookback Type", ["floating", "fixed"])
    
    if st.button("Price Exotic Option", type="primary"):
        try:
            payload = {
                "option_class": exotic_type.lower() if exotic_type else "asian",
                "S": S_exotic,
                "K": K_exotic,
                "T": T_exotic,
                "r": risk_free_rate,
                "sigma": sigma_exotic,
                "option_type": option_type_exotic,
                "num_paths": num_paths,
                "steps": steps
            }
            
            if exotic_type == "Asian" and average_type is not None:
                payload["average_type"] = average_type
            elif exotic_type == "Barrier" and barrier_level is not None and barrier_type is not None:
                payload["barrier"] = barrier_level
                payload["barrier_type"] = barrier_type
            elif exotic_type == "Lookback" and lookback_type is not None:
                payload["lookback_type"] = lookback_type
            
            res = requests.post(f"{API_URL}/valuation/exotic-options", json=payload).json()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Option Price", f"${res['price']:.4f}")
                st.metric("Standard Error", f"{res['std_error']:.6f}")
            
            with col2:
                ci = res['confidence_interval']
                st.subheader("95% Confidence Interval")
                st.write(f"${ci[0]:.4f} - ${ci[1]:.4f}")
            
            with col3:
                if '_cache_metadata' in res:
                    st.subheader("Computation Info")
                    st.write(f"Time: {res['_cache_metadata']['computation_time']:.2f}s")
                    st.write(f"Paths: {num_paths:,}")
            
        except Exception as e:
            st.error(f"Error pricing exotic option: {e}")


# Tab 4: Bond Analytics
with tab4:
    st.header("📜 Bond Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        face_value = st.number_input("Face Value ($)", value=1000.0, min_value=0.01)
        coupon_rate = st.number_input("Coupon Rate (%)", value=5.0, min_value=0.0, max_value=50.0) / 100
        years_to_maturity = st.number_input("Years to Maturity", value=10.0, min_value=0.01, max_value=50.0)
        frequency = st.selectbox("Payment Frequency", [1, 2, 4, 12], index=1, format_func=lambda x: f"{x} times per year")
    
    with col2:
        calculation_type = st.radio("Calculate", ["Price from Yield", "Yield from Price"])
        
        # Initialize variables to avoid unbound variable errors
        ytm = None
        bond_price = None
        
        if calculation_type == "Price from Yield":
            ytm = st.number_input("Yield to Maturity (%)", value=5.0, min_value=0.0, max_value=50.0) / 100
        else:
            bond_price = st.number_input("Bond Price ($)", value=1000.0, min_value=0.01)
    
    if st.button("Calculate Bond Metrics", type="primary"):
        if calculation_type == "Price from Yield" and ytm is None:
            st.error("Please provide the yield to maturity.")
        elif calculation_type == "Yield from Price" and bond_price is None:
            st.error("Please provide the bond price.")
        else:
            try:
                if calculation_type == "Price from Yield":
                    payload = {
                        "face_value": face_value,
                        "coupon_rate": coupon_rate,
                        "years_to_maturity": years_to_maturity,
                        "yield_to_maturity": ytm,
                        "frequency": frequency
                    }
                else:  # calculation_type == "Yield from Price"
                    payload = {
                        "face_value": face_value,
                        "coupon_rate": coupon_rate,
                        "years_to_maturity": years_to_maturity,
                        "price": bond_price,
                        "frequency": frequency
                    }
                
                res = requests.post(f"{API_URL}/valuation/bond-pricing", json=payload).json()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Bond Price", f"${res['bond_price']:.2f}")
                    st.metric("Yield to Maturity", f"{res['yield_to_maturity']:.4%}")
                
                with col2:
                    if 'macaulay_duration' in res:
                        st.metric("Macaulay Duration", f"{res['macaulay_duration']:.2f} years")
                        st.metric("Modified Duration", f"{res['modified_duration']:.2f}")
                
                with col3:
                    # Calculate additional metrics
                    current_yield = (coupon_rate * face_value) / res['bond_price']
                    st.metric("Current Yield", f"{current_yield:.4%}")
                    
                    if res['bond_price'] > face_value:
                        st.info("📈 Trading at Premium")
                    elif res['bond_price'] < face_value:
                        st.info("📉 Trading at Discount")
                    else:
                        st.info("🎯 Trading at Par")
                
                # Bond price sensitivity analysis
                st.subheader("Yield Sensitivity Analysis")
                
                ytm_range = np.linspace(max(0.001, res['yield_to_maturity'] - 0.05), 
                                       res['yield_to_maturity'] + 0.05, 50)
                prices = []
                
                for y in ytm_range:
                    price_data = {
                        "face_value": face_value,
                        "coupon_rate": coupon_rate,
                        "years_to_maturity": years_to_maturity,
                        "yield_to_maturity": y,
                        "frequency": frequency
                    }
                    price_res = requests.post(f"{API_URL}/valuation/bond-pricing", json=price_data).json()
                    prices.append(price_res['bond_price'])
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=ytm_range * 100,
                    y=prices,
                    mode='lines',
                    name='Bond Price',
                    line=dict(color='blue', width=3)
                ))
                
                # Mark current point
                fig.add_trace(go.Scatter(
                    x=[res['yield_to_maturity'] * 100],
                    y=[res['bond_price']],
                    mode='markers',
                    marker=dict(color='red', size=10),
                    name='Current Price'
                ))
                
                fig.update_layout(
                    title="Bond Price vs Yield to Maturity",
                    xaxis_title="Yield to Maturity (%)",
                    yaxis_title="Bond Price ($)",
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error calculating bond metrics: {e}")


# Tab 5: Portfolio Analysis
with tab5:
    st.header("💼 Portfolio Analysis")
    
    st.subheader("Portfolio Composition")
    
    # Default portfolio example
    default_assets = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
    default_weights = [0.3, 0.25, 0.25, 0.2]
    default_returns = [0.12, 0.10, 0.11, 0.15]
    
    num_assets = st.slider("Number of Assets", 2, 10, 4)
    
    col1, col2 = st.columns(2)
    
    weights = []
    returns = []
    asset_names = []
    
    with col1:
        st.subheader("Asset Details")
        for i in range(num_assets):
            asset_name = st.text_input(f"Asset {i+1} Name", 
                                     value=default_assets[i] if i < len(default_assets) else f"Asset_{i+1}",
                                     key=f"asset_{i}")
            asset_names.append(asset_name)
            
            weight = st.number_input(f"Weight for {asset_name}", 
                                   value=default_weights[i] if i < len(default_weights) else 1.0/num_assets,
                                   min_value=0.0, max_value=1.0, step=0.01,
                                   key=f"weight_{i}")
            weights.append(weight)
            
            expected_return = st.number_input(f"Expected Return for {asset_name} (%)",
                                            value=default_returns[i]*100 if i < len(default_returns) else 10.0,
                                            min_value=-50.0, max_value=100.0, step=0.1,
                                            key=f"return_{i}") / 100
            returns.append(expected_return)
    
    with col2:
        st.subheader("Correlation Matrix")
        
        # Create a simple correlation matrix (in practice, this would be estimated from historical data)
        correlation_matrix = np.eye(num_assets)
        
        # Allow user to input some correlations
        st.info("Simplified correlation input (diagonal elements are 1.0)")
        correlation_data = {}
        
        for i in range(num_assets):
            for j in range(i+1, num_assets):
                corr_key = f"corr_{i}_{j}"
                corr_value = st.slider(
                    f"Correlation: {asset_names[i]} & {asset_names[j]}",
                    -1.0, 1.0, 0.3, 0.01,
                    key=corr_key
                )
                correlation_matrix[i, j] = corr_value
                correlation_matrix[j, i] = corr_value
        
        # Display correlation matrix
        st.write("Correlation Matrix:")
        corr_df = pd.DataFrame(correlation_matrix, 
                              index=asset_names, 
                              columns=asset_names)
        st.dataframe(corr_df.style.format("{:.3f}"))
    
    # Portfolio simulation parameters
    st.subheader("Monte Carlo Simulation Parameters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        initial_value = st.number_input("Initial Portfolio Value ($)", value=100000, min_value=1000, step=1000)
        time_horizon = st.number_input("Time Horizon (years)", value=1.0, min_value=0.1, max_value=10.0, step=0.1)
    
    with col2:
        num_simulations = st.slider("Number of Simulations", 1000, 50000, 10000, step=1000)
    
    with col3:
        # Check if weights sum to 1
        total_weight = sum(weights)
        if abs(total_weight - 1.0) > 0.01:
            st.warning(f"Weights sum to {total_weight:.3f}, not 1.0")
            # Normalize weights
            weights = [w / total_weight for w in weights]
            st.info("Weights normalized automatically")
    
    if st.button("Run Portfolio Analysis", type="primary"):
        try:
            # Convert correlation to covariance matrix
            volatilities = [0.2] * num_assets  # Assume 20% volatility for simplicity
            cov_matrix = np.zeros((num_assets, num_assets))
            
            for i in range(num_assets):
                for j in range(num_assets):
                    cov_matrix[i, j] = correlation_matrix[i, j] * volatilities[i] * volatilities[j]
            
            # Submit portfolio analysis task
            task_res = requests.post(f"{API_URL}/tasks/portfolio-monte-carlo-async", json={
                "weights": weights,
                "expected_returns": returns,
                "cov_matrix": cov_matrix.tolist(),
                "initial_value": initial_value,
                "time_horizon": time_horizon,
                "num_simulations": num_simulations
            }).json()
            
            task_id = task_res["task_id"]
            st.info(f"Portfolio analysis started. Task ID: {task_id}")
            
            # Poll for results
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(60):  # Poll for 60 seconds max
                time.sleep(1)
                progress_bar.progress((i + 1) / 60)
                
                status_res = requests.get(f"{API_URL}/tasks/status/{task_id}").json()
                
                if status_res["status"] == "completed":
                    progress_bar.progress(1.0)
                    status_text.success("Analysis completed!")
                    
                    result = status_res["result"]
                    
                    # Display portfolio statistics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Expected Return", f"{result['portfolio_stats']['expected_return']:.2%}")
                        st.metric("Portfolio Volatility", f"{result['portfolio_stats']['volatility']:.2%}")
                    
                    with col2:
                        st.metric("Sharpe Ratio", f"{result['portfolio_stats']['sharpe_ratio']:.2f}")
                        st.metric("Mean Final Value", f"${result['simulation_results']['mean_final_value']:,.0f}")
                    
                    with col3:
                        st.metric("95% VaR", f"${result['risk_metrics']['var_95']:,.0f}")
                        st.metric("99% VaR", f"${result['risk_metrics']['var_99']:,.0f}")
                    
                    with col4:
                        st.metric("95% CVaR", f"${result['risk_metrics']['cvar_95']:,.0f}")
                        st.metric("Max Drawdown", f"${result['risk_metrics']['max_drawdown']:,.0f}")
                    
                    # Portfolio return distribution
                    st.subheader("Portfolio Value Distribution")
                    
                    percentiles = result['simulation_results']['percentiles']
                    
                    # Create distribution plot
                    x_values = list(percentiles.keys())
                    y_values = list(percentiles.values())
                    
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=x_values,
                        y=y_values,
                        name="Portfolio Value Percentiles",
                        marker_color="lightblue"
                    ))
                    
                    fig.update_layout(
                        title="Portfolio Value Percentiles",
                        xaxis_title="Percentile",
                        yaxis_title="Portfolio Value ($)",
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Risk metrics visualization
                    st.subheader("Risk Metrics Summary")
                    
                    risk_data = {
                        'Metric': ['95% VaR', '99% VaR', '95% CVaR', '99% CVaR', 'Max Drawdown'],
                        'Value': [
                            result['risk_metrics']['var_95'],
                            result['risk_metrics']['var_99'],
                            result['risk_metrics']['cvar_95'],
                            result['risk_metrics']['cvar_99'],
                            result['risk_metrics']['max_drawdown']
                        ]
                    }
                    
                    risk_df = pd.DataFrame(risk_data)
                    
                    fig = px.bar(risk_df, x='Metric', y='Value', title='Risk Metrics')
                    fig.update_layout(yaxis_title="Value ($)")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    break
                else:
                    status_text.info(f"Status: {status_res['status']}...")
            
            else:
                st.warning("Analysis is taking longer than expected. Check status manually.")
            
        except Exception as e:
            st.error(f"Error running portfolio analysis: {e}")


# Tab 6: Market Data & Analytics
with tab6:
    st.header("📈 Market Data & Advanced Analytics")
    
    # Volatility Surface
    st.subheader("🌊 Volatility Surface Generator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        surf_S = st.number_input("Current Stock Price", value=100.0, key="surf_S")
        surf_r = st.number_input("Risk-free Rate (%)", value=5.0, key="surf_r") / 100
        base_vol = st.number_input("Base Volatility (%)", value=20.0, min_value=5.0, max_value=100.0) / 100
    
    with col2:
        K_range = st.slider("Strike Range (+/- %)", 10, 80, 40) / 100
        T_max = st.slider("Max Time to Expiration (years)", 0.5, 5.0, 2.0, 0.1)
    
    if st.button("Generate Volatility Surface"):
        try:
            res = requests.get(f"{API_URL}/valuation/volatility-surface", params={
                "S": surf_S, "r": surf_r, "base_vol": base_vol,
                "K_range": K_range, "T_max": T_max
            }).json()
            
            surface_df = pd.DataFrame(res['volatility_surface'])
            
            # Create 3D surface plot
            fig = go.Figure(data=[go.Surface(
                z=surface_df.pivot(index='time_to_expiry', columns='strike', values='volatility').values,
                x=surface_df['strike'].unique(),
                y=surface_df['time_to_expiry'].unique(),
                colorscale='Viridis'
            )])
            
            fig.update_layout(
                title='Implied Volatility Surface',
                scene=dict(
                    xaxis_title='Strike Price',
                    yaxis_title='Time to Expiry',
                    zaxis_title='Implied Volatility'
                ),
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show volatility smile for different expiries
            st.subheader("Volatility Smile by Expiry")
            
            unique_expiries = sorted(surface_df['time_to_expiry'].unique())
            
            fig = go.Figure()
            
            for expiry in unique_expiries[::2]:  # Show every other expiry to avoid clutter
                expiry_data = surface_df[surface_df['time_to_expiry'] == expiry]
                fig.add_trace(go.Scatter(
                    x=expiry_data['moneyness'],
                    y=expiry_data['volatility'],
                    mode='lines+markers',
                    name=f'T = {expiry:.2f}y'
                ))
            
            fig.update_layout(
                title='Volatility Smile (by Moneyness)',
                xaxis_title='Moneyness (ln(K/S))',
                yaxis_title='Implied Volatility',
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error generating volatility surface: {e}")
    
    # Implied Volatility Calculator
    st.subheader("🔍 Implied Volatility Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        market_price = st.number_input("Market Option Price ($)", value=5.0, min_value=0.01, step=0.01)
        iv_S = st.number_input("Stock Price ($)", value=100.0, key="iv_S")
        iv_K = st.number_input("Strike Price ($)", value=100.0, key="iv_K")
    
    with col2:
        iv_T = st.number_input("Time to Expiration (years)", value=0.25, key="iv_T")
        iv_type = st.selectbox("Option Type", ["call", "put"], key="iv_type")
    
    if st.button("Calculate Implied Volatility"):
        try:
            res = requests.post(f"{API_URL}/valuation/implied-volatility", json={
                "option_price": market_price,
                "S": iv_S,
                "K": iv_K,
                "T": iv_T,
                "r": risk_free_rate,
                "option_type": iv_type
            }).json()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Implied Volatility", f"{res['implied_volatility']:.2%}")
            
            with col2:
                st.metric("Market Price", f"${res['market_price']:.4f}")
            
            with col3:
                st.metric("Model Price", f"${res['model_price']:.4f}")
            
            price_diff = res['model_price'] - res['market_price']
            if abs(price_diff) < 0.01:
                st.success("✓ Model price matches market price")
            else:
                st.info(f"Price difference: ${price_diff:.4f}")
                
        except Exception as e:
            st.error(f"Error calculating implied volatility: {e}")
    
    # Task Monitor
    st.subheader("🔍 Task Monitor")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Show Active Tasks"):
            try:
                res = requests.get(f"{API_URL}/tasks/list-active").json()
                st.json(res)
            except Exception as e:
                st.error(f"Error fetching active tasks: {e}")
    
    with col2:
        task_id_to_check = st.text_input("Task ID to Check")
        if st.button("Check Task Status") and task_id_to_check:
            try:
                res = requests.get(f"{API_URL}/tasks/status/{task_id_to_check}").json()
                st.json(res)
            except Exception as e:
                st.error(f"Error checking task status: {e}")
