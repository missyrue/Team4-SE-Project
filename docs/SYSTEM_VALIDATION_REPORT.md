# System Validation Report

Date of run: 2026-11-11  
Scope: integration and system tests (tests/integration, tests/test_smoke.py). Each test calls the real API with a fresh temporary database, so the router, rules and database work together.

## Summary

| Total | Passed | Failed |
|---|---|---|
| 128 | 128 | 0 |

## Requirement traceability (SRS -> test case -> automated result)

| Requirement | Title | Test case(s) | Automated in | Result |
|---|---|---|---|---|
| OBS-F-001 | Create customer account (unique email + password) | TC-Auth-01 | test_auth_api.py | PASS |
| OBS-F-002 | Customer login with valid credentials | TC-Auth-02 | test_auth_api.py | PASS |
| OBS-F-003 | Customer logout ends session | TC-Auth-03 | test_auth_api.py | PASS |
| OBS-F-004 | Display active books (title, author, price, category, availability) | TC-Cat-01 | test_catalogue_api.py | PASS |
| OBS-F-005 | Search books by title, author or ISBN | TC-Cat-02 | test_catalogue_api.py | PASS |
| OBS-F-006 | Filter books by category and price range | TC-Cat-03 | test_catalogue_api.py | PASS |
| OBS-F-007 | Sort books by title or price | TC-Cat-04 | test_catalogue_api.py | PASS |
| OBS-F-008 | Book detail page | TC-Book-01 | test_catalogue_api.py | PASS |
| OBS-F-009 | Add available book + quantity to cart | TC-Cart-01 | test_cart_api.py | PASS |
| OBS-F-010 | Change quantity / remove item in cart | TC-Cart-02 | test_cart_api.py | PASS |
| OBS-F-011 | Prevent quantity above available stock | TC-Cart-03 | test_cart_api.py | PASS |
| OBS-F-012 | Collect delivery address and contact details at checkout | TC-Order-01 | test_checkout_orders_api.py | PASS |
| OBS-F-013 | Calculate order total (prices, delivery, discounts) | TC-Order-02 | test_checkout_orders_api.py, test_pricing.py | PASS |
| OBS-F-014 | Send payment request to external payment service | TC-Pay-01 | test_checkout_orders_api.py | PASS |
| OBS-F-015 | Mark paid only after valid successful payment response | TC-Pay-02 | test_checkout_orders_api.py | PASS |
| OBS-F-016 | Unique order number after confirmation | TC-Order-03 | test_checkout_orders_api.py | PASS |
| OBS-F-017 | Reduce stock only after confirmed order | TC-Inv-01, TC-Cart-04 | test_checkout_orders_api.py, test_inventory_service.py | PASS |
| OBS-F-018 | Customer order history and status | TC-Order-04 | test_checkout_orders_api.py | PASS |
| OBS-F-019 | Customer cancels order before non-cancellable status | TC-Order-05 | test_checkout_orders_api.py | PASS |
| OBS-F-020 | Admin adds new book | TC-Admin-01 | test_admin_api.py | PASS |
| OBS-F-021 | Admin edits / deactivates book | TC-Admin-02 | test_admin_api.py | PASS |
| OBS-F-022 | Admin creates / updates categories | TC-Admin-03 | test_admin_api.py | PASS |
| OBS-F-023 | Admin updates stock quantity and reorder level | TC-Inv-02 | test_admin_api.py, test_inventory_service.py | PASS |
| OBS-F-024 | Identify books at or below reorder level | TC-Inv-03 | test_admin_api.py, test_inventory_service.py | PASS |
| OBS-F-025 | Admin updates order status | TC-Admin-04 | test_admin_api.py | PASS |
| OBS-F-026 | Admin sales and inventory reports for a period | TC-Rep-01 | test_admin_api.py | PASS |
| OBS-NF-001 | Catalogue/search/detail pages respond within 3 s (p90) | TC-Perf-01 | test_scale_performance.py | PASS |
| OBS-NF-002 | 99.5% monthly availability (health endpoint + measurement plan) | TC-Reliability-01 | - | Not automated (see Test Summary) |
| OBS-NF-003 | First-time user can search and add to cart without training | TC-UX-01 | - | Not automated (see Test Summary) |
| OBS-NF-004 | Support 10,000 books and 20 concurrent sessions | TC-Scale-01 | test_scale_performance.py | PASS |
| OBS-NF-005 | Usable on desktop, tablet and mobile screen sizes | TC-UX-02 | - | Not automated (see Test Summary) |
| OBS-NF-006 | Audit trail of administrator changes | TC-Audit-01 | test_admin_api.py | PASS |
| OBS-SR-001 | Authentication required for protected functions | TC-Sec-01 | test_admin_api.py, test_auth_api.py | PASS |
| OBS-SR-002 | Passwords stored as salted one-way hashes | TC-Sec-02 | test_auth_api.py, test_passwords.py | PASS |
| OBS-SR-003 | Role-based access control (customer vs admin) | TC-Sec-03 | test_admin_api.py | PASS |
| OBS-SR-004 | Secure (TLS) communication for account/order/payment traffic | TC-Sec-04 | - | Not automated (see Test Summary) |
| OBS-SR-005 | Validate and sanitise input (account, search, address, admin forms) | TC-Sec-05 | test_auth_api.py, test_catalogue_api.py | PASS |
| OBS-SR-006 | Verify payment-service response before marking paid | TC-Sec-06 | test_checkout_orders_api.py, test_payment_signature.py | PASS |

