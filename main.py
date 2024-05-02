import sqlite3
from datetime import datetime, timedelta

DATABASE = 'library.db'

def generate_position(copy_no, location):
    return f"{copy_no:03d}{location}"

def connect_to_database():
    return sqlite3.connect(DATABASE)

def authenticate_user(r_id):
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute("SELECT RID FROM READER WHERE RID = ?", (r_id,))

    db_r_id = cursor.fetchone()

    if db_r_id:
        return r_id == db_r_id[0]
    else:
        return False


def authenticate_admin(admin_id, password):
    return admin_id == 'admin' and password == 'password'

def reader_functions_menu():
    r_id = int(input("Enter Card Number: "))
    print()

    if authenticate_user(r_id):
        print("1. Search for a document by ID, title, or publisher name.") 
        print("2. Checkout a document.")
        print("3. Return a document.")
        print("4. Reserve a document.")
        print("5. Compute fine for a borrowed document copy based on the current date.")
        print("6. Print the list of documents reserved by a reader and their status.")
        print("7. Print the document ID and titles of documents published by a specific publisher.")
        print("8. Quit.")
        print()

        choice = input("Enter your choice: ")
        print()

        if choice == '1':
            search_document() #done
        elif choice == '2':
            document_checkout(r_id) #done
        elif choice == '3':
            document_return() #done
        elif choice == '4':
            document_reserve(r_id) #done
        elif choice == '5':
            compute_fine(r_id) #done
        elif choice == '6':
            print_reserved_documents(r_id) #done
        elif choice == '7':
            print_documents_by_publisher() #done
        elif choice == '8':
            return
    else:
        print("Wrong Card Number")

def search_document():
    search_term = input("Enter ID, title, or publisher name to search: ")
    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM DOCUMENT WHERE DOCID = ? OR TITLE LIKE ? OR PUBLISHERID IN "
                   "(SELECT PUBLISHERID FROM PUBLISHER WHERE PUBNAME LIKE ?)", 
                   (search_term, f'%{search_term}%', f'%{search_term}%'))
    documents = cursor.fetchall()
    print()

    if documents:
        for document in documents:
            print("ID: {}\nTitle: {}\nPublisher Date: {}\n".format(document[0],document[1],document[2]))
            
    else:
        print("No documents found.")

    conn.close()

def document_checkout(r_id):
    doc_id = input("Enter Document ID: ")
    b_id = input("Enter Branch ID: ")
    copy_no = input("Enter Copy No: ")
    borrow_date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT * "
                   "FROM BORROWS "
                   "JOIN BORROWING ON BORROWS.BOR_NO = BORROWING.BOR_NO "
                   "WHERE BORROWS.DOCID = ? AND BORROWS.BID = ? AND BORROWS.COPYNO = ? "
                   "AND BORROWING.RDTIME IS NULL "
                   "LIMIT 1", 
                    (doc_id,b_id,copy_no))
    
    conn.commit()
    borrow = cursor.fetchone()

    if not borrow:
        cursor.execute("INSERT INTO BORROWING (BDTIME) VALUES (?)", 
                   (borrow_date_time,))
    
        conn.commit()
        new_bor_no = cursor.lastrowid
    
        cursor.execute("INSERT INTO BORROWS (RID, DOCID, BID, COPYNO, BOR_NO) VALUES (?, ?, ?, ?, ?)", 
                   (r_id, doc_id, b_id, copy_no, new_bor_no))
        conn.commit()
        print("Document Checked Out.")
        print("Borrowing No.",new_bor_no)
    else:
        print("Book is already borrowed by someone else")
    conn.close()

def document_return():
    b_num = input("Enter borrowing number: ")
    return_date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM BORROWING WHERE BOR_NO = ?", (b_num,))
    borrowing = cursor.fetchone()

    if borrowing:
        borrow_date = datetime.strptime(borrowing[1], '%Y-%m-%d %H:%M:%S')
        fine_amount = 0
        if datetime.now() > (borrow_date + timedelta(days=20)):
            days_delayed = (datetime.now() - (borrow_date + timedelta(days=20))).days
            fine_amount = days_delayed * 0.2

        cursor.execute("UPDATE BORROWING SET RDTIME = ? WHERE BOR_NO = ?", 
                       (return_date_time, b_num))
        conn.commit()
        print("Document returned successfully.")
        if fine_amount > 0:
            print(f"Fine amount: {fine_amount}$")
    else:
        print("Invalid borrowing number.")

    conn.close()

