


   
import hashlib
import io
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from unittest.mock import patch

import FR1_User_Login_Python as FR1
import FR3
import Claim as FR4claim
import Pledge as FR4pledge


class DatabaseTestCase(unittest.TestCase):
    """Give every test independent user and opportunity databases."""

    def setUp(self):
        self.email = "volunteer@test.com"

        self.users = {
            self.email: {
                "password": FR1.hash_password("secure123"),
                "account_type": "volunteer",
            },
            "other@test.com": {
                "password": FR1.hash_password("other123"),
                "account_type": "volunteer",
            },
            "shelter@test.com": {
                "password": FR1.hash_password("password456"),
                "account_type": "Non-Profit",
            },
        }

        self.jobs = {
            1: {
                "id": 1,
                "title": "Food Bank Volunteers",
                "organization": "Community Food Bank",
                "description": "Help pack food boxes for local families.",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701",
                "date": "2026-12-05",
                "listing_type": "volunteer",
                "donation_type": None,
                "status": "published",
                "available": True,
            },
            2: {
                "id": 2,
                "title": "Winter Clothing Drive",
                "organization": "Neighborhood Shelter",
                "description": "Donate coats, gloves, and warm clothing.",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78702",
                "date": "2026-12-06",
                "listing_type": "donation",
                "donation_type": "clothes",
                "status": "published",
                "available": True,
                "pledges": [],
            },
            3: {
                "id": 3,
                "title": "Food Donation Drive",
                "organization": "Dallas Pantry",
                "description": "Donate canned goods.",
                "city": "Dallas",
                "state": "TX",
                "zip_code": "75201",
                "date": "2026-12-07",
                "listing_type": "donation",
                "donation_type": "food",
                "status": "published",
                "available": True,
                "pledges": [],
            },
        }

        bindings = [
            (FR1, "user_database", self.users),
            (FR3, "publishedjobs_database", self.jobs),
            (FR4claim, "user_database", self.users),
            (FR4claim, "publishedjobs_database", self.jobs),
            (FR4pledge, "user_database", self.users),
            (FR4pledge, "publishedjobs_database", self.jobs),
        ]

        for module, name, database in bindings:
            patcher = patch.object(module, name, database, create=True)
            patcher.start()
            self.addCleanup(patcher.stop)

    def capture_output(self, function, *args):
        output = io.StringIO()
        with redirect_stdout(output):
            function(*args)
        return output.getvalue()


class TestFR1(DatabaseTestCase):

    def test_successful_registration(self):
        result = FR1.register_account(
            "new@test.com", "newpass123", "Volunteer"
        )

        self.assertEqual(
            result,
            "Success: Volunteer account created for new@test.com!",
        )
        self.assertEqual(
            self.users["new@test.com"]["account_type"], "Volunteer"
        )

    def test_duplicate_registration_preserves_original_account(self):
        original = deepcopy(self.users[self.email])

        result = FR1.register_account(
            self.email, "replacement-password", "Non-Profit"
        )

        self.assertEqual(
            result,
            "Error: Account with this email already exists.",
        )
        self.assertEqual(self.users[self.email], original)

    def test_password_is_stored_as_sha256_not_plaintext(self):
        password = "newpass123"
        FR1.register_account("new@test.com", password, "Volunteer")

        stored = self.users["new@test.com"]["password"]
        expected = hashlib.sha256(password.encode()).hexdigest()

        self.assertEqual(stored, expected)
        self.assertNotEqual(stored, password)
        self.assertEqual(len(stored), 64)

    def test_hash_matches_known_sha256_value(self):
        self.assertEqual(
            FR1.hash_password("abc"),
            "ba7816bf8f01cfea414140de5dae2223"
            "b00361a396177a9cb410ff61f20015ad",
        )

    def test_same_password_produces_same_hash(self):
        self.assertEqual(
            FR1.hash_password("secure123"),
            FR1.hash_password("secure123"),
        )

    def test_different_passwords_produce_different_hashes(self):
        self.assertNotEqual(
            FR1.hash_password("secure123"),
            FR1.hash_password("wrongpass"),
        )

    def test_successful_login(self):
        self.assertEqual(
            FR1.login_user(self.email, "secure123"),
            "Success: Logged in as volunteer.",
        )

    def test_unknown_email_login(self):
        self.assertEqual(
            FR1.login_user("missing@test.com", "secure123"),
            "Error: Account not found.",
        )

    def test_password_mismatch(self):
        original = deepcopy(self.users[self.email])

        self.assertEqual(
            FR1.login_user(self.email, "wrongpass"),
            "Error: Invalid password.",
        )
        self.assertEqual(self.users[self.email], original)


