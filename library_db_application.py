import sqlite3
from pathlib import Path
from datetime import date
from datetime import datetime
import re

db_path = Path("library.db").resolve()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Make sure input is nonempty
def nonEmpty(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("❌ Input cannot be empty. Please try again.\n")
        
# Helper function: Valid email
def get_valid_email():
    while True:
        email = input("\nEnter your email: ")
        if re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            return email
        print("\n❌ Invalid email format. Please enter a valid email.")

# Helper function: Valid date
def get_valid_date(prompt):
    while True:
        date_input = input(prompt)
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_input):
            return date_input
        print("\n❌ Invalid date format. Please use YYYY-MM-DD.")
        
# Checks if someone has a membership
def check_membership():
    print("\n\n---------------------------------------")
    print("\n\nDo you have an existing membership with us?")
    answer = input("Enter (y) for Yes or (n) for No: ").lower()
    
    # User response: n
    if answer == 'n':
        create_membership()
        return True 
    # User response: y
    elif answer == 'y':
        email = input("Please enter your email: ")
        query = "SELECT * FROM Member WHERE email = ?"
        cursor.execute(query, (email,))
        member = cursor.fetchone()
        
        # If member -> Proceed
        if member:
            print(f"\nWelcome back, {member[1]}!")
            return True
        # Retry if input not in db
        else:
            print("Invalid input. Please try again.")
            return check_membership()
    # User response: other
    else:
        print("Invalid input. Please try again.")
        return check_membership()  # Retry in case of invalid input

# Creates membership
def create_membership():
    print("\nTo access the library, you need to create a membership.")

    name = nonEmpty("\nEnter your full name: ")

    # Birthday format:(YYYY-MM-DD)
    while True:
        birthday = input("Enter your full birthday in this format (YYYY-MM-DD): ")
        if re.match(r"^\d{4}-\d{2}-\d{2}$", birthday):
            break
        print("\n❌ Invalid date format. Please enter in YYYY-MM-DD format.")

    # Email format: @
    while True:
        email = input("Enter your email: ")

        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            print("\n❌ Invalid email. Please enter a valid email address.")
            continue  # Restart email input

        # If entered email already in db -> Retry 
        cursor.execute("SELECT email FROM Member WHERE email = ?", (email,))
        if cursor.fetchone():
            print("\n❌ This email is already registered.\nRedirecting to membership check...")
            check_membership()
            return

        break

    # Valid inputs + Email not in db -> Create new member
    query = '''INSERT INTO Member (name, birthday, email) 
               VALUES (?, ?, ?)'''
    cursor.execute(query, (name, birthday, email))
    conn.commit()

    print(f"\n✅ Membership created successfully for {name}. Welcome to our library!")

# Define library functions
def introPage():
    print("\n\n---------------------------------------")
    print("\nPlease input the number of the option you would like: \n")
    print("(1): Find an item in the library ")
    print("(2): Borrow an item from the library ")
    print("(3): Return a borrowed item ")
    print("(4): Donate an item to the library ")
    print("(5): Find an event in the library ")
    print("(6): Register for an event in the library ")
    print("(7): Volunteer for the library ")
    print("(8): Ask for help from a librarian ")
    print("(9): Exit Program ")
    return input("Enter Number: ")

# Finds item
def find_item():
    print("\n\nPlease enter either the Name, Author, or Genre of the item you're looking for: ")
    item_type = input("(1) Name, (2) Author, (3) Genre: ")

    if item_type == '1':
        search_value = input('Enter the item name (partial match allowed): ')
        query = 'SELECT itemID FROM Item WHERE name LIKE ?'
    elif item_type == '2':
        search_value = input("Enter the author name (partial match allowed): ")
        query = 'SELECT itemID FROM Item WHERE author LIKE ?'
    elif item_type == '3':
        search_value = input('Enter the genre (partial match allowed): ')
        query = 'SELECT itemID FROM Item WHERE genre LIKE ?'
    else:
        print('❌ Invalid choice')
        return
    
    # Search
    search_value = '%' + search_value + '%'

    cursor.execute(query, (search_value,))
    itemIDs = cursor.fetchall()

    if itemIDs:
        available_items = []
        unavailable_items = []

        # Sort items -> Available, unavailable
        for itemID in itemIDs:
            cursor.execute("SELECT * FROM Item WHERE itemID = ?", (itemID[0],))
            item_attributes = cursor.fetchone()

            if item_attributes[5].lower() == 'available':
                available_items.append(item_attributes)
            else:
                unavailable_items.append(item_attributes)

        # Print available items
        if available_items:
            print("\n✅ Available Items:")
            for item in available_items:
                print(f"ItemID: {item[0]}, Name: {item[1]}, Author: {item[2]}, Category: {item[3]}, Genre: {item[4]}, Status: {item[5]}")
        else:
            print("\nNo available items found.")

        # Print unavailable items
        if unavailable_items:
            print("\n❌ Unavailable Items:")
            for item in unavailable_items:
                print(f"ItemID: {item[0]}, Name: {item[1]}, Author: {item[2]}, Category: {item[3]}, Genre: {item[4]}, Status: {item[5]}")
        else:
            print("\nNo unavailable items found.")

    else:
        print("\n❌ No item found matching your search input :(")




