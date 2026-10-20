"""Optional: Claude explains a mistake the rules already found. It never decides whether an entry is right.

Needs ANTHROPIC_API_KEY in .streamlit/secrets.toml (never in the code). The app hides the button without it.
"""
import anthropic
import streamlit as st

import rules

MODEL = "claude-haiku-5-5"


def explain(txn, lines, findings, chart):
    entry = "\n".join(f"  {rules.label(l['account'], chart) if l.get('account') in chart else l.get('account')}: "
                      f"debit {l.get('debit') or ''} credit {l.get('credit') or ''}" for l in lines if l.get("account"))
    problems = "\n".join(f"  - {f.message}" for f in findings)
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model=st.secrets.get("ANTHROPIC_MODEL", MODEL), max_tokens=400,
        system=("You tutor accounting students. A rules engine has already checked a student's journal entry and listed "
                "what is wrong; treat its findings as correct and never contradict them. In at most three short sentences, "
                "explain the accounting idea behind the first finding so the student can fix the entry themselves. "
                "Don't write out the correct entry or its amounts."),
        messages=[{"role": "user", "content": f"Transaction: {txn['Description']}\nStudent's entry:\n{entry}\nFindings:\n{problems}"}],
    )
    # newer models may send a "thinking" block first: take the first text block
    return next(b.text for b in msg.content if b.type == "text").strip()
