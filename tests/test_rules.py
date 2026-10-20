"""Proof that the rules are right. Run from the repository folder:  python -m pytest

Two kinds of test:
  1. The answer key itself is sound, and every answer passes the checker.
  2. Each kind of mistake is caught, and named correctly, on a real transaction.
"""
import os
import sys
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rules  # noqa: E402

CHART = rules.load_chart()
TXNS = rules.load_transactions()
KEY = rules.load_answer_key()


def entry(*lines):
    """entry(("1300", 2400, None), ("1000", None, 2400)) -> lines as the screen sends them."""
    return [{"account": a, "debit": d, "credit": c} for a, d, c in lines]


# ---------- 1. the answer key -------------------------------------------------------------------------------------

def test_every_transaction_has_an_answer():
    assert set(TXNS) == set(KEY)


@pytest.mark.parametrize("tid", sorted(KEY))
def test_answer_key_balances_and_uses_real_accounts(tid):
    lines = KEY[tid]
    assert all(l["account"] in CHART for l in lines)
    assert sum(l["debit"] or 0 for l in lines) == sum(l["credit"] or 0 for l in lines)


@pytest.mark.parametrize("tid", sorted(KEY))
def test_every_answer_passes(tid):
    ok, findings = rules.check_entry(KEY[tid], KEY[tid], CHART)
    assert ok, findings


def test_order_and_split_lines_dont_matter():
    # T05 written differently: cash credit split in two, lines in another order
    mine = entry(("1200", None, 170), ("1000", None, 8000), ("2000", 8500, None), ("1000", None, 330))
    assert rules.check_entry(mine, KEY["T05"], CHART)[0]


def test_accounts_by_name_and_amounts_as_typed():
    mine = entry(("prepaid insurance", "$2,400", None), ("1000 Cash", None, "2400.00"))
    assert rules.check_entry(mine, KEY["T01"], CHART)[0]


# ---------- 2. each kind of mistake ---------------------------------------------------------------------------------

def codes(lines, tid):
    ok, findings = rules.check_entry(lines, KEY[tid], CHART)
    assert not ok
    return [f.code for f in findings]


def test_unbalanced():          # T05 forgetting the discount
    assert codes(entry(("2000", 8500, None), ("1000", None, 8330)), "T05") == ["unbalanced"]


def test_unknown_account():
    assert codes(entry(("Prepaid Insurence", 2400, None), ("1000", None, 2400)), "T01") == ["unknown_account"]


def test_debit_and_credit_on_one_line():
    assert "one_side" in codes(entry(("1300", 2400, 2400), ("1000", None, 2400)), "T01")


def test_not_a_number():
    assert codes(entry(("1300", "two thousand", None), ("1000", None, 2400)), "T01") == ["not_a_number"]


def test_one_line_is_not_an_entry():
    assert codes(entry(("1300", 2400, None)), "T01") == ["empty"]


def test_reversed():
    assert codes(entry(("1000", 3000, None), ("6100", None, 3000)), "T07") == ["reversed"]


def test_expensed_a_prepaid():
    assert codes(entry(("6200", 2400, None), ("1000", None, 2400)), "T01") == ["expensed_prepaid"]


def test_revenue_too_early():
    assert codes(entry(("1000", 600, None), ("4000", None, 600)), "T04") == ["revenue_too_early"]


def test_expensed_an_asset():
    assert codes(entry(("6400", 12000, None), ("1000", None, 2000), ("2500", None, 10000)), "T09") == ["expensed_asset"]


def test_wrong_amount():
    assert codes(entry(("6000", 4500, None), ("1000", None, 4500)), "T08") == ["wrong_amount", "wrong_amount"]


def test_forgot_cost_of_goods_sold():
    found = codes(entry(("1000", 1250, None), ("4000", None, 1250)), "T03")
    assert found == ["missing_account", "missing_account"]


def test_wrong_account_names_the_type_not_the_answer():
    ok, findings = rules.check_entry(entry(("6000", 5100, None), ("2000", None, 5100)), KEY["T13"], CHART)
    assert [f.code for f in findings] == ["wrong_account"]
    assert "liability" in findings[0].message and "Wages Payable" not in findings[0].message


def test_money_rounds_to_cents():
    assert rules.money("1,234.565") == Decimal("1234.57")      # half up, the way accountants round
    assert rules.money("") is None