def borrow_item():
    email = input("\nEnter your email: ")

    # Checks if member exists
    cursor.execute("SELECT * FROM Member WHERE email = ?", (email,))
    member = cursor.fetchone()
    if not member:
        print("\n❌ No membership found with this email. Please create a membership first.")
        return

    # Ask for itemID
    while True:
        try:
            item_id = int(input("Enter the item ID: "))
            break
        except ValueError:
            print("❌ Invalid input! Please enter a numeric item ID.")

    # Check item status
    cursor.execute("SELECT status FROM Item WHERE itemID = ?", (item_id,))
    item = cursor.fetchone()
    # Item doesn't exist
    if item is None:
        print("\n❌ Item not found.")
        return
    status = item[0]
    # Item currently unavailable
    if status == 'Unavailable':
        print("\n❌ The item is currently unavailable for borrowing.")
        return

    # New borrow transaction
    cursor.execute("INSERT INTO Borrow (email, itemID) VALUES (?, ?)", (email, item_id))
    conn.commit()

    # Insert into BorrowTransactions (NULL borrowID) and get borrowID (created using trigger)
    borrow_date = date.today().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO BorrowTransactions (borrowID, borrowDate) VALUES (NULL, ?)", (borrow_date,))
    conn.commit()
    borrow_id = cursor.lastrowid

    # Update Borrow table
    cursor.execute("UPDATE Borrow SET borrowID = ? WHERE email = ? AND itemID = ?", (borrow_id, email, item_id))
    conn.commit()

    # Get return date
    cursor.execute("SELECT returnDate FROM BorrowTransactions WHERE borrowID = ?", (borrow_id,))
    return_date = cursor.fetchone()[0]

    # Make item -> Unavailable
    cursor.execute("UPDATE Item SET status = 'Unavailable' WHERE itemID = ?", (item_id,))
    conn.commit()

    # Success output
    cursor.execute("SELECT name FROM Item WHERE itemID = ?", (item_id,))
    item_name = cursor.fetchone()[0]

    print(f"\n✅ Success! You borrowed '{item_name}'.")
    print(f"Return Date: {return_date}")
        

# Return borrowed item
def return_item():
    email = input("\nEnter your email: ")

    # Get member info
    cursor.execute("SELECT * FROM Member WHERE email = ?", (email,))
    member = cursor.fetchone()
    if not member:
        print("\n❌ No membership found with this email.")
        return

    # (If exists) print all borrowed items 
    cursor.execute("""
        SELECT Item.itemID, Item.name 
        FROM Item
        JOIN Borrow ON Item.itemID = Borrow.itemID
        WHERE Borrow.email = ?
    """, (email,))
    borrowed_items = cursor.fetchall()
    
    if not borrowed_items:
        print("\n❌ You have no borrowed items.")
        return
    
    print("\n📌 Your borrowed items:")
    for item in borrowed_items:
        print(f"- {item[0]}: {item[1]}")
    
    # Get itemID
    item_id = input("\nEnter the item ID of the item you want to return: ")
    
    # Return if pass checks / error
    cursor.execute("SELECT borrowID FROM Borrow WHERE email = ? AND itemID = ?", (email, item_id))
    borrow_record = cursor.fetchone()
    
    if borrow_record is None:
        print("\n❌ You have not borrowed this item or it does not exist.")
        return
    
    borrow_id = borrow_record[0] 
    
    # Item Status -> Available
    cursor.execute("UPDATE Item SET status = 'Available' WHERE itemID = ?", (item_id,))
    conn.commit()
    
    # BorrowTransactions status -> Returned
    return_date = date.today().strftime("%Y-%m-%d")
    cursor.execute("UPDATE BorrowTransactions SET status = 'Returned', returnDate = ? WHERE borrowID = ?", 
                   (return_date, borrow_id))
    conn.commit()
    
    # Delete Borrow record
    cursor.execute("DELETE FROM Borrow WHERE email = ? AND itemID = ?", (email, item_id))
    conn.commit()
    
    # Success output
    cursor.execute("SELECT name FROM Item WHERE itemID = ?", (item_id,))
    item_name = cursor.fetchone()[0]
    
    print(f"\n✅ Success! You returned '{item_name}'.")

