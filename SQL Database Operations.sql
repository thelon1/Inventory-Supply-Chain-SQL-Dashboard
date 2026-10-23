Create database  Advance_DB_Operations

use Advance_DB_Operations

select * from products
select * from reorders
select * from shipments
select * from stock_entries
select * from suppliers

-- Total Suppliiers

select COUNT(*) as [Total Suppliers]
from suppliers

-- Total Products

select COUNT(product_id) as [Total Products] 
from products

-- Total Categories Dealing

select COUNT(DISTINCT(category)) as [Total Categories Dealing]
from products


-- Total Sales made in last 3 months
 
select COALESCE(ROUND(SUM(ABS(se.change_quantity)*p.price),2), 0)  as [Total sales value in last 3 months]
from stock_entries as se 
join
products as p on 
p.product_id  = se.product_id
WHERE se.change_type = 'sale' 
AND se.entry_date >= (
                        SELECT DATEADD(MONTH, -3, MAX(entry_date))
                        FROM stock_entries
                         where change_type in ('Sale', 'Restock')
                      );

--Total restock value  made in last 3 months

select COALESCE(ROUND(SUM(ABS(se.change_quantity)*p.price),2), 0)  as [Total restock value in last 3 months]
from stock_entries as se 
join
products as p on 
p.product_id  = se.product_id
WHERE se.change_type = 'Restock' 
AND se.entry_date >= (
                        SELECT DATEADD(MONTH, -3, MAX(entry_date))
                        FROM stock_entries
                         where change_type in ('Sale', 'Restock')
                      );

-- Below Reorders and no pending Reorders

select count(*) as [Below reorder and no pendng records] 
from products as p 
where p.stock_quantity<p.reorder_level
AND product_id NOT IN (select DISTINCT product_id from reorders where status='Pending')


-- *******************************************************************************************************

-- Suppliers and theirs contact details.

select supplier_name, contact_name, email, phone from suppliers

-- Product with their supplier and current stock

select p.product_name, s.supplier_name, p.stock_quantity, p.reorder_level 
from products as p  
join 
suppliers as s 
on p.supplier_id = s.supplier_id
order by p.product_name ASC

-- Product needing reorder

select product_name, product_id, stock_quantity, reorder_level
from products 
where stock_quantity <= reorder_level


-- ************************************** OPERATIONAL TASK ***************************************************************

-- Add an new product to database.


ALTER procedure AddNewProductManualID
    @p_name varchar(20),
    @p_category varchar(100),
    @p_price decimal(10, 2),
    @p_stock int,
    @p_reorder int,
    @p_supplier int
AS
BEGIN
    DECLARE @new_product_id int,
            @new_shipment_id int,
            @new_entry_id int

            -- Make changes in product table
            -- generating product id

            select @new_product_id = MAX(product_id)+1 from products

            insert into products(product_id, product_name, category, price, stock_quantity, reorder_level, supplier_id)
            values (@new_product_id, @p_name, @p_category, @p_price, @p_stock, @p_reorder, @p_supplier)

            -- Make changes in shipment talbe.
            -- generate shipment id

            select @new_shipment_id = MAX(shipment_id)+1 from shipments

            insert into shipments(shipment_id, product_id, supplier_id, quantity_received, shipment_date)
            values (@new_shipment_id, @new_product_id, @p_supplier, @p_stock, CAST(GETDATE() AS DATE))

            -- make changes in stock entries.
            -- genertate new stock id

            select @new_entry_id = MAX(entry_id)+1 from stock_entries
            insert into stock_entries(entry_id, product_id, change_quantity, change_type, entry_date)
            values(@new_entry_id, @new_product_id, @p_stock, 'New Product Added', CAST(GETDATE() AS DATE))
END

EXEC  AddNewProductManualID  'Smart Phone', 'Electronics', 96.49, 44, 24, 1

select * from products where product_name = 'Mens OverSized T-shi'
select * from shipments where product_id = 217
select * from stock_entries where product_id = 216


--- Product History

create view product_Inventory_History 
as
    select pih.product_id,
           pih.record_type,
           pih.record_date,
           pih.Quantity,
           pih.change_type,
           pr.supplier_id from  
            (select product_id, 'Shipment' as record_type,
                    shipment_date as record_date , 
                    quantity_received as Quantity, 
                    NULL as change_type  
            from shipments

            UNION ALL

            select product_id, 'stock entry' as record_type, 
                    entry_date as record_date, 
                    change_quantity as Quantity, 
                    change_type 
            from stock_entries) as pih 
            join 
            products as pr on pih.product_id = pr.product_id 

select  * 
from product_Inventory_History
where product_id  = 123
order by record_date desc 

-- Place Reorder

insert into reorders(reorder_id, product_id, reorder_quantity, reorder_date, status)

select MAX(reorder_id)+1,101, 200, CURRENT_DATE, 'ORDER' from reorders  

select * from reorders order by  reorder_id desc

select * from products where product_id = 183

-- Receicve order

Create or ALter procedure MarkReorderAsEReceived
    @in_reorder_id int
As
BEGIN   
        
        DECLARE @product_id      int,
                @quantity        int,
                @supplier_id     int,
                @new_shipment_id int,
                @new_entry_id        int

        BEGIN Transaction;
        
        -- get product id and quantity from reorder

        Select @product_id = product_id,  @quantity =  reorder_quantity from reorders
        where reorder_id = @in_reorder_id;

        -- get supplier id from products

        Select @supplier_id = supplier_id from products

        -- updating reorder table : Received

        update reorders

        set status='Received' 
        where reorder_id = @in_reorder_id

        -- updating quantity in product table

        update products

        set stock_quantity = stock_quantity+@quantity
        where product_id   = @product_id

        -- Insert Record into shipment table

        select @new_shipment_id = MAX(shipment_id)+1 from shipments

        insert into shipments(shipment_id, product_id, supplier_id, quantity_received, shipment_date)
        values(@new_shipment_id, @product_id, @supplier_id, @quantity, CURRENT_DATE)

        -- Insert recordds into Restocks

        select @new_entry_id = MAX(entry_id)+1 from stock_entries

        insert into stock_entries(entry_id, product_id, change_quantity, change_type, entry_date)
        values(@new_entry_id, @product_id, @quantity, 'Restock',  CURRENT_DATE)

        commit; -- save all the changes
End

EXEC MarkReorderAsEReceived 2;







select * from reorders where reorder_id=1

select * from products where product_name='Someone shirt'

select * from stock_entries where product_id = 164  order by entry_date desc