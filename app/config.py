"""Central settings. Everything can be overridden with environment variables."""
import os

# Shared secret between the bookstore and the (mock) payment gateway.
# Used to sign / verify payment results (OBS-SR-006).
PAYMENT_SECRET = os.getenv("PAYMENT_SECRET", "dev-only-shared-secret")

# How long a login session stays valid.
SESSION_HOURS = int(os.getenv("SESSION_HOURS", "24"))

# The real payment gateway is outside our scope (SRS 1.2), so we ship a mock.
ENABLE_MOCK_GATEWAY = os.getenv("ENABLE_MOCK_GATEWAY", "1") == "1"
