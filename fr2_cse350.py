import sqlite3
from datetime import datetime

# connect to database
def connect(database_file):
    db = sqlite3.connect(database_file)
    db.row_factory = sqlite3.Row

    db.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY,
            name TEXT,
            verified INTEGER
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER,
            title TEXT,
            category TEXT,
            location TEXT,
            description TEXT,
            need_date TEXT,
            shift_time TEXT,
            capacity INTEGER,
            item_name TEXT,
            item_quantity INTEGER,
            status TEXT DEFAULT 'open'
        )
    """)

    db.commit()
    return db
# add organizations for testing
def add_demo_organizations(db):
    db.execute(
        "INSERT OR IGNORE INTO organizations VALUES (?, ?, ?)",
        (1, "Community Food Bank", 1)
    )

    db.execute(
        "INSERT OR IGNORE INTO organizations VALUES (?, ?, ?)",
        (2, "Unverified Group", 0)
    )

    db.commit()

#create new listing
def create_listing(db, organization_id, form):

    # check if organization is verified
    org = db.execute(
        "SELECT verified FROM organizations WHERE id = ?",
        (organization_id,)
    ).fetchone()

    if org is None or org["verified"] != 1:
        raise PermissionError("Only verified nonprofits can post.")

    #get listing info
    category = form.get("category", "").strip().lower()
    title = form.get("title", "").strip()
    location = form.get("location", "").strip()
    description = form.get("description", "").strip()

    if category != "volunteer" and category != "donation":
        raise ValueError("Invalid listing type.")

    if title == "" or location == "" or description == "":
        raise ValueError("Please fill out all required fields.")

    if len(title) > 100 or len(location) > 120 or len(description) > 2000:
        raise ValueError("One of the fields is too long.")

    need_date = None
    shift_time = None
    capacity = None
    item_name = None
    item_quantity = None

    #volunteer listing
    if category == "volunteer":
        need_date = form.get("need_date", "").strip()
        shift_time = form.get("shift_time", "").strip()

        try:
            datetime.strptime(need_date, "%Y-%m-%d")
            datetime.strptime(shift_time, "%H:%M")
            capacity = int(form.get("capacity", ""))
        except ValueError:
            raise ValueError("Invalid volunteer information.")

        if capacity < 1:
            raise ValueError("Volunteers needed must be greater than zero.")

    #donation listing
    else:
        item_name = form.get("item_name", "").strip()

        if item_name == "":
            raise ValueError("Please enter an item.")

        try:
            item_quantity = int(form.get("item_quantity", ""))
        except ValueError:
            raise ValueError("Invalid item quantity.")

        if item_quantity < 1:
            raise ValueError("Item quantity must be greater than zero.")

    #save listing
    result = db.execute("""
        INSERT INTO listings
        (organization_id, title, category, location, description,
         need_date, shift_time, capacity, item_name, item_quantity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        organization_id, title, category, location, description,
        need_date, shift_time, capacity, item_name, item_quantity
    ))

    db.commit()
    return result.lastrowid


#get all open listings
def get_listings(db):
    return db.execute("""
        SELECT listings.*, organizations.name AS organization_name
        FROM listings
        JOIN organizations ON listings.organization_id = organizations.id
        WHERE listings.status = 'open'
        AND organizations.verified = 1
        ORDER BY listings.id DESC
    """).fetchall()


#demo output
if __name__ == "__main__":

    #using memory database so it starts fresh every time
    db = connect(":memory:")
    add_demo_organizations(db)

    print("--- CommunityConnect: Post Community Need ---")

    #volunteer example
    volunteer = {
        "category": "volunteer",
        "title": "Community Park Cleanup",
        "location": "Louisville, KY",
        "description": "Help clean the local park.",
        "need_date": "2026-11-20",
        "shift_time": "10:00",
        "capacity": "5"
    }

    #donation example
    donation = {
        "category": "donation",
        "title": "Food Donation Drive",
        "location": "Louisville, KY",
        "description": "Collect food for families.",
        "item_name": "Canned Food",
        "item_quantity": "20"
    }

    #test volunteer posting
    try:
        listing_id = create_listing(db, 1, volunteer)
        print("Success: Volunteer listing created! ID:", listing_id)
    except (ValueError, PermissionError) as error:
        print("Error:", error)

    #test donation posting
    try:
        listing_id = create_listing(db, 1, donation)
        print("Success: Donation listing created! ID:", listing_id)
    except (ValueError, PermissionError) as error:
        print("Error:", error)

    #test unverified nonprofit
    try:
        create_listing(db, 2, volunteer)
    except (ValueError, PermissionError) as error:
        print("Error:", error)

    #show saved listings
    print("\n--- CommunityConnect: Open Listings ---")

    listings = get_listings(db)

    for listing in listings:
        print("Title:", listing["title"])
        print("Organization:", listing["organization_name"])
        print("Type:", listing["category"])
        print("Location:", listing["location"])
        print()

    db.close()