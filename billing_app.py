import sys
from PySide2.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
)
import pymysql  # Library for connecting and executing SQL commands on MySQL databases
import pandas as pd  # Library for handling data and exporting it to Excel files
from datetime import datetime  # Library for getting the current time

# Function to establish a connection with the MySQL database
def get_connection():
    """
    Establish and return a connection to the MySQL database.
    Raises an error if the connection fails.
    """
    try:
        return pymysql.connect(
            host="localhost",            # Host where the database is running (usually localhost for local setups)
            user="root",                 # MySQL username
            password="admin",            # MySQL password (replace with your actual password)
            database="BillingDB"         # Database name to connect to
        )
    except pymysql.MySQLError as e:
        print(f"Error: {e}")              # Logs the error if the connection fails
        raise  # Re-raise the exception to notify about the connection issue

# Main class for the billing system application
class BillingApp(QMainWindow):
    def __init__(self):
        """
        Initialize the billing application.
        Sets up the main window and calls the UI setup function.
        """
        super().__init__()
        self.setWindowTitle("Billing Form")  # Title of the application window
        self.setGeometry(100, 100, 600, 550)  # Set the dimensions and position of the window
        self.initUI()  # Call the function to set up the UI components

    def initUI(self):
        """
        Set up the user interface with input fields, buttons, and a table to display records.
        """
        # Create a central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Input field: Customer Name
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Customer Name")  # Adds a hint for the user
        layout.addWidget(self.name_input)

        # Input field: Customer Email
        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText("Customer Email")  # Adds a hint for the user
        layout.addWidget(self.email_input)

        # Input field: Bill Amount
        self.amount_input = QLineEdit(self)
        self.amount_input.setPlaceholderText("Bill Amount")  # Adds a hint for the user
        layout.addWidget(self.amount_input)

        # Button: Save Bill
        self.save_button = QPushButton("Save Bill")
        self.save_button.clicked.connect(self.save_bill)  # Link the button to the save_bill function
        layout.addWidget(self.save_button)

        # Button: Load Records
        self.load_button = QPushButton("Load Records")
        self.load_button.clicked.connect(self.load_records)  # Link the button to the load_records function
        layout.addWidget(self.load_button)

        # Button: Export Records to Excel
        self.export_button = QPushButton("Export to Excel")
        self.export_button.clicked.connect(self.export_to_excel)  # Link the button to the export_to_excel function
        layout.addWidget(self.export_button)

        # Button: Delete a Customer
        self.delete_button = QPushButton("Delete Customer")
        self.delete_button.clicked.connect(self.delete_customer)  # Link the button to the delete_customer function
        layout.addWidget(self.delete_button)

        # Table: Display Records
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # The table will display 6 columns
        self.table.setHorizontalHeaderLabels(["Bill ID", "Customer Name", "Email", "Amount", "Date", "Time"])  # Column headers
        layout.addWidget(self.table)

        # Apply the layout to the central widget
        central_widget.setLayout(layout)

    def save_bill(self):
        """
        Saves a new bill record to the database. 
        If the customer doesn't already exist, a new customer record is created.
        """
        # Fetch values from the input fields
        name = self.name_input.text()
        email = self.email_input.text()
        amount = self.amount_input.text()
        current_time = datetime.now().strftime('%H:%M:%S')  # Capture the current time in HH:MM:SS format

        # Ensure all fields are filled
        if name and email and amount:
            connection = get_connection()
            cursor = connection.cursor()
            try:
                # Check if the customer already exists
                cursor.execute("SELECT customer_id FROM Customers WHERE email = %s", (email,))
                result = cursor.fetchone()

                if result:
                    # Fetch the customer's ID if they exist
                    customer_id = result[0]
                    print(f"Customer already exists with ID: {customer_id}")
                else:
                    # Insert a new customer into the database
                    cursor.execute("INSERT INTO Customers (name, email) VALUES (%s, %s)", (name, email))
                    customer_id = cursor.lastrowid  # Get the ID of the newly added customer
                    print(f"New customer added with ID: {customer_id}")

                # Insert a bill record with the current time
                cursor.execute(
                    "INSERT INTO Bills (customer_id, amount, bill_date, time_slot) VALUES (%s, %s, CURDATE(), %s)", 
                    (customer_id, amount, current_time)
                )
                connection.commit()  # Commit the changes to the database

                QMessageBox.information(self, "Success", "Bill saved successfully!")
                self.clear_inputs()  # Clear input fields after saving
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save bill. Error: {e}")
            finally:
                cursor.close()  # Close the cursor
                connection.close()  # Close the connection
        else:
            # Show a warning if any field is empty
            QMessageBox.warning(self, "Input Error", "Please fill in all fields.")

    def load_records(self):
        """
        Loads and displays all customer and bill records in the table widget.
        """
        connection = get_connection()
        cursor = connection.cursor()
        try:
            # SQL query to fetch customer and bill records
            query = """
            SELECT Bills.bill_id, Customers.name, Customers.email, Bills.amount, Bills.bill_date, Bills.time_slot
            FROM Bills
            JOIN Customers ON Bills.customer_id = Customers.customer_id
            """
            cursor.execute(query)
            results = cursor.fetchall()

            # Populate the table widget with the fetched records
            self.table.setRowCount(len(results))
            for row_idx, row_data in enumerate(results):
                for col_idx, col_data in enumerate(row_data):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load records. Error: {e}")
        finally:
            cursor.close()
            connection.close()

    def export_to_excel(self):
        """
        Exports the customer and bill records to an Excel file.
        """
        connection = get_connection()
        cursor = connection.cursor()
        try:
            # SQL query to fetch records for exporting
            query = """
            SELECT Bills.bill_id AS `Bill ID`, Customers.name AS `Customer Name`, 
                   Customers.email AS `Email`, Bills.amount AS `Amount`, 
                   Bills.bill_date AS `Date`, Bills.time_slot AS `Time`
            FROM Bills
            JOIN Customers ON Bills.customer_id = Customers.customer_id
            """
            cursor.execute(query)
            results = cursor.fetchall()

            # Use pandas to create a DataFrame and save it as an Excel file
            columns = ["Bill ID", "Customer Name", "Email", "Amount", "Date", "Time"]
            df = pd.DataFrame(results, columns=columns)
            df.to_excel("BillingRecords.xlsx", index=False)

            QMessageBox.information(self, "Success", "Records exported to BillingRecords.xlsx successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not export records. Error: {e}")
        finally:
            cursor.close()
            connection.close()

    def delete_customer(self):
        """
        Deletes a customer record and their associated bills from the database.
        """
        email = self.email_input.text()

        # Ensure the email field is not empty
        if email:
            connection = get_connection()
            cursor = connection.cursor()
            try:
                # Check if the customer exists
                cursor.execute("SELECT customer_id FROM Customers WHERE email = %s", (email,))
                result = cursor.fetchone()

                if result:
                    # Delete the customer and their associated bills
                    customer_id = result[0]
                    cursor.execute("DELETE FROM Bills WHERE customer_id = %s", (customer_id,))
                    cursor.execute("DELETE FROM Customers WHERE customer_id = %s", (customer_id,))
                    connection.commit()

                    QMessageBox.information(self, "Success", "Customer and associated bills deleted successfully!")
                    self.clear_inputs()
                    self.load_records()
                else:
                    QMessageBox.warning(self, "Not Found", "Customer not found with the provided email.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete customer. Error: {e}")
            finally:
                cursor.close()
                connection.close()
        else:
            # Show a warning if the email field is empty
            QMessageBox.warning(self, "Input Error", "Please provide the customer's email to delete.")
    def clear_inputs(self):
        """
        Clears all input fields on the form.
        This ensures that after saving or deleting data, the input fields are reset
        and ready for the next input.
        """
        self.name_input.clear()  # Clears the Customer Name input field
        self.email_input.clear()  # Clears the Customer Email input field
        self.amount_input.clear()  # Clears the Bill Amount input field

# Entry point of the application
if __name__ == "__main__":
    """
    This block initializes and runs the billing application.
    It ensures that the application starts and remains running until the user closes it.
    """
    app = QApplication(sys.argv)  # Create an application instance
    main_window = BillingApp()  # Instantiate the BillingApp class
    main_window.show()  # Display the main application window
    sys.exit(app.exec_())  # Execute the application and wait for its termination