## Results by file

### test_admin_api.py (39/39 passed)

| Test | Result |
|---|---|
| test_TC_Admin_01_add_book_appears_in_public_catalogue | PASS |
| test_TC_Admin_01_duplicate_isbn_is_rejected | PASS |
| test_TC_Admin_01_invalid_book_data_is_rejected[overrides0] | PASS |
| test_TC_Admin_01_invalid_book_data_is_rejected[overrides1] | PASS |
| test_TC_Admin_01_invalid_book_data_is_rejected[overrides2] | PASS |
| test_TC_Admin_01_invalid_book_data_is_rejected[overrides3] | PASS |
| test_TC_Admin_01_invalid_book_data_is_rejected[overrides4] | PASS |
| test_TC_Admin_01_invalid_book_data_is_rejected[overrides5] | PASS |
| test_TC_Admin_02_deactivated_book_is_hidden_and_cannot_be_bought | PASS |
| test_TC_Admin_02_edit_book_saves_changes | PASS |
| test_TC_Admin_02_unknown_book_is_404 | PASS |
| test_TC_Admin_03_create_and_rename_category_reflected_in_filtering | PASS |
| test_TC_Admin_03_duplicate_or_blank_category_is_rejected | PASS |
| test_TC_Admin_04_admin_cancel_restores_stock | PASS |
| test_TC_Admin_04_invalid_status_change_is_rejected | PASS |
| test_TC_Admin_04_status_update_is_visible_to_the_customer | PASS |
| test_TC_Audit_01_every_admin_change_is_recorded_with_user_action_record_and_time | PASS |
| test_TC_Audit_01_failed_changes_are_not_logged | PASS |
| test_TC_Inv_02_negative_stock_or_empty_update_is_rejected | PASS |
| test_TC_Inv_02_update_stock_is_reflected_in_availability | PASS |
| test_TC_Inv_03_low_stock_list_contains_only_books_at_or_below_level | PASS |
| test_TC_Inv_03_update_response_flags_low_stock_immediately | PASS |
| test_TC_Rep_01_end_date_is_inclusive | PASS |
| test_TC_Rep_01_inventory_report_counts_match | PASS |
| test_TC_Rep_01_period_filter_excludes_orders_outside_the_period | PASS |
| test_TC_Rep_01_sales_report_totals_match_stored_orders | PASS |
| test_TC_Rep_01_start_after_end_or_bad_date_is_rejected | PASS |
| test_TC_Sec_01_admin_endpoints_need_login[get-/api/admin/audit-log] | PASS |
| test_TC_Sec_01_admin_endpoints_need_login[get-/api/admin/books] | PASS |
| test_TC_Sec_01_admin_endpoints_need_login[get-/api/admin/inventory/low-stock] | PASS |
| test_TC_Sec_01_admin_endpoints_need_login[get-/api/admin/orders] | PASS |
| test_TC_Sec_01_admin_endpoints_need_login[get-/api/admin/reports/inventory] | PASS |
| test_TC_Sec_03_customer_cannot_create_books_or_change_orders | PASS |
| test_TC_Sec_03_customer_cannot_use_admin_endpoints[get-/api/admin/audit-log] | PASS |
| test_TC_Sec_03_customer_cannot_use_admin_endpoints[get-/api/admin/books] | PASS |
| test_TC_Sec_03_customer_cannot_use_admin_endpoints[get-/api/admin/inventory/low-stock] | PASS |
| test_TC_Sec_03_customer_cannot_use_admin_endpoints[get-/api/admin/orders] | PASS |
| test_TC_Sec_03_customer_cannot_use_admin_endpoints[get-/api/admin/reports/inventory] | PASS |
| test_admin_can_list_and_filter_all_orders | PASS |

