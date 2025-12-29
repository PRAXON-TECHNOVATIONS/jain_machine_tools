app_name = "jain_machine_tools"
app_title = "Jain Machine Tools"
app_publisher = "Praxon Technovation"
app_description = "Jain Machine Tools Application"
app_email = "avi.mathur@praxontech.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# boot_session = [
#     "jain_machine_tools.patches.reorder_patch.apply_reorder_patch"
# ]

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
# app_include_css = "/assets/jain_machine_tools/css/jain_machine_tools.css"
# app_include_js = "/assets/jain_machine_tools/js/jain_machine_tools.js"

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
    "Supplier": "public/js/supplier_terms.js",
    "Supplier Quotation": "public/js/supplier_quot_terms.js",
    "Material Request": "public/js/mr_item_duplicate.js",
    "Request for Quotation":"public/js/rfq_item_duplicate.js",
    "Purchase Order": "public/js/purchase_order_custom.js"
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
# jinja = {
# 	"methods": "jain_machine_tools.utils.jinja_methods",
# 	"filters": "jain_machine_tools.utils.jinja_filters"
# }

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

permission_query_conditions = {
    "Material Request": "jain_machine_tools.permissions.material_request_permission.material_request_permission",
    "Purchase Order":"jain_machine_tools.permissions.purchase_order_permission.purchase_order_permission"
}

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
        "validate": "jain_machine_tools.api.supplier_quotation.validate_duplicate_sq"
    },
    "Request for Quotation": {
        "before_insert": "jain_machine_tools.api.rfq.before_insert"
    },
    "Purchase Order": {
        "validate": "jain_machine_tools.api.purchase_order_discount.validate_items"
    },
    "Material Request": {
        "before_insert": "jain_machine_tools.patches.reorder_override.set_reorder_field"
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
# before_request = ["jain_machine_tools.utils.before_request"]
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
    {"doctype": "Workflow", "filters": [["name" , "in" , ("Purchase Order Approval","Supplier Approval", "Material Request Approval")]]},
    {"doctype": "Notification", "filters": [["document_type" , "in" , ("Purchase Order", "Material Request" , "Supplier")],["is_standard", "=", 0]]},
    {"doctype": "Email Template", "filters": [["name" , "in" , ("Request for Quotation Email")]]},
    {"doctype": "Server Script", "filters": [["name" , "in" , ("Purchase User Role see only approved suppliers")]]},
    {"doctype": "Print Format", "filters": [["name" , "in" , ("PO Print Format")]]},
    {"doctype": "Workspace", "filters": [["name" , "in" , ("Purchase")]]},
    {"doctype": "Custom DocPerm", "filters": [["role" , "in" , ("Store Manager")]]},
]   