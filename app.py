import streamlit as st
import pandas as pd
from db_functions import (get_basic_info, sql_connector, get_additional_tabels, Add_new_manual_id, get_supplier, get_categories, get_all_products,
                          get_product_history, place_reorder, get_pending_reorders, mark_reorder_as_received)

#sidebar

st.sidebar.title("Inventory Management Dashboard")
option  = st.sidebar.radio("Select Options:", ["Basic Information", "Operational Task"])

#Main

st.title("Inventory and Supply Chain Dashboard")
db     = sql_connector()
cursor = db.cursor()

# ----------------------------- BASIC INFORMATION PAGE ----------------------------------

if option=="Basic Information":
    st.header("Basic Metrics")

    #Get basic information from Database

    basic_info = get_basic_info(cursor)

    #divide 1st row into n columns
    cols = st.columns(3)
    keys = list(basic_info.keys())

    for col in range(3):
        cols[col].metric(label=keys[col], value=basic_info[keys[col]])

    # divide 2nd row into n columns
    cols = st.columns(3)

    for col in range(3, 6):
        cols[col-3].metric(label=keys[col], value=basic_info[keys[col]])

    st.divider()

    #fetch and display detail tabels

    # Fetch and display detail tables
    tables = get_additional_tabels(cursor)

    for label, data in tables.items():
        st.header(label)
        df = pd.DataFrame(data)
        st.dataframe(df)
        st.divider()

elif option == "Operational Task":
    st.header("Operational Task")
    selected_task = st.selectbox("Choose an Task", ["Add New Product", "Product History", "Place Reorder", "Receive Reorder"])

    if selected_task == "Add New Product":
        st.header("Add New Product")
        categories = [row[0] for row in get_categories(cursor)]
        supplier = get_supplier(cursor)

        with st.form("Add_Product_Form"):
            product_name = st.text_input("Product Name")
            product_category = st.selectbox("category", categories)
            product_price = st.number_input("Price", min_value=0.00)
            product_stock = st.number_input("Stock Quantity", min_value=0, step=1)
            product_restock = st.number_input("Reorder Level", min_value=0, step=1)

            supplier_ids   = [ids[0] for ids in supplier]
            supplier_names = [names[1] for names in supplier]

            supplier_id = st.selectbox("Supplier", options=supplier_ids,
                                       format_func=lambda x : supplier_names[supplier_ids.index(x)])


            submitted = st.form_submit_button("Add Product")

            if submitted:
                if not product_name:
                    st.error("Please enter the product name")

                else:
                    try:
                        Add_new_manual_id(cursor,
                                          db,
                                          product_name, product_category, product_price, product_stock, product_restock, supplier_id)

                        st.success(f"Product {product_name} Added Successfully")

                    except Exception as e:
                        st.error(f"Error adding the product {e}")

#----------------------------------------------- Product History -------------------------------------------------------


    if selected_task == "Product History":
        st.header("Product Inventory History")

        products = get_all_products(cursor)
        product_ids  = [ids[0] for ids in products]
        product_names = [ids[1] for ids in products]

        selected_product_name = st.selectbox(
            "Select An Option",
            options=product_names
        )

        if selected_product_name:
            selected_product_id = product_ids[product_names.index(selected_product_name)]
            history_data = get_product_history(cursor, selected_product_id)

            if history_data:
                df = pd.DataFrame(
                    [list(row) for row in history_data],
                    columns=["product_id", "record_type", "record_date",
                             "Quantity", "change_type", "supplier_id"]
                )
                st.dataframe(df, use_container_width=True)

            else:
                st.info("No History found for the product selected")


#------------------------------------------------- Place Reorder -------------------------------------------------------

    if selected_task == "Place Reorder":
        st.header("Place an Reorder")

        products = get_all_products(cursor)
        product_ids = [ids[0] for ids in products]
        product_names = [ids[1] for ids in products]

        selected_product_name = st.selectbox(
            "Select An Option",
            options=product_names
        )

        reorder_qty = st.number_input("Reorder Quantity", min_value=1, step=1)

        if st.button("Place Reorder"):
            if not selected_product_name:
                st.error("Please select an product")

            elif reorder_qty <=0 :
                st.error("Reorder Quantity must be greater than Zero")

            else:
                selected_product_id = product_ids[product_names.index(selected_product_name)]

                try:
                    place_reorder(cursor, db, selected_product_id, reorder_qty)
                    st.success(f"Order placed for {selected_product_name} with quantity {reorder_qty}")

                except Exception as e:
                    st.error(f"Error placing reorer {e}")


#-------------------------------------------------- RECEIVING AN ORDER -------------------------------------------------

    if selected_task == "Receive Reorder":
        st.header("Mark reorder as  Received")

        # Fetch orders in ordered stage

        pending_reorders = get_pending_reorders(cursor)

        if not  pending_reorders:
            st.info("No pending order to Received")

        else:
            reorder_ids = [ids[0] for ids in pending_reorders]
            reorder_label = [f"ID - {ids[0]} - {ids[1]}" for ids in pending_reorders]

            selected_label = st.selectbox("Select reorder to mark as Received", options=reorder_label)

            if selected_label:
                selected_reorder_id = reorder_ids[reorder_label.index(selected_label)]

                if st.button("Mark as Received"):
                    try:
                        mark_reorder_as_received(cursor, db ,selected_reorder_id)
                        st.success(f"Reorder ID {selected_reorder_id} Mark as Received")

                    except Exception as e:
                        st.error(f"Error {e}")
























