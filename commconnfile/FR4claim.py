def claim_job(email, job_id):

    # Check for account
    if email not in user_database:
        return "Error: User account not found."

    # Check if volunteer
    if user_database[email]["account_type"].casefold() != "volunteer":
        return "Error: Only volunteers can claim opportunities."

    # Check for job
    if job_id not in publishedjobs_database:
        return "Error: Opportunity not found."

    job = publishedjobs_database[job_id]

    # Check if job is published
    if job.get("status") != "published":
        return "Error: This opportunity is not published."

    # Check if job is available
    if not job.get("available", False):
        return "Error: This opportunity has already been claimed."

    # Mark job taken
    job["available"] = False
    job["status"] = "taken"
    job["claimed_by"] = email

    # Connect job to account
    if "claimed_jobs" not in user_database[email]:
        user_database[email]["claimed_jobs"] = []

    user_database[email]["claimed_jobs"].append(job_id)

    return f"Success: Job '{job['title']}' claimed by {email}!"


def view_claimed_jobs(email):
    """Displays all jobs claimed by a volunteer."""

    if email not in user_database:
        print("Error: User account not found.")
        return

    claimed_jobs = user_database[email].get("claimed_jobs", [])

    if not claimed_jobs:
        print("You have not claimed any opportunities.")
        return

    print(f"\nJobs claimed by {email}:")

    for job_id in claimed_jobs:
        job = publishedjobs_database.get(job_id)

        if job:
            print(f"\n[{job_id}] {job['title']}")
            print(f"Organization: {job['organization']}")
            print(f"Date: {job['date']}")
            print(f"Location: {job['city']}, {job['state']}")


# DEMO
if __name__ == "__main__":

    print("\n--- CommunityConnect: Claim an Opportunity ---")

    # Claim first opportunity
    print(claim_job("volunteer@test.com", 1))

    # Attempt to claim same opportunity again
    print(claim_job("volunteer@test.com", 1))

    # Display claimed opportunities
    view_claimed_jobs("volunteer@test.com")

    # Verify job is no longer available
    print("\n--- Updated Job Status ---")
    print(publishedjobs_database[1])