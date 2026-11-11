
import unittest
from fr2_cse350 import connect, add_demo_organizations, create_listing, get_listings


class TestCommunityPosting(unittest.TestCase):

    #set up database
    def setUp(self):
        self.db = connect(":memory:")
        add_demo_organizations(self.db)

        self.volunteer = {
            "category": "volunteer",
            "title": "Park Cleanup",
            "location": "Louisville, KY",
            "description": "Help clean the park",
            "need_date": "2026-11-20",
            "shift_time": "10:00",
            "capacity": "5"
        }

        self.donation = {
            "category": "donation",
            "title": "Food Drive",
            "location": "Louisville, KY",
            "description": "Collect canned food",
            "item_name": "Canned goods",
            "item_quantity": "20"
        }

    def tearDown(self):
        self.db.close()

    #test volunteer posting
    def test_01_volunteer(self):
        listing_id = create_listing(self.db, 1, self.volunteer)
        self.assertEqual(listing_id, 1)

    #donation posting
    def test_02_donation(self):
        listing_id = create_listing(self.db, 1, self.donation)
        self.assertEqual(listing_id, 1)

    #test unverified organization
    def test_03_unverified(self):
        with self.assertRaises(PermissionError):
            create_listing(self.db, 2, self.volunteer)

    #test organization that does not exist
    def test_04_unknown_organization(self):
        with self.assertRaises(PermissionError):
            create_listing(self.db, 999, self.volunteer)

    #test missing title
    def test_05_missing_title(self):
        self.volunteer["title"] = ""
        with self.assertRaises(ValueError):
            create_listing(self.db, 1, self.volunteer)

    #test zero volunteers
    def test_06_zero_capacity(self):
        self.volunteer["capacity"] = "0"
        with self.assertRaises(ValueError):
            create_listing(self.db, 1, self.volunteer)

    #test invalid item quantity
    def test_07_invalid_quantity(self):
        self.donation["item_quantity"] = "abc"
        with self.assertRaises(ValueError):
            create_listing(self.db, 1, self.donation)

    #check if listing saved
    def test_08_saved_listing(self):
        create_listing(self.db, 1, self.volunteer)
        listings = get_listings(self.db)
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0]["title"], "Park Cleanup")

    #test invalid date
    def test_09_invalid_date(self):
        self.volunteer["need_date"] = "wrong"
        with self.assertRaises(ValueError):
            create_listing(self.db, 1, self.volunteer)

    #test special characters
    def test_10_special_text(self):
        self.volunteer["title"] = "Cleanup'); DROP TABLE listings; --"
        create_listing(self.db, 1, self.volunteer)
        listings = get_listings(self.db)
        self.assertEqual(listings[0]["title"], self.volunteer["title"])

    #test wrong listing type
    def test_11_wrong_category(self):
        self.volunteer["category"] = "other"
        with self.assertRaises(ValueError):
            create_listing(self.db, 1, self.volunteer)

    #test blank description
    def test_12_blank_description(self):
        self.donation["description"] = " "
        with self.assertRaises(ValueError):
            create_listing(self.db, 1, self.donation)

if __name__ == "__main__":
    unittest.main()
