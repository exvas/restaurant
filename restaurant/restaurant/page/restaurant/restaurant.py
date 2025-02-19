import frappe,json


@frappe.whitelist()
def get_orders():
    orders = frappe.db.sql(""" SELECT * FROM `tabOrders` """, as_dict=1)

    for x in orders:
        print(x)
        color = "red" if x.status == 'Void' else "green" if x.status == 'Paid' else "orange"
        x['table'] = '<table class="order" style="box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);width: 100%;margin-top: 10px;border-bottom: 1px solid lightgray;margin-right: 10px;cursor: pointer" onclick="select_order({0})">'.format("'" + x.name + "'") + \
                     '<td style="width: 2%;border: 1px solid black;background-color: {0}"></td>'.format(color) + \
                       '<td style="width: 40%;padding-left: 10px">#' + x.name.split("-")[1] + '<br>' + str(
            x.total_amount) + '<br>TABLE: ' + x.table + ' </td>' \
                                                        '<td style="width: 58%">' + str(x.posting_date) + " " + str(
            x.posting_time) + ' <br>' + (x.mode_of_payment if x.mode_of_payment else "") + ' <br>' + (x.status if x.status else "") + '</td>' \
                                                                                 '</table>'
        print(x['table'])
    selected_order = ""

    if len(orders) > 0:
        selected_order = get_selected_order(orders[0].name,[],from_get_orders=True)
    return {
        "orders": orders,
        "selected_order":selected_order,
        "dashboard": "change_tab('Dashboard')"
    }


@frappe.whitelist()
def get_selected_order(order_name,e_orders,from_get_orders=False):
    print(e_orders)
    orders = frappe.get_doc("Orders",order_name)
    items_table = ""
    items = frappe.db.sql(""" SELECT * FROM `tabOrder Items` WHERE parent=%s""", order_name, as_dict=1)
    total_amount =0
    for x in items:
        items_table += '<tr>'
        items_table += '<td style="padding: 15px">' + (x.item_name or "") + '</td>' \
                        '<td style="padding: 15px">' + str(x.qty) + '</td>' \
                        '<td style="padding: 15px">' + (x.notes or "") + '</td>' \
                        '<td style="padding: 15px">' + (x.status or "") + '</td>' \
                        '<td style="padding: 15px">' + str(x.rate) + '</td>' \
                        '<td style="padding: 15px">' + str(x.amount) + '</td>'
        items_table += '</tr>'
        total_amount += x.amount
    selected_order = '<table style="width:100%;">' \
                      '<tr>' \
                      '<td style="padding: 10px" class="text-left">#' + orders.name.split("-")[1] + '</td>' \
                       '<td style="padding: 10px" class="text-right">KIOSK : Kiosk acticve</td>' \
                       '</tr>' \
                       '<tr>' \
                       '<td style="padding: 10px" class="text-left">' \
                       'Date and Time:<br>' + str(orders.posting_date) + " " + str(orders.posting_time) + \
                      '</td>' \
                      '<td style="padding: 10px" class="text-right">' \
                      'Payment Type:<br>' \
                      + orders.mode_of_payment + \
                      '</td>' \
                      '</tr>' \
                      '</table>' \
                      '' \
                      '<table style="width: 98%;margin: 1%">' \
                      ' <tr>' \
                      '<td style="padding: 10px" class="text-left">' \
                      ' Items' \
                      '</td>' \
                      '</tr>' \
                      '<th bgcolor="#d3d3d3" class="text-left" style="padding: 15px;width:20%">Item</th>' \
                      '<th bgcolor="#d3d3d3" class="text-left" style="padding: 15px;width:20%">Quantity</th>' \
                      ' <th bgcolor="#d3d3d3" class="text-left" style="padding: 15px;width:20%">Notes</th>' \
                      ' <th bgcolor="#d3d3d3" class="text-left" style="padding: 15px;width:20%">Status</th>' \
                      ' <th bgcolor="#d3d3d3" class="text-left" style="padding: 15px;width:20%">Price</th>' \
                      ' <th bgcolor="#d3d3d3" class="text-left" style="padding: 15px;width:20%">Amount</th>' \
                      '</tr>' + items_table + \
                      '<th bgcolor="#d3d3d3" class="text-left" style="padding: 15px" colspan="5">Total</th>' \
                      '<th bgcolor="#d3d3d3" class="text-left" style="padding: 15px">' + str(total_amount) + '</th></tr>'

    if orders.status == "Unpaid":
        selected_order += ' <tr> <td colspan="6" style="width: 100%">' \
                                        '<div style=" display: flex;">' \
                                             '<button class="custom-button" style="background-color: red;font-weight: bold" onclick="void_order({0})">Void Order</button> '.format("'" + orders.name + "'")  + \
                                             '<button class="custom-button" style="background-color: green;font-weight: bold" onclick="paid_order({0})">Paid</button>'.format("'" + orders.name + "'")  + \
                                         '</div>' \
                                         '</td></tr>'
    selected_order += '</table>'
    return selected_order if from_get_orders else {
        "orders": json.loads(e_orders),
        "selected_order":selected_order,
        "dashboard": "change_tab('Dashboard')"
    }

@frappe.whitelist()
def create_order(values):
    data = json.loads(values)
    data['doctype'] = 'Orders'
    data['status'] = 'Unpaid'
    data['posting_date'] = frappe.utils.now_datetime().date()
    data['posting_time'] = frappe.utils.now_datetime().time()
    for x in data['order_item']:
        x['item_name'] = frappe.get_doc("Item",x['item']).item_name
        x['status'] = "Preparing"
    frappe.get_doc(data).insert()
    frappe.db.sql(""" UPDATE `tabTable` SET status='Occupied' WHERE name=%s """,data['table'])
    frappe.db.commit()
    return get_orders()


@frappe.whitelist()
def void_order(order_name):
    order = frappe.get_doc("Orders",order_name)
    order.status = 'Void'
    order.save()
    change_table_status(order.table)

@frappe.whitelist()
def paid_order(order_name):
    order = frappe.get_doc("Orders",order_name)
    order.status = 'Paid'
    order.save()
    change_table_status(order.table)
def change_table_status(table):
    frappe.db.sql(""" UPDATE `tabTable` SET status='Available' WHERE name=%s """,table)
    frappe.db.commit()