class TestFR3(DatabaseTestCase):

    def test_invalid_sort(self):
        for value in ("invalid", "title", "", "DATE"):
            with self.subTest(sort_by=value):
                with self.assertRaises(ValueError) as error:
                    FR3.search_jobs(sort_by=value)

                self.assertEqual(
                    str(error.exception),
                    "sort_by must be date, city, listing_type, "
                    "or donation_type.",
                )

    def test_only_published_available_jobs_are_returned(self):
        original = deepcopy(self.jobs[1])

        for field, value in (
            ("status", "draft"),
            ("status", "taken"),
            ("status", None),
            ("available", False),
            ("available", None),
        ):
            with self.subTest(field=field, value=value):
                self.jobs[1] = deepcopy(original)
                self.jobs[1][field] = value
                ids = [job["id"] for job in FR3.search_jobs()]
                self.assertNotIn(1, ids)

        for field in ("status", "available"):
            with self.subTest(missing=field):
                self.jobs[1] = deepcopy(original)
                del self.jobs[1][field]
                ids = [job["id"] for job in FR3.search_jobs()]
                self.assertNotIn(1, ids)

    def test_individual_filters(self):
        cases = [
            ({"city": "Dallas"}, [3]),
            ({"state": "TX"}, [1, 2, 3]),
            ({"zip_code": "78701"}, [1]),
            ({"date": "2026-12-06"}, [2]),
            ({"listing_type": "donation"}, [2, 3]),
            ({"donation_type": "clothes"}, [2]),
        ]

        for filters, expected in cases:
            with self.subTest(filters=filters):
                results = FR3.search_jobs(**filters)
                self.assertEqual(
                    [job["id"] for job in results], expected
                )

    def test_filters_ignore_case_and_surrounding_whitespace(self):
        results = FR3.filter_jobs(
            city="  AUSTIN  ",
            state=" tx ",
            listing_type=" DONATION ",
            donation_type=" CLOTHES ",
        )

        self.assertEqual([job["id"] for job in results], [2])

    def test_combined_filters(self):
        results = FR3.filter_jobs(
            city="Austin",
            zip_code="78701",
            date="2026-12-05",
            listing_type="volunteer",
        )

        self.assertEqual([job["id"] for job in results], [1])

    def test_keyword_searches_title_description_and_organization(self):
        cases = [
            (" WINTER ", [2]),
            ("canned goods", [3]),
            ("Neighborhood Shelter", [2]),
        ]

        for keyword, expected in cases:
            with self.subTest(keyword=keyword):
                results = FR3.search_jobs(keyword=keyword)
                self.assertEqual(
                    [job["id"] for job in results], expected
                )

    def test_no_matching_results(self):
        self.assertEqual(FR3.search_jobs(city="Unknown City"), [])

    def test_whitespace_filter_is_ignored(self):
        self.assertEqual(
            FR3.search_jobs(city=" \t\n "),
            FR3.search_jobs(),
        )

    def test_donation_filter_excludes_volunteer_listings(self):
        self.jobs[1]["donation_type"] = "food"

        results = FR3.donation_type_filter("food")

        self.assertEqual([job["id"] for job in results], [3])

    def test_valid_sort_fields(self):
        cases = {
            "date": [1, 2, 3],
            "city": [1, 2, 3],
            "listing_type": [2, 3, 1],
            "donation_type": [2, 3, 1],
        }

        for field, expected in cases.items():
            with self.subTest(sort_by=field):
                results = FR3.search_jobs(sort_by=field)
                self.assertEqual(
                    [job["id"] for job in results], expected
                )

    def test_sort_missing_values_last_and_break_ties_by_id(self):
        self.jobs[1]["city"] = "austin"
        self.jobs[2]["city"] = " Austin "
        del self.jobs[3]["city"]

        results = FR3.search_jobs(sort_by="city")

        self.assertEqual([job["id"] for job in results], [1, 2, 3])

    def test_clear_filters_returns_all_eligible_jobs(self):
        self.jobs[3]["status"] = "draft"
        FR3.filter_jobs(listing_type="volunteer")

        results = FR3.clear_filters()

        self.assertEqual([job["id"] for job in results], [1, 2])

    def test_search_does_not_modify_database(self):
        original = deepcopy(self.jobs)

        FR3.search_jobs(keyword="food", sort_by="date")

        self.assertEqual(self.jobs, original)

    def test_display_no_results(self):
        self.assertEqual(
            self.capture_output(FR3.display_results, []),
            "No matching opportunities found.\n",
        )


