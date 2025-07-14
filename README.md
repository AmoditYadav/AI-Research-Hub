# 🤖 AI Research Hub

An intelligent, multi-agent system designed for comprehensive talent scouting and deep company analysis. This tool leverages large language models (LLMs) via the Groq API to provide actionable intelligence for recruiters, analysts, and business development professionals.

---

## 🚀 Features

This application is composed of two specialized AI agents accessible through a unified Streamlit interface:

### 1. The Talent Scout Agent
-   **Objective:** Find potential candidates on LinkedIn based on specific job criteria.
-   **Workflow:**
    -   Dynamically generates targeted Google search queries (`site:linkedin.com/in/...`).
    -   Executes searches to find public profiles.
    -   Formats the results into a clean, readable report with profile links.

### 2. The Company Analyst Agent
-   **Objective:** Provide a full-spectrum intelligence report on any given company.
-   **Workflow:**
    -   **Data Gathering:** Performs a wide array of targeted searches to gather information on:
        -   **General News:** Developments, funding, partnerships, acquisitions.
        -   **Public Perception:** Controversies, criticisms, lawsuits, and layoffs.
        -   **Employee Sentiment:** Glassdoor reviews, ratings, pros, and cons.
        -   **Job Vacancies:** Scans prominent job boards (`Naukri`, `LinkedIn`, `Indeed`) and major Applicant Tracking Systems (`Lever`, `Greenhouse`).
    -   **AI Synthesis:** Feeds all gathered context to a powerful LLM (`llama3-70b-8192`).
    -   **Structured Reporting:** The LLM generates a detailed report with three key sections:
        1.  **Company Standing & Public Perception:** A balanced view of positive developments and potential challenges, with all points cited with source URLs.
        2.  **Glassdoor Employee Sentiment:** A summary of employee reviews and ratings.
        3.  **Potential Open Vacancies:** A list of currently open jobs with links to the postings.

---

## 🛠️ Tech Stack

-   **Backend:** Python
-   **UI:** Streamlit
-   **AI Orchestration:** LangChain & LangGraph
-   **LLM Provider:** Groq (using `llama3-70b-8192`)
-   **Search Tool:** Tavily Search API

---

## ⚙️ Setup & Installation

Follow these steps to run the project locally:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/AmoditYadav/AI-Research-Hub.git
    cd AI-Research-Hub
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create a `.env` file:**
    -   Create a file named `.env` in the root of the project folder.
    -   Add your secret API keys to this file:
        ```
        GROQ_API_KEY="gsk_YourGroqAPIKey"
        TAVILY_API_KEY="tvly-YourTavilyAPIKey"
        ```

5.  **Run the Streamlit application:**
    ```bash
    streamlit run app.py
    ```

---

## 📖 Usage

Once the application is running, you will see two tabs:

-   **Talent Scout:** Enter job criteria (role, skills, location, domain) and click "Scout for Talent" to find relevant LinkedIn profiles.
-   **Company Research:** Enter a company name and click "Generate Company Report" to receive a detailed intelligence briefing.
