"""Tests for lead notify event stats."""
from leads_db import get_notify_channel_stats, init_leads_db, record_notify_event


class TestLeadNotifyStats:
    def test_channel_stats_aggregation(self):
        init_leads_db()
        channel = "pytest_stats_channel"
        record_notify_event(1, channel, success=True, source="test")
        record_notify_event(2, channel, success=False, source="failure")
        rows = {row["channel"]: row for row in get_notify_channel_stats(days=30)}
        assert rows[channel]["success_count"] == 1
        assert rows[channel]["failure_count"] == 1
