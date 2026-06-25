# Detailed Non-Functional Requirements (NFRs)

This document outlines the Non-Functional Requirements for the Cognitive Digital Twin (CDT) framework, ensuring the system is robust, fast, user-friendly, and secure.

### Quick Reference Table (For Presentation Slide)

| NFR ID | Category | Requirement Summary |
| :--- | :--- | :--- |
| **NFR-01** | **Reliability** | Must guarantee 99.9% uptime and implement auto-retry logic with cached fallbacks in case the NASA POWER API drops connection. |
| **NFR-02** | **Performance** | Interactive "What-If" climate simulations must return updated risk predictions to the UI in under 2 seconds. |
| **NFR-03** | **Scalability** | The backend architecture must be horizontally scalable to support multi-state expansion beyond the initial Odisha pilot without schema redesigns. |
| **NFR-04** | **Usability (HCI)** | The Expert Advisory Chatbot must translate complex tensor outputs into plain, non-academic language for farmers. |
| **NFR-05** | **Security** | All API data transfers must use HTTPS/TLS encryption; role-based access must separate 'Analyst' read/write privileges from 'Farmer' read-only access. |
| **NFR-06** | **Maintainability** | The ML engine must be fully decoupled from the UI, allowing data scientists to swap out deep learning models without breaking the dashboard. |

---

## Detailed Explanations

### NFR-01: Reliability & Availability
*   **Target:** The Decision Support System (DSS) must be highly reliable, particularly during critical decision-making windows (e.g., the onset of the Kharif season).
*   **Mechanism:** The backend must gracefully handle external dependencies. If the UPAg API or NASA POWER API experiences an outage, the system must not crash. Instead, it must utilize the most recently cached telemetry and initiate exponential backoff retries.

### NFR-02: Performance & Latency
*   **Simulation Speed:** When an Agricultural Analyst adjusts the temperature or humidity sliders on the dashboard, the backend Simulation Engine (executing Monte Carlo scenarios through the Dual-Track ML models) must return the new failure probabilities in **under 2 seconds** to maintain a fluid user experience.
*   **Pipeline Speed:** The initial ETL pipeline must be highly optimized, capable of interpolating and harmonizing 20 years of historical yield data alongside millions of daily weather data points in under 5 minutes during routine seasonal syncs.

### NFR-03: Scalability
*   **Data Volume Handling:** While the pilot project is specifically stratified for the districts of Odisha, the database schema and data ingestion pipelines must be designed dynamically. This ensures the system can effortlessly scale to absorb millions of new rows if the framework is expanded nationwide (e.g., to Punjab or Maharashtra).

### NFR-04: Human-Computer Interface (Usability)
*   **Accessibility:** The frontend dashboard must implement an intuitive, modern user interface (e.g., glassmorphism styling, clean GIS map overlays) that makes complex Deep Learning predictions immediately understandable.
*   **Language Constraint:** The LangGraph-powered Expert Advisory Chatbot must be strictly constrained by its system prompt to never output raw mathematical variables (like "LSTM attention weight = 0.89") to the farmer. It must translate these metrics into actionable, plain-language agronomic advice (e.g., "High risk of thermal stress detected; increase irrigation").

### NFR-05: Security & Data Privacy
*   **Data in Transit:** All communications between the React Frontend, the FastAPI Backend, and the LangGraph Orchestrator must be secured via standard HTTPS/TLS protocols.
*   **Access Control:** The system must implement Role-Based Access Control (RBAC). A 'Farmer' profile should have simplified, read-only access to failure risks and the chatbot, whereas an 'Analyst' profile requires elevated permissions to execute heavy "What-If" simulations and view deep-dive historical trends.

### NFR-06: Maintainability & Extensibility
*   **Decoupled Architecture:** The system must follow strict Object-Oriented Analysis and Design (OOAD) principles. The `Model` classes (RF/LSTM) must be fully decoupled from the `Dashboard` class via REST APIs. This ensures that if the research team upgrades the LSTM to a more advanced architecture (like a Time-Series Vision Transformer) in the future, the frontend UI requires absolutely zero code changes.
