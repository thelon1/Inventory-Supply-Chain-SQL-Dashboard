import pyodbc
import streamlit
import pandas as pd

def sql_connector():
    return pyodbc.connect(
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=ROHIT\SQLEXPRESS;"
    r"DATABASE=Advance_DB_Operations;"
    r"Trusted_Connection=yes;")

def get_basic_info(cursor):
    queries = {
        "Total Supplier": "select COUNT(*) as [Total Suppliers] from suppliers",

        "Total Products": "select COUNT(product_id) as [Total Products] from products",

        "Total Category Dealing": "select COUNT(DISTINCT(category)) as [Total Categories Dealing] from products",

        "Total Sales value (Last 3 Months)":
            """select COALESCE(ROUND(SUM(ABS(se.change_quantity) * p.price), 2), 0) as [Total sales value in last 3 months]
               from stock_entries as se
                   join
                   products as p
               on
                   p.product_id = se.product_id
               WHERE se.change_type = 'Sale'
                 AND se.entry_date >= (
                   SELECT DATEADD(MONTH
                   , -3
                   , MAX (entry_date))
                   FROM stock_entries
                   where change_type in ('Sale')
                   );""",

        "Total restock value (Last 3 months)":
            """select COALESCE(ROUND(SUM(ABS(se.change_quantity) * p.price), 2), 0) as [Total restock value in last 3 months]
               from stock_entries as se
                   join
                   products as p
               on
                   p.product_id = se.product_id
               WHERE se.change_type = 'Restock'
                 AND se.entry_date >= (
                   SELECT DATEADD(MONTH
                   , -3
                   , MAX (entry_date))
                   FROM stock_entries
                   where change_type in ('Sale', 'Restock')
                   );""",

        "Below Reorders & No pending reorders":
            """select count(*) as [Below reorder and no pendng records]
               from products as p
               where p.stock_quantity
                   <p.reorder_level
                 AND product_id NOT IN (select DISTINCT product_id from reorders where status='Pending')
            """}

    result = {}

    for label, query in queries.items():
        cursor.execute(query)
        row = cursor.fetchone()
        result[label] = row[0]

    return result


def get_additional_tabels(cursor):
    queries = {
        "Supplier contact Default": "select supplier_name, contact_name, email, phone from suppliers",

        "Product with supplier and stock": """select p.product_name,
                                                     s.supplier_name,
                                                     p.stock_quantity,
                                                     p.reorder_level
                                              from products as p
                                                       join
                                                   suppliers as s
                                                   on p.supplier_id = s.supplier_id
                                              order by p.product_name ASC""",

        "Product needing reorder":
            """select product_name, product_id, stock_quantity, reorder_level
               from products
               where stock_quantity <= reorder_level"""}

    tabels = {}

    for label, query in queries.items():
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        rows = [tuple(row) for row in cursor.fetchall()]
        tabels[label] = pd.DataFrame(rows, columns=columns)

    return tabels


def get_categories(cursor):
    cursor.execute("Select Distinct Category from products order by category asc")
    rows = cursor.fetchall()
    return rows

def get_supplier(cursor):
    cursor.execute("Select supplier_id, supplier_name from suppliers order by supplier_name asc")
    rows = cursor.fetchall()
    return rows

def Add_new_manual_id(cursor, conn, p_name, p_category, p_price, p_stock , p_reorder,p_supplier):

    proc_call = "EXEC AddNewProductManualID ?, ?, ?, ?, ?, ?"
    params = (p_name, p_category, p_price , p_stock , p_reorder ,p_supplier)

    cursor.execute(proc_call,  params)
    conn.commit()

def get_all_products(cursor):
    cursor.execute("Select product_id, product_name from products order by product_name")
    return cursor.fetchall()

def get_product_history(cursor, product_id):
    query = "select  * from product_Inventory_History where product_id = ? order by record_date desc"
    cursor.execute(query, (product_id,))
    return cursor.fetchall()

def place_reorder(cursor, db, product_id, reorder_quantity):
    query = """
                INSERT INTO reorders
                    (reorder_id, product_id, reorder_quantity, reorder_date, status)
                SELECT
                    ISNULL(MAX(reorder_id), 0) + 1,
                    ?,
                    ?,
                    GETDATE(),
                    'Pending'
                FROM reorders
            """

    cursor.execute(query, (product_id, reorder_quantity))
    db.commit()

def get_pending_reorders(cursor):
    cursor.execute("""Select ro.reorder_id, p.product_name from reorders as ro 
                      join products as p on  
                      ro.product_id = p.product_id""")

    return cursor.fetchall()

def mark_reorder_as_received(cursor, db, reorder_id):
    cursor.execute("EXEC MarkReorderAsEReceived ?", reorder_id)
    db.commit()














