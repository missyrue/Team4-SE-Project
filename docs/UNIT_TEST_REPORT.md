# Unit Test Report

Date of run: 2026-11-11  
Command: `python scripts/generate_test_reports.py` (pytest, tests/unit)

## Summary

| Total | Passed | Failed |
|---|---|---|
| 46 | 46 | 0 |

Unit tests check one function or service on its own: password hashing, price and discount rules, payment signature, inventory rules and catalogue helpers.

## Results by file

### test_catalogue_helpers.py (5/5 passed)

| Test | Result |
|---|---|
| test_all_four_sort_options_exist | PASS |
| test_book_to_dict_availability_boundary_zero_stock | PASS |
| test_book_to_dict_availability_in_stock | PASS |
| test_book_to_dict_detail_includes_description | PASS |
| test_escape_like_makes_wildcards_literal | PASS |

### test_inventory_service.py (21/21 passed)

| Test | Result |
|---|---|
| test_TC_Inv_01_deduct_exactly_all_stock_is_allowed | PASS |
| test_TC_Inv_01_deduct_more_than_stock_raises_and_changes_nothing | PASS |
| test_TC_Inv_01_deduct_stock_reduces_quantity | PASS |
| test_TC_Inv_01_multi_item_deduction_is_all_or_nothing | PASS |
| test_TC_Inv_02_invalid_reorder_level_does_not_partially_update_stock | PASS |
| test_TC_Inv_02_negative_values_are_rejected | PASS |
| test_TC_Inv_02_update_stock_and_reorder_level | PASS |
| test_TC_Inv_02_update_stock_can_change_only_one_field | PASS |
| test_TC_Inv_03_low_stock_books_lists_only_books_at_or_below_level | PASS |
| test_TC_Inv_03_needs_reorder_boundary_at_reorder_level[0-True] | PASS |
| test_TC_Inv_03_needs_reorder_boundary_at_reorder_level[4-True] | PASS |
| test_TC_Inv_03_needs_reorder_boundary_at_reorder_level[5-True] | PASS |
| test_TC_Inv_03_needs_reorder_boundary_at_reorder_level[6-False] | PASS |
| test_deduct_stock_rejects_non_positive_quantity_without_changing_stock[-1] | PASS |
| test_deduct_stock_rejects_non_positive_quantity_without_changing_stock[0] | PASS |
| test_deduct_stock_validates_all_quantities_before_updating | PASS |
| test_get_stock_level | PASS |
| test_restore_stock_adds_quantity_back | PASS |
| test_restore_stock_rejects_missing_book_before_updating_other_books | PASS |
| test_restore_stock_rejects_non_positive_quantity_without_changing_stock[-1] | PASS |
| test_restore_stock_rejects_non_positive_quantity_without_changing_stock[0] | PASS |

### test_passwords.py (6/6 passed)

| Test | Result |
|---|---|
| test_TC_Sec_02_hash_is_not_plaintext | PASS |
| test_TC_Sec_02_same_password_gets_different_salted_hashes | PASS |
| test_correct_password_verifies | PASS |
| test_empty_password_is_rejected | PASS |
| test_malformed_stored_hash_is_rejected_not_crashing | PASS |
| test_wrong_password_is_rejected | PASS |

### test_payment_signature.py (4/4 passed)

| Test | Result |
|---|---|
| test_altered_result_fails_verification | PASS |
| test_empty_or_garbage_signature_fails | PASS |
| test_other_request_id_fails_verification | PASS |
| test_valid_signature_verifies | PASS |

### test_pricing.py (10/10 passed)

| Test | Result |
|---|---|
| test_discount_boundary[1999.99-0.0] | PASS |
| test_discount_boundary[2000.0-200.0] | PASS |
| test_discount_boundary[3000.0-300.0] | PASS |
| test_empty_cart_totals_are_zero | PASS |
| test_free_delivery_boundary[499.99-40.0] | PASS |
| test_free_delivery_boundary[500.0-0.0] | PASS |
| test_free_delivery_boundary[500.01-0.0] | PASS |
| test_large_order_total_is_subtotal_minus_discount | PASS |
| test_rounding_to_two_decimals | PASS |
| test_small_order_pays_delivery_no_discount | PASS |
