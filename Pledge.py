def pledge_donation(email, job_id, item, quantity=1):

    # Check for account
    if email not in user_database:
        return "Error: Account not found."

    # Check if volunteer
    if user_database[email]["account_type"].casefold() != "volunteer":
        return "Error: Only volunteers can claim opportunities."

    # Check for job
    if job_id not in publishedjobs_database:
        return "Error: Donation not found."

    job = publishedjobs_database[job_id]

    # Check if listing is donation
    if job.get("listing_type") != "donation":
        return "Error: This opportunity is not a donation listing."

    # Check if donation is published
    if job.get("status") != "published":
        return "Error: This donation listing is not published."

    # Check if donation is available
    if not job.get("available", False):
        return "Error: This donation opportunity is no longer available."

    # Validate item and quantity
    if not isinstance(item, str) or not item.strip():
        return "Error: Please enter a valid donation item."

    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        return "Error: Quantity must be a positive whole number."

    # Record the pledge
    pledge = {
        "email": email,
        "item": item.strip(),
        "quantity": quantity
    }

    job["pledges"].append(pledge)

    # Connect pledge to account
    if "pledged_donations" not in user_database[email]:
        user_database[email]["pledged_donations"] = []

    user_database[email]["pledged_donations"].append({
        "job_id": job_id,
        "item": item.strip(),
        "quantity": quantity
    })

    return (
        f"Success: {quantity} {item.strip()} pledged "
        f"to '{job['title']}'!"
    )


def view_pledged_donations(email):
    """Displays all donations pledged by a volunteer."""

    if email not in user_database:
        print("Error: User account not found.")
        return

    pledges = user_database[email].get("pledged_donations", [])

    if not pledges:
        print("You have not pledged any donations.")
        return

    print(f"\nDonations pledged by {email}:")

    for pledge in pledges:
        job = publishedjobs_database.get(pledge["job_id"])

        print(f"\nOpportunity: {job['title'] if job else 'Listing unavailable'}")
        print(f"Item: {pledge['item']}")
        print(f"Quantity: {pledge['quantity']}")


def view_opportunity_pledges(job_id):
    """Displays all pledges made"""

    if job_id not in publishedjobs_database:
        print("Error: Donation opportunity not found.")
        return

    job = publishedjobs_database[job_id]

    if job.get("listing_type") != "donation":
        print("Error: This is not a donation listing.")
        return

    pledges = job.get("pledges", [])

    print(f"\nPledges for: {job['title']}")

    if not pledges:
        print("No items have been pledged yet.")
        return

    for pledge in pledges:
        print(
            f"Volunteer: {pledge['email']} | "
            f"Item: {pledge['item']} | "
            f"Quantity: {pledge['quantity']}"
        )


# DEMO
if __name__ == "__main__":

    print("\n--- CommunityConnect: Pledge a Donation ---")

    # Pledge items to clothing drive
    print(
        pledge_donation(
            "volunteer@test.com",
            2,
            "Winter Coats",
            3
        )
    )

    # Pledge another item to the same drive
    print(
        pledge_donation(
            "volunteer@test.com",
            2,
            "Gloves",
            5
        )
    )

    # Display user's donations
    view_pledged_donations("volunteer@test.com")

    # Display all pledges
    view_opportunity_pledges(2)