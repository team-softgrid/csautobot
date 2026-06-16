import unittest
from storage.db import get_db_context
from storage.repositories import (
    Tenant, Site, Charger, Incident, Action, PartUsage
)
from csautobot.build_index import load_docs

class TestDBIngest(unittest.TestCase):
    def test_database_records_exist(self):
        with get_db_context() as db:
            site_count = db.query(Site).count()
            charger_count = db.query(Charger).count()
            incident_count = db.query(Incident).count()
            action_count = db.query(Action).count()
            
            self.assertGreater(site_count, 0, "No sites ingested in DB")
            self.assertGreater(charger_count, 0, "No chargers ingested in DB")
            self.assertGreater(incident_count, 0, "No incidents ingested in DB")
            self.assertGreater(action_count, 0, "No actions ingested in DB")
            
    def test_load_docs_returns_documents(self):
        docs = load_docs()
        self.assertGreater(len(docs), 0, "load_docs() returned no documents")
        for doc in docs:
            self.assertIsNotNone(doc.page_content)
            self.assertIsNotNone(doc.metadata)
            self.assertIn("source", doc.metadata)
            self.assertIn("sheet", doc.metadata)
            self.assertIn("row", doc.metadata)

if __name__ == "__main__":
    unittest.main()