# Donates item (add item)
def donate_item():
    # Get item details
    full_name = nonEmpty("\nEnter the full name of the item: ")
    author = nonEmpty("\nEnter the author of the item: ")
    category = nonEmpty("\nEnter the category of the item: ")
    genre = nonEmpty("\nEnter the genre of the item: ")

    # Add new item (-> Automatically adds to history also)
    query = """INSERT INTO Item (name, author, category, genre, status)
               VALUES (?, ?, ?, ?, ?)"""
    cursor.execute(query, (full_name, author, category, genre, 'Available'))
    conn.commit()

    # Success output
    print(f"\n✅ Successfully donated the item: '{full_name}' by {author}.")
    print("It is now available in the library!")

# Prints past and future events
def find_events():
    # Get today's date
    today = datetime.today().date()

    # Retrieve all events ordered by date
    query = "SELECT eventID, name, scheduledTime, scheduledDate, targetAudience FROM Events ORDER BY scheduledDate, scheduledTime"
    cursor.execute(query)
    events = cursor.fetchall()

    if not events:
        print("\n❌ No events found.")
        return

    # Get future and past events
    future_events = []
    past_events = []

    for event in events:
        event_date = datetime.strptime(event[3], "%Y-%m-%d").date() 
        if event_date >= today:
            future_events.append(event)
        else:
            past_events.append(event)

    def print_events(title, event_list):
        if not event_list:
            print(f"\n❌ No {title.lower()} events found.")
            return

        print(f"\n{title}")
        print("-" * 90)
        print(f"{'ID':<5} {'Event Name':<25} {'Time':<10} {'Date':<12}{'Audience':<15}")
        print("-" * 90)

        for event_id, name, time, date, audience in event_list:
            print(f"{event_id:<5} {name:<25} {time:<10} {date:<12} {'N/A':<20} {audience:<15}")

        print("-" * 90)

    # Print
    print_events("\n✅ Upcoming Events", future_events)
    print_events("❌ Past Events", past_events)

# Registers member for event
def register_event():
    email = input("\nEnter your email: ")

    # Get member
    cursor.execute("SELECT * FROM Member WHERE email = ?", (email,))
    member = cursor.fetchone()
    if not member:
        print("\n❗ No membership found with this email. Please create a membership first.")
        return

    # Get eventID and its details
    event_id = input("\nEnter the Event ID you want to register for: ")
    cursor.execute("""
        SELECT e.name, e.scheduledTime, e.scheduledDate, e.targetAudience, l.roomNum 
        FROM Events e 
        LEFT JOIN Located l ON e.eventID = l.eventID 
        WHERE e.eventID = ?
    """, (event_id,))
    
    event = cursor.fetchone()

    # Check if event exists
    if event is None:
        print("\n❌ Event not found.")
        return

    # If it does -> Get details
    event_name, scheduled_time, scheduled_date, target_audience, room_num = event

    # Make sure event is in future
    event_date = datetime.strptime(scheduled_date, "%Y-%m-%d").date()
    if event_date < datetime.today().date():
        print(f"\n❌ You cannot register for '{event_name}' because the event has already passed.")
        return

    # Display event details
    print("\nEvent Details:")
    print(f"Name: {event_name}")
    print(f"Scheduled Time: {scheduled_time}")
    print(f"Scheduled Date: {scheduled_date}")
    print(f"Target Audience: {target_audience}")
    print(f"Room Number: {room_num if room_num else 'Not assigned'}")

    # Insert into Attends table
    try:
        cursor.execute("INSERT INTO Attends (email, eventID) VALUES (?, ?)", (email, event_id))
        conn.commit()
        print(f"\n✅ Success! You are now registered for '{event_name}'\n\t- ⏰ Time: {scheduled_time}\n\t- Date: 📅 {scheduled_date}\n\t- #️⃣ Room Number: {room_num}.")
    except sqlite3.IntegrityError:
        print("\n❗ You are already registered for this event.")