def document_reserve(r_id):
    doc_id = input("Enter Document ID: ")
    b_id = input("Enter Branch ID: ")
    copy_no = input("Enter Copy No: ")
    
    reservation_date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO RESERVATION (DTIME) VALUES (?)", 
                    (reservation_date_time,))
    
    conn.commit()
    res_no = cursor.lastrowid
    
    cursor.execute("INSERT INTO RESERVES (RID, DOCID, BID, COPYNO, RESERVATION_NO) VALUES (?, ?, ?, ?, ?)", 
                    (r_id, doc_id, b_id, copy_no, res_no))
    
    conn.commit()
    
    cursor.execute("SELECT DOCUMENT.TITLE "
                   "FROM DOCUMENT "
                   "JOIN RESERVES ON DOCUMENT.DOCID = RESERVES.DOCID "
                   "WHERE RESERVES.RESERVATION_NO = ?", 
                    (res_no,))

    document = cursor.fetchone()
    print(document)
    conn.close()
    print("Reservation No.",res_no)
    

def compute_fine(r_id):
    b_num = input("Enter borrowing number: ")
    return_date_time = datetime.now()

    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT BORROWING.BDTIME "
                   "FROM BORROWING "
                   "JOIN BORROWS ON BORROWING.BOR_NO = BORROWS.BOR_NO "
                   "WHERE BORROWING.BOR_NO = ? AND BORROWS.RID = ?", (b_num, r_id))
    borrowing = cursor.fetchone()

    if borrowing:
        borrow_date = datetime.strptime(borrowing[0], '%Y-%m-%d %H:%M:%S')
        fine_amount = 0
        if return_date_time > (borrow_date + timedelta(days=20)):
            days_delayed = (return_date_time - (borrow_date + timedelta(days=20))).days
            fine_amount = days_delayed * 0.2

        print(f"Fine amount: ${fine_amount}")
    else:
        print("Invalid borrowing number.")

    conn.close()

def print_reserved_documents(r_id):
    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT DOCUMENT.DOCID, DOCUMENT.TITLE, RESERVATION.DTIME "
                   "FROM DOCUMENT "
                   "JOIN RESERVES ON DOCUMENT.DOCID = RESERVES.DOCID "
                   "JOIN RESERVATION ON RESERVES.RESERVATION_NO = RESERVATION.RES_NO "
                   "WHERE RESERVES.RID = ?", (r_id,))
    reserved_documents = cursor.fetchall()

    if reserved_documents:
        for document in reserved_documents:
            print("Document ID: {}\tDocument Title: {}\tReservation Date and Time: {}".format(document[0],document[1],document[2]))
            reserve_date_time = datetime.strptime(document[2], '%Y-%m-%d %H:%M:%S')
            current_date_time = datetime.now()
            if (reserve_date_time.date() == current_date_time.date()) and (current_date_time.time().hour < 18):
                print("Reservation is still available")
            else:
                print("Reservation is cancelled") 
    else:
        print("No reserved documents.")

    conn.close()

def print_documents_by_publisher():
    publisher_name = input("Enter publisher name: ")

    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT DOCID, TITLE FROM DOCUMENT WHERE PUBLISHERID IN "
                   "(SELECT PUBLISHERID FROM PUBLISHER WHERE PUBNAME = ?)", (publisher_name,))
    documents = cursor.fetchall()

    if documents:
        for document in documents:
            print("Document ID: {}\tDocument Title: {}".format(document[0],document[1]))
    else:
        print("No documents found.")

    conn.close()

def admin_functions_menu():
    admin_id = input("Enter Admin ID: ")
    password = input("Enter Password: ")
    print()

    if authenticate_admin(admin_id, password):
        print("1. New Document copy.")
        print("2. Search for a document copy and check its status.")
        print("3. New Reader.")
        print("4. Print branch information (name and location).")
        print("5. Top N most frequent borrowers from a branch.")
        print("6. Top N most frequent borrowers from the library.")
        print("7. Top N most borrowed book from a branch.")
        print("8. Top N most borrowed book from the library.")
        print("9. Top 10 most popular books of a year.")
        print("10. Average Fine at each branch within a given timeframe")
        print("11. Quit.")
        print()

        choice = input("Enter your choice: ")

        if choice == '1':
            add_document_copy() #done
        elif choice == '2':
            search_document_copy() 
        elif choice == '3':
            add_new_reader() #done
        elif choice == '4':
            print_branch_info() #done
        elif choice == '5':
            top_borrowers_in_branch() #done
        elif choice == '6':
            top_borrowers_in_library() #done
        elif choice == '7':
            most_borrowed_books_in_branch() #done
        elif choice == '8':
            most_borrowed_books_in_library() #done
        elif choice == '9':
            popular_books_by_year() #done
        elif choice == '10':
            average_fine_by_branch() # done
        elif choice == '11':
            return
        else:
            print("Invalid choice.")
    else:
        print("Invalid Admin ID or Password.")

