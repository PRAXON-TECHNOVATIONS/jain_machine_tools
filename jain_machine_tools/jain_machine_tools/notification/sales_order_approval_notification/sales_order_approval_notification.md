<p>Dear Accounts Head,</p>

<p>A new Sales Order <b>{{ doc.name }}</b> has been submitted by <b>{{ frappe.db.get_value("User", doc.owner, "full_name") }}</b> and requires your financial approval.</p>

<p>Please review the credit limits and tax details before taking action:</p>

<p><a href="{{ frappe.utils.get_url_to_form('Sales Order', doc.name) }}" 
   style="padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; display: inline-block;">
   Review & Approve Sales Order
</a></p>

<p>Regards,<br>
ERPNext System</p>