class TestFR4Claim(DatabaseTestCase):

    def assert_claim_rejected(self, email, job_id, expected):
        users_before = deepcopy(self.users)
        jobs_before = deepcopy(self.jobs)

        self.assertEqual(FR4claim.claim_job(email, job_id), expected)
        self.assertEqual(self.users, users_before)
        self.assertEqual(self.jobs, jobs_before)

    def test_unknown_user(self):
        self.assert_claim_rejected(
            "mising@test.com",
            1,
            "Error: User account not found.",
        )

    def test_non_volunteer(self):
        self.assert_claim_rejected(
            "shelter@test.com",
            1,
            "Error: Only volunteers can claim opportunities.",
        )

    def test_account_type_is_case_insensitive(self):
        original = deepcopy(self.jobs[1])

        for account_type in ("Volunteer", "VOLUNTEER"):
            with self.subTest(account_type=account_type):
                self.jobs[1] = deepcopy(original)
                self.users[self.email]["account_type"] = account_type
                self.users[self.email].pop("claimed_jobs", None)

                self.assertEqual(
                    FR4claim.claim_job(self.email, 1),
                    f"Success: Job 'Food Bank Volunteers' "
                    f"claimed by {self.email}!",
                )

    def test_unknown_job(self):
        self.assert_claim_rejected(
            self.email, 999, "Error: Opportunity not found."
        )

    def test_not_published_or_missing_status(self):
        for status in ("draft", "taken", None):
            with self.subTest(status=status):
                if status is None:
                    self.jobs[1].pop("status", None)
                else:
                    self.jobs[1]["status"] = status

                self.assert_claim_rejected(
                    self.email,
                    1,
                    "Error: This opportunity is not published.",
                )

    def test_unavailable_or_missing_availability(self):
        for missing in (False, True):
            with self.subTest(missing=missing):
                if missing:
                    self.jobs[1].pop("available", None)
                else:
                    self.jobs[1]["available"] = False

                self.assert_claim_rejected(
                    self.email,
                    1,
                    "Error: This opportunity has already been claimed.",
                )

    def test_success_updates_job_and_creates_claimed_jobs(self):
        result = FR4claim.claim_job(self.email, 1)

        self.assertEqual(
            result,
            f"Success: Job 'Food Bank Volunteers' "
            f"claimed by {self.email}!",
        )
        self.assertFalse(self.jobs[1]["available"])
        self.assertEqual(self.jobs[1]["status"], "taken")
        self.assertEqual(self.jobs[1]["claimed_by"], self.email)
        self.assertEqual(self.users[self.email]["claimed_jobs"], [1])

    def test_append_to_existing_claimed_jobs(self):
        self.users[self.email]["claimed_jobs"] = [99]

        FR4claim.claim_job(self.email, 1)

        self.assertEqual(
            self.users[self.email]["claimed_jobs"], [99, 1]
        )

    def test_claim_same_job_twice(self):
        FR4claim.claim_job(self.email, 1)

        self.assert_claim_rejected(
            self.email,
            1,
            "Error: This opportunity is not published.",
        )
        self.assertEqual(self.users[self.email]["claimed_jobs"], [1])

    def test_second_volunteer_cannot_claim_taken_job(self):
        FR4claim.claim_job(self.email, 1)

        self.assert_claim_rejected(
            "other@test.com",
            1,
            "Error: This opportunity is not published.",
        )
        self.assertEqual(self.jobs[1]["claimed_by"], self.email)
        self.assertNotIn("claimed_jobs", self.users["other@test.com"])

    def test_view_claimed_jobs_unknown_user(self):
        self.assertEqual(
            self.capture_output(
                FR4claim.view_claimed_jobs, "missing@test.com"
            ),
            "Error: User account not found.\n",
        )

    def test_view_claimed_jobs_empty(self):
        self.assertEqual(
            self.capture_output(FR4claim.view_claimed_jobs, self.email),
            "You have not claimed any opportunities.\n",
        )

    def test_view_claimed_jobs_success(self):
        FR4claim.claim_job(self.email, 1)

        output = self.capture_output(
            FR4claim.view_claimed_jobs, self.email
        )

        self.assertIn(f"Jobs claimed by {self.email}:", output)
        self.assertIn("[1] Food Bank Volunteers", output)
        self.assertIn("Organization: Community Food Bank", output)
        self.assertIn("Date: 2026-12-05", output)
        self.assertIn("Location: Austin, TX", output)


