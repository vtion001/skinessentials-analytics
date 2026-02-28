import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime

# Simple test dashboard
st.set_page_config(page_title="Test Dashboard", page_icon="📊", layout="wide")

st.title("📊 Test Dashboard")
st.markdown(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")

st.metric("Test Metric", "42", "+5%")

st.write("If you can see this, Streamlit is working correctly!")
