<p>Dear Sales Head,</p>

<p>A new Quotation <b>{{ doc.name }}</b> has been submitted for your approval by <b>{{ frappe.db.get_value("User", doc.owner, "full_name") }}</b>.</p>

<p><b>Customer:</b> {{ doc.customer }}<br>
<b>Total Amount:</b> {{ doc.get_formatted("grand_total") }}</p>

<p>Please review and take the necessary action by clicking the link below:</p>

<p><a href="{{ frappe.utils.get_url_to_form('Quotation', doc.name) }}" 
   style="padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">
   View Quotation
</a></p>

<p>Regards,<br>
ERPNext System</p>