class TestFR4Pledge(DatabaseTestCase):

    def assert_pledge_rejected(
        self, expected, email=None, job_id=2,
        item="Winter Coats", quantity=1
    ):
        if email is None:
            email = self.email

        users_before = deepcopy(self.users)
        jobs_before = deepcopy(self.jobs)

        result = FR4pledge.pledge_donation(
            email, job_id, item, quantity
        )

        self.assertEqual(result, expected)
        self.assertEqual(self.users, users_before)
        self.assertEqual(self.jobs, jobs_before)

    def test_unknown_account(self):
        self.assert_pledge_rejected(
            "Error: Account not found.",
            email="missing@test.com",
        )

    def test_non_volunteer(self):
        self.assert_pledge_rejected(
            "Error: Only volunteers can claim opportunities.",
            email="shelter@test.com",
        )

    def test_account_type_is_case_insensitive(self):
        for account_type in ("Volunteer", "VOLUNTEER"):
            with self.subTest(account_type=account_type):
                self.users[self.email]["account_type"] = account_type

                self.assertEqual(
                    FR4pledge.pledge_donation(
                        self.email, 2, "Winter Coats"
                    ),
                    "Success: 1 Winter Coats pledged "
                    "to 'Winter Clothing Drive'!",
                )

    def test_account_type_is_whitespace_insensitive(self):
        self.users[self.email]["account_type"] = "  volunteer  "

        self.assertEqual(
            FR4pledge.pledge_donation(
                self.email, 2, "Winter Coats"
            ),
            "Success: 1 Winter Coats pledged "
            "to 'Winter Clothing Drive'!",
        )

    def test_unknown_listing(self):
        self.assert_pledge_rejected(
            "Error: Donation not found.", job_id=999
        )

    def test_not_donation_or_missing_listing_type(self):
        for listing_type in ("volunteer", None):
            with self.subTest(listing_type=listing_type):
                if listing_type is None:
                    self.jobs[2].pop("listing_type", None)
                else:
                    self.jobs[2]["listing_type"] = listing_type

                self.assert_pledge_rejected(
                    "Error: This opportunity is not a donation listing."
                )

    def test_not_published_or_missing_status(self):
        for status in ("draft", "taken", None):
            with self.subTest(status=status):
                if status is None:
                    self.jobs[2].pop("status", None)
                else:
                    self.jobs[2]["status"] = status

                self.assert_pledge_rejected(
                    "Error: This donation listing is not published."
                )

    def test_unavailable_or_missing_availability(self):
        for missing in (False, True):
            with self.subTest(missing=missing):
                if missing:
                    self.jobs[2].pop("available", None)
                else:
                    self.jobs[2]["available"] = False

                self.assert_pledge_rejected(
                    "Error: This donation opportunity "
                    "is no longer available."
                )

    def test_invalid_items(self):
        for item in ("", " \t\n ", None, 123, []):
            with self.subTest(item=item):
                self.assert_pledge_rejected(
                    "Error: Please enter a valid donation item.",
                    item=item,
                )

    def test_invalid_quantities(self):
        for quantity in (0, -2, 1.5, 1.0, "3", True, False, None):
            with self.subTest(quantity=quantity):
                self.assert_pledge_rejected(
                    "Error: Quantity must be a positive whole number.",
                    quantity=quantity,
                )

    def test_default_quantity_is_one(self):
        result = FR4pledge.pledge_donation(
            self.email, 2, "Winter Coats"
        )

        self.assertEqual(
            result,
            "Success: 1 Winter Coats pledged "
            "to 'Winter Clothing Drive'!",
        )
        self.assertEqual(self.jobs[2]["pledges"][0]["quantity"], 1)
        self.assertEqual(
            self.users[self.email]["pledged_donations"][0]["quantity"],
            1,
        )

    def test_success_trims_item_and_records_both_sides(self):
        result = FR4pledge.pledge_donation(
            self.email, 2, "  Winter Coats  ", 3
        )

        self.assertEqual(
            result,
            "Success: 3 Winter Coats pledged "
            "to 'Winter Clothing Drive'!",
        )
        self.assertEqual(
            self.jobs[2]["pledges"],
            [{
                "email": self.email,
                "item": "Winter Coats",
                "quantity": 3,
            }],
        )
        self.assertEqual(
            self.users[self.email]["pledged_donations"],
            [{
                "job_id": 2,
                "item": "Winter Coats",
                "quantity": 3,
            }],
        )
        self.assertEqual(self.jobs[2]["status"], "published")
        self.assertTrue(self.jobs[2]["available"])

    def test_multiword_item_preserves_internal_spaces(self):
        FR4pledge.pledge_donation(self.email, 2, "Winter Coats", 3)

        self.assertEqual(
            self.jobs[2]["pledges"][0]["item"], "Winter Coats"
        )

    def test_new_pledge_appends_without_removing_existing_pledges(self):
        FR4pledge.pledge_donation(self.email, 2, "Winter Coats", 3)
        first_job_pledge = deepcopy(self.jobs[2]["pledges"][0])
        first_user_pledge = deepcopy(
            self.users[self.email]["pledged_donations"][0]
        )

        FR4pledge.pledge_donation(self.email, 2, "Gloves", 5)

        self.assertEqual(len(self.jobs[2]["pledges"]), 2)
        self.assertEqual(
            len(self.users[self.email]["pledged_donations"]), 2
        )
        self.assertEqual(
            self.jobs[2]["pledges"][0], first_job_pledge
        )
        self.assertEqual(
            self.users[self.email]["pledged_donations"][0],
            first_user_pledge,
        )

    def test_view_pledged_donations_unknown_user(self):
        self.assertEqual(
            self.capture_output(
                FR4pledge.view_pledged_donations, "missing@test.com"
            ),
            "Error: User account not found.\n",
        )

    def test_view_pledged_donations_empty(self):
        self.assertEqual(
            self.capture_output(
                FR4pledge.view_pledged_donations, self.email
            ),
            "You have not pledged any donations.\n",
        )

    def test_view_pledged_donations_success(self):
        FR4pledge.pledge_donation(self.email, 2, "Winter Coats", 3)

        output = self.capture_output(
            FR4pledge.view_pledged_donations, self.email
        )

        self.assertIn(f"Donations pledged by {self.email}:", output)
        self.assertIn("Opportunity: Winter Clothing Drive", output)
        self.assertIn("Item: Winter Coats", output)
        self.assertIn("Quantity: 3", output)

    def test_view_pledged_donations_deleted_listing(self):
        FR4pledge.pledge_donation(self.email, 2, "Winter Coats", 3)
        del self.jobs[2]

        output = self.capture_output(
            FR4pledge.view_pledged_donations, self.email
        )

        self.assertIn("Opportunity: Listing unavailable", output)
        self.assertIn("Item: Winter Coats", output)

    def test_view_opportunity_pledges_unknown_listing(self):
        self.assertEqual(
            self.capture_output(
                FR4pledge.view_opportunity_pledges, 999
            ),
            "Error: Donation opportunity not found.\n",
        )

    def test_view_opportunity_pledges_not_donation(self):
        self.assertEqual(
            self.capture_output(
                FR4pledge.view_opportunity_pledges, 1
            ),
            "Error: This is not a donation listing.\n",
        )

    def test_view_opportunity_pledges_empty(self):
        output = self.capture_output(
            FR4pledge.view_opportunity_pledges, 2
        )

        self.assertIn("Pledges for: Winter Clothing Drive", output)
        self.assertIn("No items have been pledged yet.", output)

    def test_view_opportunity_pledges_success(self):
        FR4pledge.pledge_donation(self.email, 2, "Winter Coats", 3)

        output = self.capture_output(
            FR4pledge.view_opportunity_pledges, 2
        )

        self.assertIn(
            f"Volunteer: {self.email} | "
            "Item: Winter Coats | Quantity: 3",
            output,
        )


if __name__ == "__main__":
    unittest.main()