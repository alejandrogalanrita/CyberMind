const API_ROUTE = 'http://localhost:3000/api'

fetchCveData();

function fetchCveData() {
    fetch(API_ROUTE + '/cve', { 
            method : "GET",
            credentials : 'include' 
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Network response was not ok: " + response.statusText);
            }
            return response.json();
        })
        .then(cveData => {
            populateTable(cveData);
        })
        .catch(error => {
            console.error("Error fetching CVE data:", error);
        });
}

function populateTable(cveData) {
    const table = document.getElementById("cve-table");

    // Ensure a tbody exists
    let tbody = table.querySelector("tbody");
    if (!tbody) {
        tbody = document.createElement("tbody");
        table.appendChild(tbody);
    }
    
    // Clear any previous rows
    tbody.innerHTML = "";

    cveData.forEach(item => {
        const tr = document.createElement("tr");

        const cveIdTd = document.createElement("td");
        cveIdTd.textContent = item.cve_id || "";
        tr.appendChild(cveIdTd);

        const descTd = document.createElement("td");
        descTd.textContent = item.description || "";
        tr.appendChild(descTd);

        const pubDateTd = document.createElement("td");
        pubDateTd.textContent = item.published_date || "";
        tr.appendChild(pubDateTd);

        const modDateTd = document.createElement("td");
        modDateTd.textContent = item.last_modified_date || "";
        tr.appendChild(modDateTd);

        const cvssTd = document.createElement("td");
        cvssTd.textContent = item.cvss_score != null ? item.cvss_score : "";
        tr.appendChild(cvssTd);

        const severityTd = document.createElement("td");
        severityTd.textContent = item.severity || "";
        tr.appendChild(severityTd);

        const cweTd = document.createElement("td");
        cweTd.textContent = item.cwe_id || "";
        tr.appendChild(cweTd);

        tbody.appendChild(tr);
    });
}