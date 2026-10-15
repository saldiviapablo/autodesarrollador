from invoice import cents, total, allocate
from decimal import Decimal
from pathlib import Path
import unittest


class InvoiceAcceptance(unittest.TestCase):
    def test_monetary_rounding(self):
        self.assertEqual(cents("2.675"), "2.68")
        self.assertEqual(cents("-2.675"), "-2.68")
        self.assertEqual(cents("0"), "0.00")

    def test_totals(self):
        self.assertEqual(total([("2.675", 2), ("1.00", 3)]), "8.35")
        self.assertEqual(total([]), "0.00")

    def test_largest_remainder_and_index_ties(self):
        self.assertEqual(allocate("0.05", [1, 1, 1]), ["0.02", "0.02", "0.01"])
        self.assertEqual(allocate("1.00", [1, 2, 3]), ["0.17", "0.33", "0.50"])

    def test_zero_weight_is_allowed(self):
        self.assertEqual(allocate("1.00", [0, 1]), ["0.00", "1.00"])

    def test_negative_amount_is_rejected(self):
        with self.assertRaises(ValueError):
            allocate("-1.00", [1])

    def test_negative_weight_is_rejected(self):
        with self.assertRaises(ValueError):
            allocate("1.00", [-1, 2])

    def test_zero_total_weight_is_rejected(self):
        with self.assertRaises(ValueError):
            allocate("1.00", [0, 0])

    def test_single_weight(self):
        self.assertEqual(allocate("1.00", [1]), ["1.00"])

    def test_zero_amount_is_allowed(self):
        self.assertEqual(allocate("0.00", [1, 2]), ["0.00", "0.00"])

    def test_cent_conservation(self):
        for number in range(1, 101):
            with self.subTest(number=number):
                value = str(Decimal(number) / 100)
                shares = allocate(value, [1, 2, 3, 5])
                self.assertEqual(sum(map(Decimal, shares)), Decimal(value))
                self.assertEqual(len(shares), 4)

    def test_bad_weights(self):
        for bad in ([], [0, 0], [-1, 2], [1, "bad"]):
            with self.subTest(weights=bad):
                with self.assertRaises(ValueError):
                    allocate("1.00", bad)

    def test_invalid_monetary_amounts(self):
        for bad in ("NaN", "Infinity", "bad"):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    cents(bad)

    def test_readme_documents_approved_contract(self):
        doc = Path("README.md").read_text(encoding="utf-8")
        self.assertIn("ROUND_HALF_UP", doc)
        self.assertIn("largest remainder", doc)
        self.assertIn("https://docs.python.org/3/library/decimal.html", doc)
        normalized = doc.casefold().replace("non-negative", "nonnegative")
        self.assertTrue(any(token in normalized for token in
                            ("nonnegative", "no negativo", ">= 0", ">=0", "≥ 0")),
                        "README must document nonnegative amount and weights")
        self.assertTrue("amount" in normalized or "importe" in normalized,
                        "README must describe the allocation amount")
        self.assertTrue("weight" in normalized or "peso" in normalized,
                        "README must describe allocation weights")
        compact = normalized.replace(" ", "")
        self.assertTrue("zero" in normalized or "cero" in normalized or "[0,1]" in compact,
                        "README must explain that an individual zero weight is allowed")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(InvoiceAcceptance)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("F24_UNIT_DOC_PASS")
    raise SystemExit(0 if result.wasSuccessful() else 1)
