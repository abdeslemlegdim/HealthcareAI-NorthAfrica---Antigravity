const fs = require('fs');
const file = 'frontend-react/src/pages/DashboardPage.jsx';
let content = fs.readFileSync(file, 'utf8');

// Replace {t("...") || "Fallback"} with Fallback
content = content.replace(/\{t\(\"([^\"]+)\"\)\s*\|\|\s*\"([^\"]+)\"\}/g, '$2');
// Replace t("...") || "Fallback" with "Fallback" (e.g. in attributes)
content = content.replace(/t\(\"([^\"]+)\"\)\s*\|\|\s*\"([^\"]+)\"/g, '"$2"');

fs.writeFileSync(file, content);
console.log('Fixed translations in DashboardPage.jsx');
