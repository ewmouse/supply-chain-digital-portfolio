let currentExceptions = [];


function formatNumber(value) {

    if (
        value === null
        || value === undefined
    ) {
        return "--";
    }

    return Number(value)
        .toLocaleString();
}


function formatMoney(value) {

    if (
        value === null
        || value === undefined
    ) {
        return "--";
    }

    return "$"
        + Number(value)
            .toLocaleString(
                undefined,
                {
                    maximumFractionDigits: 0
                }
            );
}


function formatPct(value) {

    if (
        value === null
        || value === undefined
    ) {
        return "--";
    }

    return Number(value)
        .toFixed(1)
        + "%";
}


function badgeClass(
    value
) {

    if (value === "P1") {
        return "badge-p1";
    }

    if (value === "P2") {
        return "badge-p2";
    }

    if (value === "P3") {
        return "badge-p3";
    }

    if (
        value === "QUALITY_ALERT"
    ) {
        return "badge-alert";
    }

    if (
        value === "DELIVERY_RISK"
    ) {
        return "badge-risk";
    }

    if (
        value === "WATCH"
    ) {
        return "badge-watch";
    }

    return "badge-stable";
}


async function fetchJson(
    url
) {

    const response =
        await fetch(url);


    if (!response.ok) {

        throw new Error(
            `Request failed: ${url}`
        );

    }


    return await response.json();
}


async function loadOverview() {

    const data =
        await fetchJson(
            "/api/overview"
        );


    document
        .getElementById(
            "snapshotDate"
        )
        .textContent =
        data.snapshot_date;


    document
        .getElementById(
            "totalPartSite"
        )
        .textContent =
        formatNumber(
            data.total_part_site
        );


    document
        .getElementById(
            "exceptionCount"
        )
        .textContent =
        formatNumber(
            data.exception_count
        );


    document
        .getElementById(
            "confirmedShortage"
        )
        .textContent =
        formatNumber(
            data.confirmed_shortage_count
        );


    document
        .getElementById(
            "shortageRisk"
        )
        .textContent =
        formatNumber(
            data.shortage_risk_count
        );


    document
        .getElementById(
            "excessCandidate"
        )
        .textContent =
        formatNumber(
            data.excess_candidate_count
        );


    document
        .getElementById(
            "inventoryValue"
        )
        .textContent =
        formatMoney(
            data.inventory_value
        );


    document
        .getElementById(
            "blockedValue"
        )
        .textContent =
        formatMoney(
            data.blocked_inventory_value
        );
}


async function loadSites() {

    const data =
        await fetchJson(
            "/api/sites"
        );


    const select =
        document.getElementById(
            "siteFilter"
        );


    for (
        const site
        of data.sites
    ) {

        const option =
            document.createElement(
                "option"
            );


        option.value =
            site;


        option.textContent =
            site;


        select.appendChild(
            option
        );
    }
}


function buildExceptionUrl() {

    const priority =
        document.getElementById(
            "priorityFilter"
        ).value;


    const site =
        document.getElementById(
            "siteFilter"
        ).value;


    const exceptionType =
        document.getElementById(
            "exceptionFilter"
        ).value;


    const params =
        new URLSearchParams();


    if (priority) {

        params.set(
            "priority",
            priority
        );
    }


    if (site) {

        params.set(
            "site_id",
            site
        );
    }


    if (exceptionType) {

        params.set(
            "exception_type",
            exceptionType
        );
    }


    params.set(
        "limit",
        "500"
    );


    return (
        "/api/exceptions?"
        + params.toString()
    );
}


async function loadExceptions() {

    const loading =
        document.getElementById(
            "exceptionLoading"
        );


    loading.classList.remove(
        "hidden"
    );


    const data =
        await fetchJson(
            buildExceptionUrl()
        );


    currentExceptions =
        data;


    renderExceptions(
        data
    );


    loading.classList.add(
        "hidden"
    );
}


function renderExceptions(
    rows
) {

    const body =
        document.getElementById(
            "exceptionTableBody"
        );


    body.innerHTML = "";


    for (
        const row
        of rows
    ) {

        const tr =
            document.createElement(
                "tr"
            );


        tr.innerHTML = `
            <td>
                <span
                    class="
                        badge
                        ${badgeClass(
                            row.priority
                        )}
                    "
                >
                    ${row.priority}
                </span>
            </td>

            <td>
                ${row.site_id}
            </td>

            <td>
                <span
                    class="part-link"
                    data-part="${row.part_id}"
                    data-site="${row.site_id}"
                >
                    ${row.part_id}
                </span>
            </td>

            <td>
                ${row.part_family}
            </td>

            <td>
                ${row.criticality_class}
            </td>

            <td>
                ${row.supplier_id}
            </td>

            <td>
                ${row.exception_type}
            </td>

            <td>
                ${
                    row.coverage_weeks
                    ?? "--"
                }
            </td>

            <td>
                ${
                    row.shortage_gap_qty
                    ?? "--"
                }
            </td>

            <td>
                ${
                    row.otif_pct
                    === null
                    ? "--"
                    : formatPct(
                        row.otif_pct
                    )
                }
            </td>

            <td>
                ${row.suggested_action}
            </td>
        `;


        body.appendChild(
            tr
        );
    }


    document
        .querySelectorAll(
            ".part-link"
        )
        .forEach(
            element => {

                element.addEventListener(
                    "click",
                    () => {

                        openPartDrawer(
                            element.dataset.part,
                            element.dataset.site
                        );

                    }
                );

            }
        );
}


