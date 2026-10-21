# Journal entry checker

Pick a Ridgeline Home & Tool transaction, enter the journal entry you would book, and check it. The checker says whether
the entry is right and, if not, what kind of mistake it is ("you expensed a prepaid", "debits and credits are reversed")
without giving away the answer.

**Live:** https://journal-entry-checker.streamlit.app (replace with your own app's address)

## Use it

1. Pick a transaction in the sidebar.
2. Enter the entry in the grid: one line per account, a debit or a credit on each. Add rows with **+**.
3. Click **Check my entry**. Stuck? **Show the answer**.

## How we know it's right

The rules (`rules.py`) are plain Python: no AI decides anything. `tests/test_rules.py` checks that

* the answer key balances and uses real accounts, and every answer passes;
* the order of lines and split lines don't matter;
* each kind of mistake is caught and named: unbalanced, unknown account, both sides on one line, reversed, expensed a
  prepaid, revenue recorded too early, expensed an asset, wrong amount, missing account.

Run them: `python -m pytest` (48 tests).

## Run it yourself

Open this repository in a codespace (**Code › Codespaces › Create codespace on main**): the app starts by itself. Or, with
Python 3.10+: `pip install -r requirements.txt`, then `streamlit run app.py`.

**Optional:** to let Claude explain a mistake in words, put `ANTHROPIC_API_KEY = "sk-ant-..."` in
`.streamlit/secrets.toml` (never in the code). Claude only explains what the rules found; it never decides whether an
entry is right.

## Files

| File | What it is |
|---|---|
| `PROBLEM.md` | Who the tool is for and what "right" means |
| `data/chart_of_accounts.csv` | 23 accounts with type and normal balance |
| `data/transactions.csv` | 16 October 2026 transactions |
| `data/answer_key.csv` | The correct entry for each, one row per line |
| `rules.py` | The checks |
| `tests/test_rules.py` | The proof |
| `app.py` | The screen |
| `explain.py` | Optional Claude explanation |

## Built by

The ACC 407 class, Winter 2027, in the Mar 9 guided build, with an AI coding assistant. Transactions are fictional.
