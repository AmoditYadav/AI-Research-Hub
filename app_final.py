import os
import streamlit as st
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import TypedDict, List
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate


load_dotenv()


@tool
def google_search_tool(query: str) -> list:
    """
    Use this tool to search Google. It returns a list of dictionaries,
    where each dictionary contains the 'url', 'title', and 'content' of a search result.
    """
    print(f"TOOL: Searching Google for: {query}")
    try:
        tavily_search=TavilySearchResults(max_results=7, include_raw_content=True)
        # We will use the structured list of dictionaries from Tavily directly
        results = tavily_search.invoke(query)
        # The result is already a list of dicts, no need to process it further.
        return results
    except Exception as e:
        print(f"Error in Tavily Search: {e}")
        return []
# runs the queries using tavily to gather the results


class AgentState(TypedDict):
    job_criteria:dict
    google_queries:List[str]
    # This key is now more descriptive. It will hold the list of dicts from Tavily.
    search_results:List[dict]
    final_report:str


llm=ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0)

def query_generation_node(state: AgentState):
    print("NODE: Generating Google Queries")
    criteria=state["job_criteria"]
    prompt=ChatPromptTemplate.from_messages([
        ("system", "You are an expert technical recruiter. Generate 7 targeted Google search queries to find public LinkedIn profiles. Create a mix of specific and broader queries. Each query must start with 'site:linkedin.com/in/'. Return ONLY a list of strings separated by newlines."),
        ("human", f"Job Criteria:\nRole: {criteria['role']}\nSkills:{criteria['skills']}\nLocation: {criteria['location']}\nDomain: {criteria['domain']}")
    ]) 
    chain=prompt | llm
    response_text=chain.invoke({}).content
    queries=[q.strip() for q in response_text.split("\n") if q.strip() and "site:linkedin.com/in/" in q]
    return {"google_queries": queries}

#creates the queries using the LLM
#User input → query_generation_node → google_search_tool → report_node

def search_node(state: AgentState):
    """
    Executes the search queries and aggregates the rich search result dictionaries.
    """
    print("NODE: Searching for Profiles")
    queries=state["google_queries"]
    all_results=[]
    for query in queries:
        # The tool now returns a list of dictionaries
        results=google_search_tool.invoke(query)
        all_results.extend(results)

    # De-duplicate results based on the URL to ensure each profile is unique
    unique_results_dict={item['url']: item for item in all_results}
    unique_results_list=list(unique_results_dict.values())
    
    print(f"Found {len(unique_results_list)} unique profiles.")
    # Update the state with the list of dictionaries
    return {"search_results": unique_results_list}
# takes the search queries, calls the search tool for each one. takees input from the previous node queries


def report_node(state: AgentState):
    """
    This node now takes the list of rich search results and formats them
    into a detailed markdown report for the user.
    """
    print("NODE: Generating Final Report")
    search_results = state["search_results"]
    
    if not search_results:
        report="No public LinkedIn profiles found matching the criteria. Try broadening your search terms."
    else:
        report=f"## AI Talent Scout Report\n\nFound **{len(search_results)}** potential candidate profiles:\n\n---\n\n"
        
        for result in search_results:
            # Extract the title, which often contains Name and Headline
            title = result.get('title', 'No Title Found')
            # Extract the content snippet provided by the search engine
            content_snippet = result.get('content', 'No summary available.')
            # Get the profile URL
            url = result.get('url', '#')
            
            # Format each result as a separate entry
            report += f"### {title}\n"
            report += f"**Summary from Search:** {content_snippet}\n\n"
            report += f"**Profile Link:** [{url}]({url})\n\n"
            report += "---\n\n"
    
    return {"final_report": report}


graph_builder=StateGraph(AgentState)

graph_builder.add_node("query_generator", query_generation_node)
graph_builder.add_node("google_searcher", search_node)
graph_builder.add_node("report_generator", report_node)

graph_builder.add_edge(START, "query_generator")
graph_builder.add_edge("query_generator", "google_searcher")
graph_builder.add_edge("google_searcher", "report_generator")
graph_builder.add_edge("report_generator", END)

