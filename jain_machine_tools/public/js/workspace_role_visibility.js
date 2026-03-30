(function () {
	const STORE_MANAGER_ROLE = "Store Manager";
	const HIDDEN_WIDGET_SELECTORS = [".dashboard-widget-box", ".number-widget-box"];
	const EXCLUDED_ROLES = ["Administrator", "System Manager"];

	function getUserRoles() {
		return frappe.boot?.user?.roles || [];
	}

	function shouldHideForUser() {
		const roles = getUserRoles();
		const hasStoreManagerRole = Boolean(frappe.user?.has_role?.(STORE_MANAGER_ROLE));
		const hasExcludedRole = roles.some((role) => EXCLUDED_ROLES.includes(role));

		return hasStoreManagerRole && !hasExcludedRole;
	}

	function hideWorkspaceMetrics() {
		if (!shouldHideForUser()) {
			return;
		}

		HIDDEN_WIDGET_SELECTORS.forEach((selector) => {
			document.querySelectorAll(selector).forEach((element) => {
				const block = element.closest(".ce-block");
				(block || element).style.display = "none";
			});
		});
	}

	function observeWorkspaceRender() {
		const workspaceRoot = document.querySelector("#editorjs");
		if (!workspaceRoot || workspaceRoot.dataset.storeManagerVisibilityBound) {
			return;
		}

		const observer = new MutationObserver(() => hideWorkspaceMetrics());
		observer.observe(workspaceRoot, { childList: true, subtree: true });
		workspaceRoot.dataset.storeManagerVisibilityBound = "1";
		hideWorkspaceMetrics();
	}

	function applyRoleVisibility() {
		hideWorkspaceMetrics();
		observeWorkspaceRender();
	}

	frappe.router?.on?.("change", () => {
		frappe.after_ajax(() => {
			setTimeout(applyRoleVisibility, 50);
		});
	});

	$(document).on("page-change", () => {
		setTimeout(applyRoleVisibility, 50);
	});
})();
