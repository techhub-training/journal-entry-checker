"""The rules: decide whether a journal entry is right, and if not, what kind of mistake it is.

Plain Python, no AI: every decision here is checked by tests/test_rules.py.
An entry is a list of lines, each a dict {"account": "...", "debit": number or None, "credit": number or None}.
"""
import csv
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CENT = Decimal("0.01")


@dataclass
class Finding:
    code: str      # a short name for the kind of mistake, e.g. "unbalanced"; "correct" when the entry is right
    message: str   # what the user sees


# ---------- reading the data ---------------------------------------------------------------------------------------

def load_chart(path="data/chart_of_accounts.csv"):
    """Chart of accounts: {"1000": {"name": "Cash", "type": "Asset", "normal": "Debit"}, ...}"""
    with open(path, newline="") as f:
        return {r["Account"]: {"name": r["Name"], "type": r["Type"], "normal": r["NormalBalance"]} for r in csv.DictReader(f)}


def load_transactions(path="data/transactions.csv"):
    with open(path, newline="") as f:
        return {r["ID"]: r for r in csv.DictReader(f)}


def load_answer_key(path="data/answer_key.csv"):
    """{"T01": [{"account": "1300", "debit": Decimal, "credit": None}, ...], ...}"""
    key = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            key.setdefault(r["ID"], []).append({"account": r["Account"], "debit": money(r["Debit"]), "credit": money(r["Credit"])})
    return key


def money(value):
    """A number typed by a person -> Decimal rounded to cents, or None if blank. Raises ValueError if it isn't a number."""
    if value is None:
        return None
    text = str(value).replace("$", "").replace(",", "").strip()
    if text in ("", "nan", "None"):
        return None
    try:
        return Decimal(text).quantize(CENT, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValueError(f"{value!r} isn't an amount")


def parse_account(text, chart):
    """Accept "1300", "1300 Prepaid Insurance" or "prepaid insurance"; return the account number or None."""
    text = str(text or "").strip()
    if not text:
        return None
    first = text.split()[0]
    if first in chart:
        return first
    by_name = {v["name"].lower(): k for k, v in chart.items()}
    return by_name.get(text.lower())


def label(account, chart):
    return f"{account} {chart[account]['name']}"


# ---------- rule 1: is it a valid entry at all? ---------------------------------------------------------------------

def check_lines(lines, chart):
    """Structural rules, before comparing with the answer. Returns (clean lines, findings).

    TODO (recipe step 3): for each line, skip it if it's completely empty; otherwise
      - parse the account with parse_account(); unknown -> Finding("unknown_account", ...)
      - parse the amounts with money(); not a number -> Finding("not_a_number", ...)
      - exactly one of debit or credit, more than zero -> otherwise Finding("one_side", ...)
    Then: fewer than two lines -> Finding("empty", ...); total debits != total credits -> Finding("unbalanced", ...).
    Return the clean lines ({"account": "1300", "debit": Decimal or None, "credit": Decimal or None}) and the findings.
    """
    return [], [Finding("todo", "The rules aren't written yet (rules.py, check_lines).")]


# ---------- rule 2: is it the right entry? --------------------------------------------------------------------------

def net(lines):
    """{account: debit minus credit}, so two entries can be compared however their lines are ordered or split."""
    out = {}
    for l in lines:
        out[l["account"]] = out.get(l["account"], Decimal("0")) + (l["debit"] or 0) - (l["credit"] or 0)
    return {a: v for a, v in out.items() if v != 0}


def compare(lines, answer, chart):
    """Compare a balanced, valid entry with the answer key. Returns a list of findings.

    TODO (recipe step 3): compare net(lines) with net(answer):
      - the same -> [Finding("correct", "Correct.")]
      - every amount the opposite sign -> Finding("reversed", ...)
      - an account in both, but a different amount -> Finding("wrong_amount", ...)
      - an account the answer doesn't have, in place of one it does (same amount): name the mistake when you can:
        an expense in place of a prepaid -> "expensed_prepaid"; revenue in place of a liability -> "revenue_too_early"
      - otherwise say which TYPE of account is missing, not which account (don't give the answer away).
    """
    return [Finding("todo", "The rules aren't written yet (rules.py, compare).")]


def check_entry(lines, answer, chart):
    """The whole check: (is it right?, findings). Structural problems are reported before comparing with the answer."""
    clean, findings = check_lines(lines, chart)
    if findings:
        return False, findings
    findings = compare(clean, answer, chart)
    return findings[0].code == "correct", findings