app_graph = graph_builder.compile()

## Company search Functionality

class CompanyAgentState(TypedDict):
    """state for the company research agent"""
    company_name:str
    news_results:List[dict]
    jobs_result:List[dict]
    glassdoor_results:List[dict]
    final_report:str

def company_search_node(state:CompanyAgentState):
    """sarches for news and job openings related to the company"""
    company_name=state['company_name']
    print(f"NODE (Company): Searching for news and jobs for {company_name}")
    news_queries=[
        f'"{company_name}" recent news and developments',
        f'"{company_name}" partnerships OR funding OR acquisition',
        f'"{company_name}" product launch OR new service offering',
        f'"{company_name}" leadership changes OR executive appointments',
        f'"{company_name}" quarterly earnings OR financial report',
        f'"{company_name}" controversy OR criticism OR lawsuit OR layoffs',
        f'"{company_name}" government partnership OR government funding',
        f'"{company_name}" market position OR competitor analysis',
    ]
    jobs_queries = [
        f'site:naukri.com "{company_name}"',
        f'site:linkedin.com/jobs/ inurl:jobs "{company_name}"',
        f'site:indeed.co.in "{company_name}"',
        f'site:glassdoor.co.in "{company_name}" jobs',
        f'site:jobs.lever.co "{company_name}"',
        f'site:boards.greenhouse.io "{company_name}"',
        f'"{company_name}" "careers" OR "job openings"',
    ]
    
    glassdoor_queries=[
        f'site:glassdoor.co.in "{company_name}" "Overall Rating"',
        f'site:glassdoor.co.in "{company_name}" "Reviews" "pros" "cons"',
        f'site:glassdoor.co.in "{company_name}" "CEO Approval"',
    ]
    
    news_results=[]
    for query in news_queries:
        news_results.extend(google_search_tool.invoke(query))
    
    jobs_results=[]
    for query in jobs_queries:
        jobs_results.extend(google_search_tool.invoke(query))

    glassdoor_results=[]
    for query in glassdoor_queries:
        glassdoor_results.extend(google_search_tool.invoke(query))

    # de duplicating the results
    unique_news = list({item['url']: item for item in news_results}.values())
    unique_jobs = list({item['url']: item for item in jobs_results}.values())
    unique_glassdoor = list({item['url']: item for item in glassdoor_results}.values())

    return {"news_results":unique_news,"jobs_results":unique_jobs,"glassdoor_results":unique_glassdoor}

def company_report_node(state:CompanyAgentState):
    print("NODE (Company): Generating Company Report")
    company_name=state['company_name']
    news_results =state.get('news_results',[])
    jobs_results = state.get('jobs_results',[])
    glassdoor_results=state.get('glassdoor_results',[])

    num_news_items = len(news_results)
    if num_news_items > 12:
        summary_instruction = "a comprehensive summary of 6-8 key points"
    elif num_news_items > 5:
        summary_instruction = "a summary of the main 4-6 key points"
    else:
        summary_instruction = "a brief summary of 1-3 key points"
    
    print(f"Found {num_news_items} news items. Requesting: {summary_instruction}.")

    news_context="\n---\n".join([f"URL: {res.get('url', 'N/A')}\nTitle: {res.get('title', '')}\nSnippet: {res.get('content', '')}" for res in news_results])

    jobs_context="\n---\n".join([f"URL: {res.get('url', 'N/A')}\nTitle: {res.get('title', '')}\nSnippet: {res.get('content', '')}" for res in jobs_results])

    glassdoor_context = "\n---\n".join([f"URL: {res.get('url', 'N/A')}\nTitle: {res.get('title', '')}\nSnippet: {res.get('content', '')}" for res in glassdoor_results])

    prompt=ChatPromptTemplate.from_template(
        """You are a sharp, unbiased business intelligence analyst. Your task is to create a concise, full-spectrum report for the company '{company_name}' based on the provided search snippets.

        Use the following context to generate the report. Structure your response in markdown with three distinct sections: 'Company Standing & Public Perception', 'Glassdoor Employee Sentiment', and 'Potential Open Vacancies'.

        **Instructions:**
        1.  **Company Standing & Public Perception:**
            -   Analyze the news context to identify both positive developments and potential challenges.
            -   Create two sub-sections: 'Positive Developments' and 'Potential Challenges'.
            -   For each point you make, you **MUST** cite the source URL in parentheses. Example: A new product was launched (Source: https://...).
            -   In total, provide {summary_instruction} for this entire section.

        2.  **Glassdoor Employee Sentiment:**
            -   Analyze the Glassdoor context. Summarize the key themes from employee reviews, mentioning specific pros and cons if found.
            -   If an overall rating or CEO approval rating is mentioned in the snippets, include it.
            -   If no specific sentiment data is found, state that.

        3.  **Potential Open Vacancies:**
            -   Analyze the job context to identify specific, open job titles.
            -   List the job titles you find and their corresponding source URLs.
            -   If no jobs are found, state that.

        4.  Ensure the final output is clean, well-formatted, and professional.

        ---
        **News Context (includes URLs):**
        {news_context}
        ---
        **Glassdoor Context (includes URLs):**
        {glassdoor_context}
        ---
        **Job Context (includes URLs):**
        {jobs_context}
        ---"""
    )

    chain=prompt|llm
    final_report = chain.invoke({
        "company_name": company_name,
        "news_context": news_context or "No news context found.",
        "jobs_context": jobs_context or "No job context found.",
        "glassdoor_context": glassdoor_context or "No Glassdoor context found.",
        "summary_instruction": summary_instruction
    }).content
   

    return {"final_report":final_report}


