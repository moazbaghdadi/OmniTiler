// Shared shell tooltips can interpret rich text; escape all external content.
function escapeMarkup(value) {
    return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
