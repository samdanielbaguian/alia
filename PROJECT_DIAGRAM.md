# Alia Project Diagram

This file contains the full workspace architecture diagram.

```mermaid
flowchart TB
    A[Alia Workspace]

    A --> DOCS[Project Docs]
    A --> SAMPLES[API Payload Samples]
    A --> FE[alia-dashboard (Next.js Frontend)]
    A --> BE[backend (FastAPI Backend)]
    A --> INFRA[Infrastructure]

    DOCS --> D1[README.md]
    DOCS --> D2[ADMIN_SYSTEM_DOCUMENTATION.md]
    DOCS --> D3[PAYMENT_SYSTEM.md]
    DOCS --> D4[IMPLEMENTATION_SUMMARY.md]
    DOCS --> D5[IMPLEMENTATION_SUMMARY_ORDER_MANAGEMENT.md]
    DOCS --> D6[backend/API_DOCUMENTATION.md]
    DOCS --> D7[backend/MERCHANT_DASHBOARD_ENDPOINTS.md]
    DOCS --> D8[backend/ORDER_MANAGEMENT_GUIDE.md]
    DOCS --> D9[backend/QUICKSTART.md]

    SAMPLES --> S1[alia commande/*.json, *.txt]

    INFRA --> I1[docker-compose.yml]
    INFRA --> I2[backend/Dockerfile]
    INFRA --> I3[backend/requirements.txt]

    FE --> FE_APP[app]
    FE --> FE_COMP[components]
    FE --> FE_LAYOUT[layout]
    FE --> FE_DATA[data/mockData.js]
    FE --> FE_STYLE[styles]
    FE --> FE_UTILS[utils]
    FE --> FE_CFG[next.config.mjs, eslint.config.mjs, jsconfig.json]

    FE_APP --> FE_ROOT_PAGES[layout.js, page.js]
    FE_APP --> FE_DASH[dashboard]
    FE_APP --> FE_PRODUCT[product/[id]]
    FE_APP --> FE_STORE[store/[slug]]

    FE_DASH --> FE_D1[overview]
    FE_DASH --> FE_D2[orders]
    FE_DASH --> FE_D3[products]
    FE_DASH --> FE_D4[customers]
    FE_DASH --> FE_D5[reports]
    FE_DASH --> FE_D6[sellers]
    FE_DASH --> FE_D7[admin]
    FE_DASH --> FE_D8[activity]
    FE_DASH --> FE_D9[alerts]
    FE_DASH --> FE_D10[heatmap]
    FE_DASH --> FE_D11[best-sellers]
    FE_DASH --> FE_D12[custom-orders]
    FE_DASH --> FE_D13[settings]
    FE_DASH --> FE_D14[export]

    FE_COMP --> FE_C1[cards/KPICard.js]
    FE_COMP --> FE_C2[charts/*]
    FE_COMP --> FE_C3[tables/DataTable.js]
    FE_COMP --> FE_C4[widgets/*]

    FE_LAYOUT --> FE_L1[DashboardLayout.js]
    FE_LAYOUT --> FE_L2[Header.js]
    FE_LAYOUT --> FE_L3[Sidebar.js]
    FE_LAYOUT --> FE_L4[constants.js]

    FE_UTILS --> FE_U1[api.js]
    FE_UTILS --> FE_U2[AdminApi.js]
    FE_UTILS --> FE_U3[authUtils.js]
    FE_UTILS --> FE_U4[protectedRoute.js]
    FE_UTILS --> FE_U5[helpers.js]

    BE --> BE_MAIN[app/main.py]
    BE --> BE_API[app/api]
    BE --> BE_CORE[app/core]
    BE --> BE_CONFIG[app/config]
    BE --> BE_MODELS[app/models]
    BE --> BE_SCHEMAS[app/schemas]
    BE --> BE_SERVICES[app/services]
    BE --> BE_UTILS[app/utils]
    BE --> BE_UPLOADS[app/uploads]
    BE --> BE_SCRIPTS[scripts]
    BE --> BE_TESTS[tests]

    BE_API --> BE_DEPS[deps.py]
    BE_API --> BE_ROUTES[routes/*]

    BE_ROUTES --> R1[auth, users, merchants, products]
    BE_ROUTES --> R2[orders, admin_orders, admin_products]
    BE_ROUTES --> R3[admin_users, admin_merchants]
    BE_ROUTES --> R4[payments, cart, uploads]
    BE_ROUTES --> R5[aliexpress, buybox]

    BE_MODELS --> M1[user.py, merchant.py, product.py]
    BE_MODELS --> M2[order.py, cart.py]
    BE_MODELS --> M3[payment.py, refund.py, share.py]

    BE_SCHEMAS --> SCH1[auth.py, user.py, product.py]
    BE_SCHEMAS --> SCH2[order.py, cart.py, dashboard.py]
    BE_SCHEMAS --> SCH3[payment.py, share.py]

    BE_SERVICES --> SV1[order_service.py]
    BE_SERVICES --> SV2[payment_service.py]
    BE_SERVICES --> SV3[cart_service.py]
    BE_SERVICES --> SV4[buybox_service.py, aliexpress_service.py]
    BE_SERVICES --> SV5[share_service.py, duplicate_detection.py]
    BE_SERVICES --> SV6[payment_providers/*]

    SV6 --> PP1[mtn_money_service.py]
    SV6 --> PP2[orange_money_service.py]
    SV6 --> PP3[moov_money_service.py]
    SV6 --> PP4[simulation_service.py]

    BE_SCRIPTS --> SC1[setup_test_data.py]
    BE_SCRIPTS --> SC2[cleanup_test_data.py]
    BE_SCRIPTS --> SC3[smoke_test_admin.py]

    BE_TESTS --> T1[test_main.py]
    BE_TESTS --> T2[test_order_service.py]
    BE_TESTS --> T3[test_payment_*.py]
    BE_TESTS --> T4[test_merchant_*.py]
    BE_TESTS --> T5[test_refund_service.py]
    BE_TESTS --> T6[test_heatmap.py]
```