def add_document_copy():
    d_id = input("Enter Document ID: ")
    b_id = int(input("Enter Branch ID: "))
    copy_no = int(input("Enter Copy Number: "))
    location = input("Which Self and Bookcase is loacated (It should be in this format like A03, A04, etc.): ")

    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO COPY (DOCID, BID, COPYNO, POSITION) VALUES (?, ?, ?, ?)", 
                   (d_id, b_id, copy_no, generate_position(copy_no, location)))
    conn.commit()
    print("New document copy added.")

    conn.close()

def search_document_copy():
    d_id = input("Enter Document ID: ")
    b_id = int(input("Enter Branch ID: "))
    copy_no = int(input("Enter Copy Number: "))

    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM COPY WHERE COPYNO = ? AND DOCID = ? AND BID = ?", (copy_no,d_id,b_id))
    copy = cursor.fetchone()

    if copy:
        print("Copy found:")
        print(copy)
        cursor.execute("""
            SELECT * FROM RESERVES 
            JOIN RESERVATION ON RESERVES.RESERVATION_NO = RESERVATION.RES_NO 
            WHERE RESERVES.DOCID = ? AND RESERVES.BID = ? AND RESERVES.COPYNO = ? 
            AND DATE(RESERVATION.DTIME) = date('now') AND strftime('%H:%M', 'now', 'localtime') <= '18:00'
        """, (copy[0], copy[1], copy[2]))
        reservation = cursor.fetchone()
        if reservation:
            print("Reservation exists valid.")
        else:
            print("Reservation cancelled.")
    else:
        print("Copy not found.")

    conn.close()

def add_new_reader():
    name = input("Name: ")
    address = input("Address: ")
    phone_number = input("Phone Number: ")
    reader_type = input("Type: ")

    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO READER (RNAME, RADDRESS, PHONE_NO, TYPE) VALUES (?, ?, ?, ?)", 
                   (name, address, phone_number, reader_type))
    conn.commit()
    new_reader_id = cursor.lastrowid
    print("ID of the new reader:", new_reader_id)

    conn.close()

def print_branch_info():
    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT BID, LName, LOCATION FROM BRANCH")
    branches = cursor.fetchall()
    print()

    if branches:
        for branch in branches:
            print("Branch Name: {}\nBranch Location: {}\n".format(branch[1],branch[2]))
    else:
        print("No branch information found.")

    conn.close()

def top_borrowers_in_branch():
    n = int(input("Enter number of top borrowers: "))
    branch_number = input("Enter branch number: ")

    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT READER.RID, READER.RNAME, COUNT(*) AS num_borrowed FROM BORROWS "
                   "JOIN READER ON BORROWS.RID = READER.RID "
                   "WHERE BORROWS.BID = ? "
                   "GROUP BY READER.RID, READER.RNAME "
                   "ORDER BY num_borrowed DESC "
                   "LIMIT ?", (branch_number, n))
    top_borrowers = cursor.fetchall()

    if top_borrowers:
        for borrower in top_borrowers:
            print(borrower)
    else:
        print("No top borrowers found.")

    conn.close()

def top_borrowers_in_library():
    n = int(input("Enter number of top borrowers: "))

    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT READER.RID, READER.RNAME, COUNT(*) AS num_borrowed FROM BORROWS "
                   "JOIN READER ON BORROWS.RID = READER.RID "
                   "GROUP BY READER.RID, READER.RNAME "
                   "ORDER BY num_borrowed DESC "
                   "LIMIT ?", (n,))
    top_borrowers = cursor.fetchall()

    if top_borrowers:
        for borrower in top_borrowers:
            print(borrower)
    else:
        print("No top borrowers found.")

    conn.close()

