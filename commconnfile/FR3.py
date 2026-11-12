# search and filter function

#mock database to store posted work
# filter by date, location, and type: donations or volunteer work
# must be able to search available opportunities
#clear filters; enter city state, or zip;date;select listing type:volunteer or donation;
# sort by kind of donation needed (food, clothes, other supplies)

publishedjobs_database = {}

def normalize(value):
    #Remove surrounding whitespace and normalize capitalization.
    if value is None:
        return ""
    return str(value).strip().casefold()


def search_jobs(
    city=None,
    state=None,
    zip_code=None,
    date=None,
    listing_type=None,
    keyword=None,
    donation_type=None,
    sort_by=None,
):
    #Search published, available opportunities.
    results = []

    allowed_sort_fields = {
        "date", "city", "listing_type", "donation_type"
    }

    if sort_by is not None and sort_by not in allowed_sort_fields:
        raise ValueError(
            "sort_by must be date, city, listing_type, or donation_type."
        )

    for job in publishedjobs_database.values():
        # Only display published and available listings.
        if job.get("status") != "published":
            continue

        if not job.get("available", False):
            continue

        if normalize(city):
            if normalize(job.get("city")) != normalize(city):
                continue

        if normalize(state):
            if normalize(job.get("state")) != normalize(state):
                continue

        if normalize(zip_code):
            if normalize(job.get("zip_code")) != normalize(zip_code):
                continue

        if normalize(date):
            if normalize(job.get("date")) != normalize(date):
                continue

        if normalize(listing_type):
            if normalize(job.get("listing_type")) != normalize(listing_type):
                continue

        if normalize(donation_type):
            if normalize(job.get("listing_type")) != "donation":
                continue

            if normalize(job.get("donation_type")) != normalize(donation_type):
                continue

        if normalize(keyword):
            searchable_text = " ".join(
                str(job.get(field) or "")
                for field in ("title", "description", "organization")
            )

            if normalize(keyword) not in normalize(searchable_text):
                continue

        results.append(job)

    if sort_by:
        # Sort alphabetically; listings with no value go last.
        results.sort(
            key=lambda job: (
                not bool(normalize(job.get(sort_by))),
                normalize(job.get(sort_by)),
                job["id"],
            )
        )

    return results


def filter_jobs(
    city=None,
    state=None,
    zip_code=None,
    date=None,
    listing_type=None,
    donation_type=None,
    sort_by=None,
):
    #Reuse the search function to avoid duplicate logic
    return search_jobs(
        city=city,
        state=state,
        zip_code=zip_code,
        date=date,
        listing_type=listing_type,
        donation_type=donation_type,
        sort_by=sort_by,
    )


def clear_filters():
    #Return every published, available opportunity.
    return search_jobs()


def donation_type_filter(donation_type):
    #Return donation listings matching the requested category.
    return search_jobs(
        listing_type="donation",
        donation_type=donation_type,
    )


def display_results(results):
    #Print matching opportunities for the demo, (based on samples below) 
    if not results:
        print("No matching opportunities found.")
        return

    label = "opportunity" if len(results) == 1 else "opportunities"
    print(f"Found {len(results)} {label}:")

    for job in results:
        print(f"\n[{job['id']}] {job['title']}")
        print(f"  Organization: {job['organization']}")
        print(
            f"  Location: {job['city']}, "
            f"{job['state']} {job['zip_code']}"
        )
        print(f"  Date: {job['date']}")
        print(f"  Listing type: {job['listing_type']}")

        if job["listing_type"] == "donation":
            print(f"  Donation needed: {job['donation_type']}")

        print(f"  Description: {job['description']}")


if __name__ == "__main__":
    # Add sample jobs to the database for testing.
    publishedjobs_database.update({
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
        },
    })
# Filter examples
    print("-- Community Connect: Find Opportunities --")

    print("\n--- All available published opportunities ---")
    display_results(search_jobs())

    print("\n--- Keyword search: food ---")
    display_results(search_jobs(keyword="food"))

    print("\n--- Volunteer opportunities in Austin ---")
    display_results(filter_jobs(
        city="Austin",
        state="TX",
        listing_type="volunteer",
    ))

    print("\n--- Opportunities in ZIP code 78701 on December 5 ---")
    display_results(filter_jobs(
        zip_code="78701",
        date="2026-12-05",
    ))

    print("\n--- Clothing donations needed in Austin ---")
    display_results(filter_jobs(
        city="Austin",
        listing_type="donation",
        donation_type="clothes",
    ))

    print("\n--- Food donation opportunities ---")
    display_results(donation_type_filter("food"))

    print("\n--- Donations sorted alphabetically by category ---")
    display_results(filter_jobs(
        listing_type="donation",
        sort_by="donation_type",
    ))

    print("\n--- Filters cleared ---")
    display_results(clear_filters())