### test_auth_api.py (15/15 passed)

| Test | Result |
|---|---|
| test_TC_Auth_01_duplicate_email_rejected | PASS |
| test_TC_Auth_01_invalid_email_rejected | PASS |
| test_TC_Auth_01_missing_fields_rejected | PASS |
| test_TC_Auth_01_password_boundary_7_chars_rejected_8_accepted | PASS |
| test_TC_Auth_01_password_needs_letter_and_digit | PASS |
| test_TC_Auth_01_register_valid_creates_account | PASS |
| test_TC_Auth_02_login_with_valid_credentials | PASS |
| test_TC_Auth_02_unknown_email_rejected_with_same_message | PASS |
| test_TC_Auth_02_wrong_password_rejected | PASS |
| test_TC_Auth_03_logout_ends_session | PASS |
| test_TC_Sec_01_protected_endpoint_without_login_is_401 | PASS |
| test_TC_Sec_02_database_never_stores_plaintext_password | PASS |
| test_TC_Sec_05_script_in_name_is_stored_as_plain_text_only | PASS |
| test_TC_Sec_05_sql_injection_in_login_does_not_log_in | PASS |
| test_registering_cannot_create_an_admin | PASS |

### test_cart_api.py (15/15 passed)

| Test | Result |
|---|---|
| test_TC_Cart_01_add_book_shows_item_and_correct_subtotal | PASS |
| test_TC_Cart_01_adding_same_book_again_increases_quantity | PASS |
| test_TC_Cart_01_quantity_zero_or_negative_is_rejected | PASS |
| test_TC_Cart_01_unknown_or_inactive_book_is_404 | PASS |
| test_TC_Cart_02_change_quantity_recalculates_total | PASS |
| test_TC_Cart_02_remove_item | PASS |
| test_TC_Cart_02_remove_item_not_in_cart_is_404 | PASS |
| test_TC_Cart_03_cumulative_quantity_cannot_exceed_stock | PASS |
| test_TC_Cart_03_out_of_stock_book_cannot_be_added | PASS |
| test_TC_Cart_03_quantity_above_stock_is_rejected_with_message | PASS |
| test_TC_Cart_03_quantity_equal_to_stock_is_allowed | PASS |
| test_TC_Cart_03_updating_quantity_above_stock_is_rejected | PASS |
| test_cart_preview_includes_delivery_and_discount | PASS |
| test_cart_requires_login | PASS |
| test_each_customer_has_their_own_cart | PASS |

### test_catalogue_api.py (16/16 passed)

| Test | Result |
|---|---|
| test_TC_Book_01_detail_shows_full_information | PASS |
| test_TC_Book_01_unknown_or_inactive_book_is_404 | PASS |
| test_TC_Cat_01_lists_active_books_with_required_fields | PASS |
| test_TC_Cat_01_out_of_stock_book_shows_availability | PASS |
| test_TC_Cat_02_no_match_returns_204_no_content | PASS |
| test_TC_Cat_02_percent_is_not_a_wildcard | PASS |
| test_TC_Cat_02_search_by_title_author_and_isbn | PASS |
| test_TC_Cat_03_filter_by_category | PASS |
| test_TC_Cat_03_filter_by_price_range_boundaries_are_inclusive | PASS |
| test_TC_Cat_03_min_greater_than_max_is_rejected | PASS |
| test_TC_Cat_03_negative_price_rejected | PASS |
| test_TC_Cat_04_sort_by_title_and_price | PASS |
| test_TC_Cat_04_unknown_sort_option_rejected | PASS |
| test_TC_Sec_05_sql_injection_in_search_is_harmless | PASS |
| test_categories_endpoint_lists_categories | PASS |
| test_pagination_limit_and_offset | PASS |