async function loadSuppliers() {

    const suppliers =
        await fetchJson(
            "/api/suppliers"
        );


    const body =
        document.getElementById(
            "supplierTableBody"
        );


    body.innerHTML = "";


    for (
        const supplier
        of suppliers
    ) {

        const tr =
            document.createElement(
                "tr"
            );


        const width =
            Math.max(
                0,
                Math.min(
                    100,
                    Number(
                        supplier.otif_pct
                        ?? 0
                    )
                )
            );


        tr.innerHTML = `
            <td>
                ${supplier.supplier_id}
            </td>

            <td>
                ${supplier.supplier_risk_class}
            </td>

            <td>
                ${supplier.po_count}
            </td>

            <td class="otif-cell">

                ${
                    formatPct(
                        supplier.otif_pct
                    )
                }

                <div class="otif-bar">

                    <div
                        class="otif-fill"
                        style="
                            width:
                            ${width}%;
                        "
                    >
                    </div>

                </div>

            </td>

            <td>
                ${
                    formatPct(
                        supplier.fill_rate_pct
                    )
                }
            </td>

            <td>
                ${
                    supplier.avg_late_days
                    ?? "--"
                }
            </td>

            <td>
                ${
                    supplier.critical_incident_count
                }
            </td>

            <td>
                ${
                    supplier.critical_a_part_count
                }
            </td>

            <td>

                <span
                    class="
                        badge
                        ${
                            badgeClass(
                                supplier.supplier_status
                            )
                        }
                    "
                >

                    ${
                        supplier.supplier_status
                    }

                </span>

            </td>
        `;


        body.appendChild(
            tr
        );
    }
}


async function openPartDrawer(
    partId,
    siteId
) {

    const drawer =
        document.getElementById(
            "partDrawer"
        );


    const overlay =
        document.getElementById(
            "drawerOverlay"
        );


    const content =
        document.getElementById(
            "drawerContent"
        );


    document
        .getElementById(
            "drawerPartId"
        )
        .textContent =
        `${partId} / ${siteId}`;


    content.innerHTML =
        "Loading part detail...";


    overlay.classList.remove(
        "hidden"
    );


    drawer.classList.add(
        "open"
    );


    const url =
        `/api/parts/${
            encodeURIComponent(
                partId
            )
        }?site_id=${
            encodeURIComponent(
                siteId
            )
        }`;


    const data =
        await fetchJson(
            url
        );


    renderPartDetail(
        data
    );
}


function renderPartDetail(
    data
) {

    const master =
        data.master;


    const current =
        data.current;


    const supplier =
        data.supplier;


    const content =
        document.getElementById(
            "drawerContent"
        );


    content.innerHTML = `
        <div class="detail-grid">

            ${detailCard(
                "Family",
                master.part_family
            )}

            ${detailCard(
                "Criticality",
                master.criticality_class
            )}

            ${detailCard(
                "Lead Time",
                `${master.lead_time_days} days`
            )}

            ${detailCard(
                "Unit Cost",
                formatMoney(
                    master.unit_cost
                )
            )}

            ${detailCard(
                "Supplier",
                master.supplier_id_primary
            )}

            ${detailCard(
                "Inventory Status",
                current?.inventory_status
                ?? "--"
            )}

            ${detailCard(
                "Available Inventory",
                current?.available_inventory
                ?? "--"
            )}

            ${detailCard(
                "Coverage",
                current?.coverage_weeks
                === null
                ? "--"
                : `${
                    current.coverage_weeks
                } weeks`
            )}

        </div>


        <div class="drawer-section">

            <h3>
                Supplier Performance
            </h3>

            <div class="detail-grid">

                ${detailCard(
                    "OTIF",
                    formatPct(
                        supplier?.otif_pct
                    )
                )}

                ${detailCard(
                    "Fill Rate",
                    formatPct(
                        supplier?.fill_rate_pct
                    )
                )}

                ${detailCard(
                    "Avg Late Days",
                    supplier?.avg_late_days
                    ?? "--"
                )}

                ${detailCard(
                    "Supplier Status",
                    supplier?.supplier_status
                    ?? "--"
                )}

            </div>

        </div>


        ${renderHistoryTable(
            data.history
        )}


        ${renderPurchaseOrders(
            data.purchase_orders
        )}
    `;
}


function detailCard(
    label,
    value
) {

    return `
        <div class="detail-card">

            <span>
                ${label}
            </span>

            <strong>
                ${value}
            </strong>

        </div>
    `;
}


