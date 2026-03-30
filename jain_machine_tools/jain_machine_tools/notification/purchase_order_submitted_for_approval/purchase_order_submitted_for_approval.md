<p>Dear Purchase Manager,</p>

<p>Purchase Order <b>{{ doc.name }}</b> has been submitted and requires your approval.</p>

<p>Please review the document before taking action:</p>

<p><a href="{{ frappe.utils.get_url_to_form('Sales Order', doc.name) }}" 
   style="padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; display: inline-block;">
   Review & Approve Purchase Order
</a></p>

<p>Regards,<br>
ERPNext System</p>
