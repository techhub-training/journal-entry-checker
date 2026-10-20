"""Journal entry checker: pick a transaction, enter the entry you would book, and check it.

The rules in rules.py decide whether the entry is right.
Run:  streamlit run app.py      Test the rules:  python -m pytest
"""
import pandas as pd
import streamlit as st

import rules

st.set_page_config(page_title="Journal entry checker", layout="wide")
CHART = rules.load_chart()
TXNS = rules.load_transactions()
KEY = rules.load_answer_key()
ACCOUNTS = [rules.label(a, CHART) for a in CHART]

st.title("Journal entry checker")
st.caption("Ridgeline Home & Tool, October 2026. Enter the journal entry for a transaction and check it.")

tid = st.sidebar.selectbox("Transaction", list(TXNS), format_func=lambda t: f"{t}  {TXNS[t]['Description'][:48]}…")
txn = TXNS[tid]
st.subheader(f"{tid} · {txn['Date']}")
st.write(txn["Description"])

blank = pd.DataFrame({"Account": [None] * 3, "Debit": [None] * 3, "Credit": [None] * 3}).astype(
    {"Account": "object", "Debit": "float", "Credit": "float"})
grid = st.data_editor(
    blank, key=f"entry_{tid}", num_rows="dynamic", hide_index=True, width="stretch",
    column_config={"Account": st.column_config.SelectboxColumn("Account", options=ACCOUNTS, width="large"),
                   "Debit": st.column_config.NumberColumn("Debit", min_value=0.0, step=0.01, format="%.2f"),
                   "Credit": st.column_config.NumberColumn("Credit", min_value=0.0, step=0.01, format="%.2f")})
lines = [{"account": None if pd.isna(r["Account"]) else r["Account"], "debit": None if pd.isna(r["Debit"]) else r["Debit"],
          "credit": None if pd.isna(r["Credit"]) else r["Credit"]} for _, r in grid.iterrows()]

# TODO (recipe step 4): a "Check my entry" button that calls rules.check_entry(lines, KEY[tid], CHART) and shows the
# result: st.success when it's right, one st.error per finding when it isn't. Then a "Show the answer" expander.

with st.expander("Chart of accounts"):
    st.dataframe(pd.DataFrame([{"Account": a, **v} for a, v in CHART.items()]), hide_index=True)