# Volunteer for library
def volunteer_library():
    print("\nBecome a Library Volunteer!")

    # Validate email format
    while True:
        email = input("Enter your email: ")

        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            print("\n❌ Invalid email. Please enter a valid email address.")
            continue

        # Check: Member
        cursor.execute("SELECT email FROM Member WHERE email = ?", (email,))
        if not cursor.fetchone():
            print("\n❗ You must be a registered library member to volunteer.")
            return 

        # Check: Member is volunteer?
        cursor.execute("SELECT email FROM Volunteer WHERE email = ?", (email,))
        if cursor.fetchone():
            print("\n❗ You are already registered as a volunteer.")
            return

        # Check: Member is staff?
        cursor.execute("SELECT email FROM Staff WHERE email = ?", (email,))
        if cursor.fetchone():
            print("\n❗ You cannot volunteer as you are already registered as a staff member.")
            return 

        break
    
    employment_date = date.today().strftime("%Y-%m-%d")
    # Insert into Volunteer table
    query = '''INSERT INTO Volunteer (email, employmentDate) 
               VALUES (?, ?)'''
    cursor.execute(query, (email, employment_date))
    conn.commit()

    print(f"\n✅ Thank you! You are now registered as a library volunteer starting from {employment_date}.")

# Ask for help from librarian 
def ask_librarian():
    while True:
        print("\n\n---------------------------------------")
        print("\n📚 Ask the Librarian:")
        print("1. How do I apply to become a librarian?")
        print("2. Do I have any outstanding fines?")
        print("3. Pay my fines")
        print("4. Recommend me events")
        print("5. Exit")

        choice = input("\nEnter the number of your choice: ")

        if choice == "1":
            apply_librarian()
        elif choice == "2":
            check_fines()
        elif choice == "3":
            print("\n\n---------------------------------------")
            print("\n\nPay Your Fines!")
            email = get_valid_email()
            pay_fines(email)
        elif choice == "4":
            recommend_events()
        elif choice == "5":
            print("\n👋 Exiting Ask a Librarian.")
            break
        else:
            print("\n❌ Invalid input. Please enter a number from 1 to 5.")

# Apply to become a librarian
def apply_librarian():
    print("\n\n---------------------------------------")
    print("\n\n📖 How to Apply as a Librarian:")
    print("To apply, please provide the following details.")

    email = get_valid_email()

    # Check: If member already staff
    cursor.execute("SELECT email FROM Staff WHERE email = ?", (email,))
    if cursor.fetchone():
        print("\n❗ You are already a staff member!")
        return

    employment_date = get_valid_date("Enter your employment start date (YYYY-MM-DD): ")

    # Ask for the position
    positions = {
        "1": ("Librarian", 20000),
        "2": ("Assistant Librarian", 15000),
        "3": ("Security", 25000),
        "4": ("Cleaner", 18000)
    }

    print("\nAvailable Positions:")
    for key, (role, wage) in positions.items():
        print(f"{key}. {role} - ${wage}/year")

    while True:
        choice = input("\nEnter the number corresponding to your chosen position: ")
        if choice in positions:
            position, wage = positions[choice]
            break
        print("\n❌ Invalid choice. Please enter a valid number (1-4).")

    # Insert into Staff table
    cursor.execute(
        "INSERT INTO Staff (email, employmentDate, position, wage, employmentStatus) VALUES (?, ?, ?, ?, ?)",
        (email, employment_date, position, wage, "Working")
    )
    conn.commit()

    print(f"\n✅ Application successful! You are now a {position} earning ${wage}/year.")


# Check fines
def check_fines():
    print("\n\n---------------------------------------")
    print("\n\nCheck my fines:")
    email = get_valid_email()

    # Get borrowIDs linked to the email
    cursor.execute("SELECT borrowID FROM Borrow WHERE email = ?", (email,))
    borrow_ids = cursor.fetchall()

    if not borrow_ids:
        print("\n❌ No borrowing records found for this email.")
        return

    # Retrieve fines for correspongding borrow transactions
    total_fines = 0
    for borrow_id in borrow_ids:
        cursor.execute("SELECT SUM(amount) FROM Fines WHERE borrowID = ?", (borrow_id[0],))
        fine = cursor.fetchone()[0]
        
        if fine:
            total_fines += fine

    # Display the total fine amount
    if total_fines > 0:
        print(f"\n💰 You have outstanding fines totaling ${total_fines:.2f}.")
    else:
        print("\n✅ You have no fines!")

