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
    """Structural rules, before comparing with the answer. Returns (clean lines, findings)."""
    findings, clean = [], []
    for i, line in enumerate(lines, 1):
        if not str(line.get("account") or "").strip() and line.get("debit") in (None, "") and line.get("credit") in (None, ""):
            continue                                               # an empty row in the grid: ignore it
        account = parse_account(line.get("account"), chart)
        try:
            debit, credit = money(line.get("debit")), money(line.get("credit"))
        except ValueError as ex:
            findings.append(Finding("not_a_number", f"Line {i}: {ex}."))
            continue
        if account is None:
            findings.append(Finding("unknown_account", f"Line {i}: \"{line.get('account')}\" isn't in the chart of accounts."))
        if (debit is None) == (credit is None):
            findings.append(Finding("one_side", f"Line {i}: enter a debit or a credit, not both and not neither."))
        elif (debit or credit) <= 0:
            findings.append(Finding("one_side", f"Line {i}: amounts must be more than zero."))
        if account is not None:
            clean.append({"account": account, "debit": debit, "credit": credit})
    if not findings and len(clean) < 2:
        findings.append(Finding("empty", "An entry needs at least two lines: something debited and something credited."))
    if not findings:
        dr = sum((l["debit"] or 0) for l in clean)
        cr = sum((l["credit"] or 0) for l in clean)
        if dr != cr:
            findings.append(Finding("unbalanced", f"Debits ({dr:,.2f}) don't equal credits ({cr:,.2f})."))
    return clean, findings


# ---------- rule 2: is it the right entry? --------------------------------------------------------------------------

def net(lines):
    """{account: debit minus credit}, so two entries can be compared however their lines are ordered or split."""
    out = {}
    for l in lines:
        out[l["account"]] = out.get(l["account"], Decimal("0")) + (l["debit"] or 0) - (l["credit"] or 0)
    return {a: v for a, v in out.items() if v != 0}


def compare(lines, answer, chart):
    """Compare a balanced, valid entry with the answer key. Returns a list of findings."""
    mine, right = net(lines), net(answer)
    if mine == right:
        return [Finding("correct", "Correct.")]
    if mine == {a: -v for a, v in right.items()}:
        return [Finding("reversed", "The right accounts and amounts, but debits and credits are reversed.")]
    findings = []
    for a in sorted(mine.keys() & right.keys()):
        if (mine[a] > 0) != (right[a] > 0):
            findings.append(Finding("wrong_side", f"{label(a, chart)} belongs on the other side of the entry."))
        elif mine[a] != right[a]:
            findings.append(Finding("wrong_amount", f"{label(a, chart)}: the amount isn't right."))
    extra = sorted(mine.keys() - right.keys())
    missing = sorted(right.keys() - mine.keys())
    for a in list(extra):                      # pair a wrong account with the one it replaced (same side, same amount)
        b = next((m for m in missing if mine[a] == right[m]), None)
        if b is None:
            continue
        extra.remove(a); missing.remove(b)
        ta, tb = chart[a]["type"], chart[b]["type"]
        if ta == "Expense" and tb == "Asset" and chart[b]["name"].startswith("Prepaid"):
            findings.append(Finding("expensed_prepaid", f"You expensed it ({label(a, chart)}), but the cost covers future months: it's an asset until it's used up."))
        elif ta == "Revenue" and tb == "Liability":
            findings.append(Finding("revenue_too_early", f"You recorded revenue ({label(a, chart)}) before it's earned: until the goods are delivered, Ridgeline owes the customer."))
        elif ta == "Expense" and tb == "Asset":
            findings.append(Finding("expensed_asset", f"You expensed it ({label(a, chart)}), but this purchase is an asset."))
        else:
            findings.append(Finding("wrong_account", f"{label(a, chart)} isn't the right account: this amount belongs in a{'n' if tb[0] in 'AEIOU' else ''} {tb.lower()} account."))
    for a in extra:
        findings.append(Finding("extra_account", f"{label(a, chart)} doesn't belong in this entry."))
    for b in missing:
        t = chart[b]["type"].lower()
        findings.append(Finding("missing_account", f"The entry is missing a{'n' if t[0] in 'aeiou' else ''} {t} account."))
    return findings or [Finding("wrong_entry", "This isn't the right entry.")]


def check_entry(lines, answer, chart):
    """The whole check: (is it right?, findings). Structural problems are reported before comparing with the answer."""
    clean, findings = check_lines(lines, chart)
    if findings:
        return False, findings
    findings = compare(clean, answer, chart)
    return findings[0].code == "correct", findings
