# Problem statement

**Who:** students learning to record journal entries (ACC 200-level and up), practicing on their own.

**The problem:** practice sets come with an answer key, so a student finds out *that* an entry is wrong but not *what kind*
of wrong. A reversed entry, a prepaid that was expensed and a forgotten cost-of-goods-sold line all look the same:
"doesn't match the key."

**The tool:** pick a transaction, enter the entry, and get told whether it's right and, if not, which kind of mistake it
is, without being handed the answer.

**What "right" means:** debits equal credits, every account is in the chart of accounts, and each account's net amount
matches the answer key, however the lines are ordered or split. The tests in `tests/test_rules.py` prove it, including
one test per kind of mistake.

**Out of scope:** writing new transactions, grading, saving anyone's work.