function renderHistoryTable(
    history
) {

    const rows =
        history
            .slice(0, 12)
            .map(
                row => `
                    <tr>

                        <td>
                            ${row.date}
                        </td>

                        <td>
                            ${row.consumption_qty}
                        </td>

                        <td>
                            ${row.forecast_qty}
                        </td>

                        <td>
                            ${row.on_hand_qty}
                        </td>

                        <td>
                            ${row.available_inventory}
                        </td>

                        <td>
                            ${
                                row.coverage_weeks
                                ?? "--"
                            }
                        </td>

                        <td>
                            ${row.inventory_status}
                        </td>

                    </tr>
                `
            )
            .join("");


    return `
        <div class="drawer-section">

            <h3>
                Recent Inventory History
            </h3>

            <div class="table-wrapper">

                <table>

                    <thead>

                        <tr>
                            <th>Date</th>
                            <th>Consumption</th>
                            <th>Forecast</th>
                            <th>On Hand</th>
                            <th>Available</th>
                            <th>Coverage</th>
                            <th>Status</th>
                        </tr>

                    </thead>

                    <tbody>
                        ${rows}
                    </tbody>

                </table>

            </div>

        </div>
    `;
}


function renderPurchaseOrders(
    orders
) {

    const rows =
        orders
            .map(
                order => `
                    <tr>

                        <td>
                            ${order.po_id}
                        </td>

                        <td>
                            ${order.promised_date}
                        </td>

                        <td>
                            ${order.receipt_date}
                        </td>

                        <td>
                            ${order.ordered_qty}
                        </td>

                        <td>
                            ${order.received_qty}
                        </td>

                        <td>
                            ${order.delay_days}
                        </td>

                    </tr>
                `
            )
            .join("");


    return `
        <div class="drawer-section">

            <h3>
                Recent Purchase Orders
            </h3>

            <div class="table-wrapper">

                <table>

                    <thead>

                        <tr>
                            <th>PO</th>
                            <th>Promised</th>
                            <th>Received</th>
                            <th>Ordered</th>
                            <th>Received Qty</th>
                            <th>Delay</th>
                        </tr>

                    </thead>

                    <tbody>
                        ${rows}
                    </tbody>

                </table>

            </div>

        </div>
    `;
}


function closePartDrawer() {

    document
        .getElementById(
            "partDrawer"
        )
        .classList.remove(
            "open"
        );


    document
        .getElementById(
            "drawerOverlay"
        )
        .classList.add(
            "hidden"
        );
}


function downloadExceptionsCsv() {

    if (
        currentExceptions.length === 0
    ) {
        return;
    }


    const columns = [
        "priority",
        "site_id",
        "part_id",
        "part_family",
        "criticality_class",
        "supplier_id",
        "exception_type",
        "available_inventory",
        "demand_signal",
        "coverage_weeks",
        "shortage_gap_qty",
        "otif_pct",
        "supplier_status",
        "suggested_action"
    ];


    const csvRows = [
        columns.join(",")
    ];


    for (
        const row
        of currentExceptions
    ) {

        const values =
            columns.map(
                column => {

                    const value =
                        row[column]
                        ?? "";


                    const safeValue =
                        String(value)
                            .replaceAll(
                                '"',
                                '""'
                            );


                    return `"${safeValue}"`;
                }
            );


        csvRows.push(
            values.join(",")
        );
    }


    const blob =
        new Blob(
            [
                csvRows.join("\n")
            ],
            {
                type:
                    "text/csv;charset=utf-8"
            }
        );


    const url =
        URL.createObjectURL(
            blob
        );


    const link =
        document.createElement(
            "a"
        );


    link.href =
        url;


    link.download =
        "supply_chain_exceptions.csv";


    link.click();


    URL.revokeObjectURL(
        url
    );
}


document
    .getElementById(
        "priorityFilter"
    )
    .addEventListener(
        "change",
        loadExceptions
    );


document
    .getElementById(
        "siteFilter"
    )
    .addEventListener(
        "change",
        loadExceptions
    );


document
    .getElementById(
        "exceptionFilter"
    )
    .addEventListener(
        "change",
        loadExceptions
    );


document
    .getElementById(
        "downloadButton"
    )
    .addEventListener(
        "click",
        downloadExceptionsCsv
    );


document
    .getElementById(
        "closeDrawerButton"
    )
    .addEventListener(
        "click",
        closePartDrawer
    );


document
    .getElementById(
        "drawerOverlay"
    )
    .addEventListener(
        "click",
        closePartDrawer
    );


async function initializeDashboard() {

    try {

        await Promise.all(
            [
                loadOverview(),
                loadSites(),
                loadSuppliers(),
            ]
        );


        await loadExceptions();

    }
    catch (error) {

        console.error(
            error
        );


        alert(
            "Dashboard failed to load. "
            + "Please check the API server."
        );

    }
}


initializeDashboard();