def most_borrowed_books_in_branch():
    n = int(input("Enter number of most borrowed books: "))
    branch_number = int(input("Enter branch number: "))

    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT DOCUMENT.DOCID, DOCUMENT.TITLE, COUNT(*) AS num_borrowed FROM DOCUMENT "
                   "JOIN BORROWS ON DOCUMENT.DOCID = BORROWS.DOCID "
                   "WHERE BORROWS.BID = ? "
                   "GROUP BY DOCUMENT.DOCID, DOCUMENT.TITLE "
                   "ORDER BY num_borrowed DESC "
                   "LIMIT ?", (branch_number, n))
    most_borrowed_books = cursor.fetchall()

    if most_borrowed_books:
        for book in most_borrowed_books:
            print(book)
    else:
        print("No most borrowed books found.")

    conn.close()

def most_borrowed_books_in_library():
    n = int(input("Enter number of most borrowed books: "))

    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT DOCUMENT.DOCID, DOCUMENT.TITLE, COUNT(*) AS num_borrowed FROM DOCUMENT "
                   "JOIN BORROWS ON DOCUMENT.DOCID = BORROWS.DOCID "
                   "GROUP BY DOCUMENT.DOCID, DOCUMENT.TITLE "
                   "ORDER BY num_borrowed DESC "
                   "LIMIT ?", (n,))
    most_borrowed_books = cursor.fetchall()

    if most_borrowed_books:
        for book in most_borrowed_books:
            print(book)
    else:
        print("No most borrowed books found.")

    conn.close()

def popular_books_by_year():
    year = input("Enter year: ")

    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT DOCUMENT.DOCID, DOCUMENT.TITLE, COUNT(*) AS num_borrowed FROM DOCUMENT "
                   "JOIN BORROWS ON DOCUMENT.DOCID = BORROWS.DOCID "
                   "JOIN BORROWING ON BORROWS.BOR_NO = BORROWING.BOR_NO "
                   "WHERE strftime('%Y', BORROWING.BDTIME) = ? "
                   "GROUP BY DOCUMENT.DOCID "
                   "ORDER BY num_borrowed DESC "
                   "LIMIT 10", (year,))
    popular_books = cursor.fetchall()

    if popular_books:
        for book in popular_books:
            print(book)
    else:
        print("No popular books found.")

    conn.close()

def average_fine_by_branch():
    start_date = input("Enter start date (YYYY-MM-DD): ")
    end_date = input("Enter end date (YYYY-MM-DD): ")

    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT B.BID AS Branch_ID, B.LNAME AS Branch_Name, AVG(CASE WHEN BO.BDTIME BETWEEN ? AND ? THEN FINE_AMOUNT ELSE 0 END) AS Avg_Fine_Paid
        FROM BRANCH B
        LEFT JOIN COPY C ON B.BID = C.BID
        LEFT JOIN BORROWS BR ON C.COPYNO = BR.COPYNO
        LEFT JOIN BORROWING BO ON BR.BOR_NO = BO.BOR_NO
        LEFT JOIN (SELECT BOR_NO, SUM(CASE WHEN (julianday(RDTIME) - julianday(BDTIME)) > 20 THEN ((julianday(DATE(RDTIME)) - julianday(DATE(BDTIME))) - 20) * 0.2 ELSE 0 END) AS FINE_AMOUNT
                   FROM BORROWING
                   WHERE RDTIME IS NOT NULL AND BDTIME BETWEEN ? AND ?
                   GROUP BY BOR_NO
                  ) F ON BO.BOR_NO = F.BOR_NO
        GROUP BY B.BID, B.LNAME;
    ''', (start_date, end_date, start_date, end_date))

    results = cursor.fetchall()

    for row in results:
        print("Branch ID:", row[0])
        print("Branch Name:", row[1])
        print("Average Fine Paid:", row[2])

def main_menu():
    print("Welcome to CITY LIBRARY MANAGEMENT SYSTEMS")
    print()
    print("1. Reader Functions")
    print("2. Administrative Functions")
    print("3. Quit")
    print()

    choice = input("Enter your choice: ")
    print()

    if choice == '1':
        reader_functions_menu()
    elif choice == '2':
        admin_functions_menu()
    elif choice == '3':
        return
    else:
        print("Invalid choice.")

if __name__ == '__main__':
    main_menu()