# Function to pay fines
def pay_fines(email):
    print("\n\n---------------------------------------")
    cursor.execute("""
        SELECT F.borrowID, F.amount
        FROM Fines F
        JOIN Borrow B ON F.borrowID = B.borrowID
        WHERE B.email = ? AND F.status != 'Paid'
    """, (email,))
    
    fines = cursor.fetchall()

    if not fines:
        print("\n\n✅ No fines to pay!")
        return

    total_fine = sum(fine[1] for fine in fines)
    print(f"\n💰 Your total outstanding fine is: ${total_fine:.2f}")

    while True:
        amount = input("Enter the amount you want to pay: $")
        try:
            amount = float(amount)
            if amount <= 0:
                print("\n❌ Amount must be greater than zero.")
            elif amount > total_fine:
                print("\n❌ You cannot overpay. Enter a valid amount.")
            else:
                # Deduct payment amount from fines -> When amount=0 -> status=paid !!!
                for borrow_id, fine_amount in fines:
                    if amount <= 0:
                        break

                    if amount >= fine_amount:
                        cursor.execute("""
                            UPDATE Fines
                            SET amount = 0, status = 'Paid'
                            WHERE borrowID = ?
                        """, (borrow_id,))
                        amount -= fine_amount
                    else:
                        cursor.execute("""
                            UPDATE Fines
                            SET amount = amount - ?
                            WHERE borrowID = ?
                        """, (amount, borrow_id))
                        amount = 0 

                conn.commit()

                print("\n✅ Payment successful! Your updated fine status has been recorded.")

                # Dont pay if your fines are already paid or you dont have any
                cursor.execute("""
                    SELECT SUM(amount)
                    FROM Fines
                    JOIN Borrow ON Fines.borrowID = Borrow.borrowID
                    WHERE Borrow.email = ?
                """, (email,))
                remaining_fine = cursor.fetchone()[0]

                if not remaining_fine or remaining_fine == 0:
                    print("\n🎉 All your fines are fully paid!")

                return
        except ValueError:
            print("\n❌ Invalid input. Please enter a numeric value.")

# Recommend events based on target audience
def recommend_events():
    print("\n\n---------------------------------------")
    print("\n\n🎭 Discover Events Based on Your Interests!")
    print("Please select a category that best suits you:")

    audience_options = {
        "1": "All Ages",
        "2": "Children",
        "3": "Teens and Adults",
        "4": "Adults",
        "5": "Volunteers",
        "6": "Children and Families"
    }

    for key, value in audience_options.items():
        print(f"{key}. {value}")

    while True:
        choice = input("\nEnter the number corresponding to your category: ")
        if choice in audience_options:
            target_audience = audience_options[choice]
            break
        print("\n❌ Invalid choice. Please enter a number between 1 and 6.")

    # Get events based on target audience (input)
    cursor.execute("""
        SELECT eventID, name, scheduledDate, scheduledTime
        FROM Events
        WHERE targetAudience = ?
    """, (target_audience,))
    
    events = cursor.fetchall()

    if not events:
        print("\n❌ No events found for your selected category.")
        return

    print(f"\n📅 Events for '{target_audience}':")
    for event in events:
        event_id, name, date, time = event
        print(f"\n🆔 Event ID: {event_id}")
        print(f"📌 Name: {name}")
        print(f"📅 Date: {date}")
        print(f"⏰ Time: {time}")

    # Asks if wants to sign up for event (shortcut)
    while True:
        sign_up = input("\nWould you like to sign up for an event? (y/n): ").strip().lower()
        if sign_up == "y":
            register_event()
        elif sign_up == "n":
            print("\n🤧 No problem! 🤧🤧 Enjoy your day.")
            break
        else:
            print("\n❌ Invalid input. Please try again.")

# Choose options
def user_question(option):
    print("\n\n---------------------------------------")
    if option == '1': 
        find_item()
    if option == '2':
        borrow_item()
    if option == '3':
        return_item()
    if option == '4':
        donate_item()
    if option == '5':
        find_events()
    if option == '6':
        register_event()
    if option == '7':
        volunteer_library()
    if option == '8':
        ask_librarian()


# Check if member
membership_verified = check_membership()

# If they have membership -> Continue
if membership_verified:
    user_choice = introPage()

    while user_choice != '9':
        if user_choice in {'1', '2', '3', '4', '5', '6', '7', '8'}:
            user_question(user_choice)
        else:
            print("\n❌ Invalid choice! Please enter a number between 1 and 9.")

        user_choice = introPage()

    print('Thanks for using our library database!')

conn.close()