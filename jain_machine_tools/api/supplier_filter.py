from frappe import whitelist, validate_and_sanitize_search_inputs, get_list


@whitelist()
@validate_and_sanitize_search_inputs
def supplier_query(doctype, txt, searchfield, start, page_len, filters):

    doctype = "Supplier"

    list_filters = {
        "workflow_state": "Approved"
    }

    or_filters = [
        [searchfield, "like", f"%{txt}%"],
        ["supplier_name", "like", f"%{txt}%"],
    ]

    if filters:
        list_filters.update(filters)

    return get_list(
        doctype,
        filters=list_filters,
        fields=["name", "supplier_name"],
        limit_start=start,
        limit_page_length=page_len,
        order_by="name asc",
        or_filters=or_filters,
        as_list=True,
    )
