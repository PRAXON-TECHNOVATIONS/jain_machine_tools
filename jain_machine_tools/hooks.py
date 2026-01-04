app_name = "jain_machine_tools"
app_title = "Jain Machine Tools"
app_publisher = "Praxon Technovation"
app_description = "Jain Machine Tools Application"
app_email = "avi.mathur@praxontech.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "jain_machine_tools",
# 		"logo": "/assets/jain_machine_tools/logo.png",
# 		"title": "Jain Machine Tools",
# 		"route": "/jain_machine_tools",
# 		"has_permission": "jain_machine_tools.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
    "https://cdn.form.io/formiojs/formio.full.min.css",
    "/assets/jain_machine_tools/css/formio_custom.css?v=5"
]
app_include_js = [
    "/assets/jain_machine_tools/js/grid_custom_icons.js?v=6.7"
]

# include js, css files in header of web template
# web_include_css = "/assets/jain_machine_tools/css/jain_machine_tools.css"
# web_include_js = "/assets/jain_machine_tools/js/jain_machine_tools.js"
# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "jain_machine_tools/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
    "Purchase Receipt": "public/js/purchase_receipt_custom.js",
    "Purchase Order": "public/js/purchase_order_custom.js",
    "Quotation": "public/js/quotation_custom.js",
    "Sales Order": "public/js/sales_order_custom.js",
    "Supplier": "public/js/supplier_terms.js",
    "Supplier Quotation": "public/js/supplier_quot_terms.js",
    "Material Request": "public/js/mr_item_duplicate.js",
    "Request for Quotation":"public/js/rfq_item_duplicate.js",
    "Item": "public/js/item.js",
}

# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "jain_machine_tools/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
	"methods": [
		"jain_machine_tools.jain_machine_tools.doctype.barcode_printing.barcode_printing.get_barcode_image"
	]
}

# Installation
# ------------

# before_install = "jain_machine_tools.install.before_install"
# after_install = "jain_machine_tools.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "jain_machine_tools.uninstall.before_uninstall"
# after_uninstall = "jain_machine_tools.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "jain_machine_tools.utils.before_app_install"
# after_app_install = "jain_machine_tools.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "jain_machine_tools.utils.before_app_uninstall"
# after_app_uninstall = "jain_machine_tools.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "jain_machine_tools.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

doc_events = {
    "Supplier Quotation": {
        "validate": [
            "jain_machine_tools.api.supplier_quotation.validate_duplicate_sq",
            "jain_machine_tools.api.auto_populate_supplier_code.populate_supplier_item_code"
        ]
    },
    "Purchase Order": {
        "validate": "jain_machine_tools.api.auto_populate_supplier_code.populate_supplier_item_code"
    },
    "Serial No": {
        "on_update": "jain_machine_tools.api.serial_no_hooks.on_update"
    },
    "Quotation": {
        "validate": "jain_machine_tools.overrides.quotation.validate_quotation"
    },
    "Sales Order": {
        "validate": "jain_machine_tools.overrides.quotation.validate_sales_order"
    },
    "Sales Invoice": {
        "validate": "jain_machine_tools.overrides.quotation.validate_sales_invoice"
    },
    "Delivery Note": {
        "validate": "jain_machine_tools.overrides.quotation.validate_delivery_note"
    }
}


# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"jain_machine_tools.tasks.all"
# 	],
# 	"daily": [
# 		"jain_machine_tools.tasks.daily"
# 	],
# 	"hourly": [
# 		"jain_machine_tools.tasks.hourly"
# 	],
# 	"weekly": [
# 		"jain_machine_tools.tasks.weekly"
# 	],
# 	"monthly": [
# 		"jain_machine_tools.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "jain_machine_tools.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "jain_machine_tools.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "jain_machine_tools.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
before_request = ["jain_machine_tools.overrides.quotation.patch_insert_item_price"]
# after_request = ["jain_machine_tools.utils.after_request"]

# Job Events
# ----------
# before_job = ["jain_machine_tools.utils.before_job"]
# after_job = ["jain_machine_tools.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"jain_machine_tools.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
standard_queries = {
    "Supplier": "jain_machine_tools.api.supplier_filter.supplier_query"
}

fixtures = [
    'Custom Field',
    {"doctype": "Workflow", "filters": [["name" , "in" , ("Purchase Order Approval","Supplier Approval", "Material Request Approval")]]},
    {"doctype": "Notification", "filters": [["name" , "in" , ("PO Send to Supplier After Approval","Purchase Order Approval - Notify Purchase Manager","New Supplier Created – Approval Required Mail", "New Supplier Created – Approval Required Notification")]]},
    {"doctype": "Email Template", "filters": [["name" , "in" , ("Request for Quotation Email")]]},
    {"doctype": "Print Format","filters":[["module", "in", "Jain Machine Tools"]]}
]