### test_checkout_orders_api.py (37/37 passed)

| Test | Result |
|---|---|
| test_TC_Cart_04_failed_payment_does_not_reduce_stock | PASS |
| test_TC_Cart_04_stock_untouched_while_payment_is_pending | PASS |
| test_TC_Inv_01_confirmed_payment_reduces_stock_by_ordered_quantity | PASS |
| test_TC_Order_01_address_exactly_10_characters_is_accepted | PASS |
| test_TC_Order_01_checkout_rejects_missing_or_invalid_details[-9876543210] | PASS |
| test_TC_Order_01_checkout_rejects_missing_or_invalid_details[12 MG Road, Bengaluru 560001-12345] | PASS |
| test_TC_Order_01_checkout_rejects_missing_or_invalid_details[12 MG Road, Bengaluru 560001-98765abcde] | PASS |
| test_TC_Order_01_checkout_rejects_missing_or_invalid_details[12 MG Road, Bengaluru 560001-] | PASS |
| test_TC_Order_01_checkout_rejects_missing_or_invalid_details[short-9876543210] | PASS |
| test_TC_Order_01_checkout_with_valid_details_creates_pending_order | PASS |
| test_TC_Order_01_empty_cart_cannot_checkout | PASS |
| test_TC_Order_02_order_total_matches_displayed_cart_total | PASS |
| test_TC_Order_02_total_with_free_delivery_and_discount | PASS |
| test_TC_Order_03_each_confirmed_order_gets_a_unique_order_number | PASS |
| test_TC_Order_03_no_order_number_before_payment_is_confirmed | PASS |
| test_TC_Order_04_customer_sees_only_their_own_orders | PASS |
| test_TC_Order_05_cancel_paid_order_gives_stock_back | PASS |
| test_TC_Order_05_cancel_pending_order | PASS |
| test_TC_Order_05_non_cancellable_order_is_rejected_with_message[cancelled] | PASS |
| test_TC_Order_05_non_cancellable_order_is_rejected_with_message[delivered] | PASS |
| test_TC_Order_05_non_cancellable_order_is_rejected_with_message[payment_failed] | PASS |
| test_TC_Order_05_non_cancellable_order_is_rejected_with_message[shipped] | PASS |
| test_TC_Pay_01_payment_request_has_order_amount_and_gateway_returns_signed_result | PASS |
| test_TC_Pay_02_failed_result_does_not_mark_order_paid | PASS |
| test_TC_Pay_02_successful_signed_result_marks_order_paid | PASS |
| test_TC_Sec_06_missing_gateway_response_leaves_order_unpaid | PASS |
| test_TC_Sec_06_payment_for_a_different_request_id_is_rejected | PASS |
| test_TC_Sec_06_tampered_payment_result_is_rejected_and_order_not_paid | PASS |
| test_TC_Sec_06_unknown_order_is_404 | PASS |
| test_cannot_cancel_someone_elses_order | PASS |
| test_cart_is_emptied_after_successful_payment | PASS |
| test_cart_is_kept_after_failed_payment_so_customer_can_retry | PASS |
| test_checkout_of_someone_elses_cart_is_404 | PASS |
| test_checkout_requires_login | PASS |
| test_failed_order_cannot_be_flipped_to_paid_later | PASS |
| test_last_copy_cannot_be_sold_twice | PASS |
| test_replayed_success_result_is_idempotent_and_deducts_stock_once | PASS |

### test_end_to_end_flow.py (2/2 passed)

| Test | Result |
|---|---|
| test_failed_payment_journey_keeps_stock_and_allows_retry | PASS |
| test_full_purchase_journey | PASS |

### test_scale_performance.py (2/2 passed)

| Test | Result |
|---|---|
| test_TC_Perf_01_and_Scale_01_20_concurrent_sessions_p90_under_3_seconds | PASS |
| test_TC_Scale_01_catalogue_holds_10000_records | PASS |

### test_smoke.py (2/2 passed)

| Test | Result |
|---|---|
| test_app_starts_and_health_endpoint_answers | PASS |
| test_home_page_is_served | PASS |

## Limits

Usability results with real people are recorded in docs/USABILITY_TEST.md. Automated tests cannot prove the absence of every defect.