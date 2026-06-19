(function () {
    const SEARCH_TEXT = "Search...";
    const SEARCH_HELP = "Search existing records. Use the plus button to add a new record.";

    function updateSelect2Hints(root) {
        const scope = root || document;

        scope.querySelectorAll(".select2-container").forEach((container) => {
            const selection = container.querySelector(".select2-selection");
            if (selection) {
                selection.setAttribute("title", SEARCH_HELP);
                selection.setAttribute("aria-label", SEARCH_HELP);
                selection.style.cursor = "pointer";
            }
        });

        scope.querySelectorAll(".select2-search__field").forEach((field) => {
            field.setAttribute("placeholder", SEARCH_TEXT);
            field.setAttribute("title", SEARCH_HELP);
            field.setAttribute("aria-label", SEARCH_HELP);
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        updateSelect2Hints();

        if (window.django && window.django.jQuery) {
            window.django.jQuery(document).on("select2:open select2:opening select2:close", () => {
                window.setTimeout(() => updateSelect2Hints(), 0);
            });
        }

        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        updateSelect2Hints(node);
                    }
                });
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });
    });
})();