company_graph_builder=StateGraph(CompanyAgentState)
company_graph_builder.add_node("company_searcher",company_search_node)
company_graph_builder.add_node("company_reporter",company_report_node)

company_graph_builder.add_edge(START, "company_searcher")
company_graph_builder.add_edge("company_searcher", "company_reporter")
company_graph_builder.add_edge("company_reporter", END)

company_research_app=company_graph_builder.compile()




#--- 6. STREAMLIT UI ---
st.set_page_config(page_title="AI Talent Scout", layout="wide")
st.title("🤖 AI Talent Scout")
st.write("A unified tool for talent scouting and company intelligence.")
# Use tabs to cleanly separate the two functionalities
tab1, tab2 = st.tabs(["Talent Scout", "Company Research"])

# --- Talent Scout Tab (Original Functionality) ---
with tab1:
    st.header("Find Potential Candidates on LinkedIn")
    with st.form("job_criteria_form"):
        st.subheader("Enter Job Criteria")
        role = st.text_input("Role / Title", "Machine Learning Engineer")
        skills = st.text_input("Key Skills (comma-separated)", "PyTorch, LangChain")
        location = st.text_input("Location", "Gurugram, India")
        domain = st.text_input("Domain / Industry", "AI")
        
        submit_talent_button = st.form_submit_button(label="Scout for Talent")

    if submit_talent_button:
        job_criteria = {"role": role, "skills": skills, "location": location, "domain": domain}
        st.write("---")
        st.subheader("Talent Scout Agent is running...")
        
        with st.spinner("Agent is planning and searching for profiles... This may take a moment."):
            initial_state = {"job_criteria": job_criteria}
            # Invokes the original graph
            final_state = app_graph.invoke(initial_state)
            
            st.subheader("Scouting Report Complete")
            st.markdown(final_state['final_report'])

# --- Company Research Tab (New Functionality) ---
with tab2:
    st.header("Research a Company")
    with st.form("company_research_form"):
        st.subheader("Enter Company Name")
        company_name = st.text_input("Company Name", "OpenAI")
        
        submit_company_button = st.form_submit_button(label="Generate Company Report")
        
    if submit_company_button and company_name:
        st.write("---")
        st.subheader("Company Research Agent is running...")

        with st.spinner(f"Agent is gathering news and job data for {company_name}..."):
            initial_state = {"company_name": company_name}
            # Invokes the new company research agent
            final_state = company_research_app.invoke(initial_state)
            
            st.subheader(f"Intelligence Report: {company_name}")
            st.markdown(final_state['final_report'])
    elif submit_company_button:
        st.error("Please enter a company name.")