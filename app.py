import streamlit as st
import os
from datetime import datetime
import json
from modules.goal_parser import GoalParser
from modules.execution_agent import ExecutionAgent
from modules.report_compiler import ReportCompiler
from database.operations import DatabaseOperations
from utils.config import Config
from utils.logger import setup_logger

# Configure page
st.set_page_config(
    page_title="Autonomous Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize logger
logger = setup_logger()

def initialize_session_state():
    """Initialize session state variables"""
    if 'research_started' not in st.session_state:
        st.session_state.research_started = False
    if 'research_completed' not in st.session_state:
        st.session_state.research_completed = False
    if 'research_progress' not in st.session_state:
        st.session_state.research_progress = []
    if 'final_report' not in st.session_state:
        st.session_state.final_report = None
    if 'research_goal' not in st.session_state:
        st.session_state.research_goal = ""
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    if 'show_history' not in st.session_state:
        st.session_state.show_history = False
    if 'show_analytics' not in st.session_state:
        st.session_state.show_analytics = False

def main():
    """Main application function"""
    initialize_session_state()
    
    # Title and description
    st.title("🔬 Autonomous Research Agent")
    st.markdown("**Powered by CloudGROQ** | Conduct comprehensive research with AI-driven analysis and citation")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        groq_api_key = st.text_input(
            "CloudGROQ API Key",
            type="password",
            value=os.getenv("GROQ_API_KEY", ""),
            help="Enter your CloudGROQ API key"
        )
        
        if groq_api_key:
            os.environ["GROQ_API_KEY"] = groq_api_key
        
        st.divider()
        
        # Research parameters
        st.subheader("Research Parameters")
        max_sources = st.slider("Max Sources per Query", 1, 10, 5)
        search_depth = st.selectbox("Search Depth", ["shallow", "medium", "deep"], index=0)
        citation_style = st.selectbox("Citation Style", ["APA", "MLA", "Chicago"], index=0)
        
        # Rate limit optimization
        st.subheader("Performance Settings")
        optimize_for_free_tier = st.checkbox("Optimize for Free Tier", value=True, 
                                           help="Reduces API calls and token usage")
        
        if optimize_for_free_tier:
            st.info("✅ Free tier optimizations enabled: Reduced sources, shorter responses, longer delays")
            max_sources = min(max_sources, 3)
            search_depth = "shallow"
        
        # Advanced settings in expander
        with st.expander("Advanced Settings"):
            model_choice = st.selectbox("Model", 
                                      ["llama3-8b-8192", "mixtral-8x7b-32768", "llama3-70b-8192"], 
                                      index=0 if optimize_for_free_tier else 0,  # Always default to fastest
                                      help="Smaller models use fewer tokens and are much faster")
            batch_processing = st.checkbox("Enable Batch Processing", value=True,
                                         help="Process sources in smaller batches with delays")
            aggressive_optimization = st.checkbox("Aggressive Optimization", value=True,
                                                help="Use caching, fallbacks, and reduced API calls")
        
        st.divider()
        
        # Database section
        st.subheader("📊 Research History")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("View History"):
                st.session_state.show_history = True
                st.session_state.show_analytics = False
        with col2:
            if st.button("Analytics"):
                st.session_state.show_analytics = True
                st.session_state.show_history = False
        
        # Progress section
        if st.session_state.research_started:
            st.subheader("🔄 Current Research")
            if st.session_state.research_progress:
                for i, step in enumerate(st.session_state.research_progress):
                    status_icon = "✅" if step.get('completed', False) else "🔄"
                    st.write(f"{status_icon} {step.get('description', 'Processing...')}")
    
    # Database views
    if st.session_state.show_history:
        show_research_history()
        return
    elif st.session_state.show_analytics:
        show_analytics_dashboard()
        return
    
    # Main content area
    if not st.session_state.research_completed:
        # Research input section
        st.header("🎯 Research Goal")
        
        research_goal = st.text_area(
            "Enter your research objective:",
            height=150,
            placeholder="Example: Impact of AI on healthcare diagnostics in 2023-2024",
            value=st.session_state.research_goal,
            help="Tip: Keep goals focused and specific for better results with API limits"
        )
        
        # Show token estimate
        if research_goal:
            from modules.config_optimizer import ConfigOptimizer
            optimizer = ConfigOptimizer(Config(groq_api_key="dummy"))
            estimate = optimizer.estimate_token_usage(research_goal)
            st.info(f"📊 Estimated token usage: ~{estimate['estimated_total_tokens']} tokens from {estimate['estimated_sources']} sources")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            start_research = st.button(
                "🚀 Start Research",
                type="primary",
                disabled=not research_goal or not groq_api_key
            )
        
        with col2:
            if st.session_state.research_started:
                stop_research = st.button("⏹️ Stop Research", type="secondary")
                if stop_research:
                    st.session_state.research_started = False
                    st.session_state.research_progress = []
                    st.rerun()
        
        # Start research process
        if start_research:
            if not groq_api_key:
                st.error("Please provide your CloudGROQ API key in the sidebar.")
                return
            
            st.session_state.research_goal = research_goal
            st.session_state.research_started = True
            st.session_state.research_progress = []
            
            # Initialize configuration with optimizations
            config = Config(
                groq_api_key=groq_api_key,
                max_sources=max_sources,
                search_depth=search_depth,
                citation_style=citation_style,
                max_tokens_default=300 if optimize_for_free_tier else 600,  # Further reduced
                temperature_default=0.3,
                retry_delay=5.0 if optimize_for_free_tier else 2.0,  # Longer delays
                max_retries=1 if optimize_for_free_tier else 2,  # Fewer retries
                default_model=model_choice
            )
            
            # Progress container
            progress_container = st.container()
            
            with progress_container:
                st.subheader("🔍 Research in Progress")
                progress_bar = st.progress(0)
                status_text = st.empty()
                logs_container = st.container()
                
                try:
                    # Initialize components
                    goal_parser = GoalParser(config)
                    execution_agent = ExecutionAgent(config)
                    report_compiler = ReportCompiler(config)
                    
                    # Step 1: Parse goal
                    status_text.text("Parsing research goal...")
                    progress_bar.progress(10)
                    
                    parsed_goals = goal_parser.parse_goal(research_goal)
                    
                    with logs_container:
                        st.info(f"✅ Identified {len(parsed_goals.get('subgoals', []))} research subtasks")
                    
                    # Step 2: Execute research with better progress tracking
                    status_text.text("Conducting research...")
                    progress_bar.progress(20)
                    
                    if optimize_for_free_tier:
                        st.info("Free tier mode: Using fastest model, aggressive caching, and fallback processing")
                        st.warning("If rate limits are hit, the system will switch to emergency mode with basic text processing")
                    
                    research_results = execution_agent.execute_research(parsed_goals)
                    
                    # Update progress through research steps
                    total_steps = len(research_results.get('steps', []))
                    for i, step in enumerate(research_results.get('steps', [])):
                        progress = 20 + (60 * (i + 1) / total_steps)
                        progress_bar.progress(int(progress))
                        status_text.text(f"Researching: {step.get('description', 'Processing...')}")
                        
                        with logs_container:
                            st.success(f"✅ {step.get('description', 'Step completed')}")
                    
                    # Step 3: Compile report
                    status_text.text("Compiling final report...")
                    progress_bar.progress(90)
                    
                    final_report = report_compiler.compile_report(research_results)
                    
                    # Complete
                    progress_bar.progress(100)
                    status_text.text("Research completed successfully!")
                    
                    st.session_state.final_report = final_report
                    st.session_state.current_session_id = research_results.get('session_id')
                    st.session_state.research_completed = True
                    st.session_state.research_started = False
                    
                    st.success("🎉 Research completed! View your report below.")
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"Research failed: {str(e)}")
                    st.error(f"Research failed: {str(e)}")
                    st.session_state.research_started = False
    
    else:
        # Display final report
        st.header("📋 Research Report")
        
        if st.session_state.final_report:
            report = st.session_state.final_report
            
            # Report metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Sources Found", report.get('source_count', 0))
            with col2:
                st.metric("Citations", report.get('citation_count', 0))
            with col3:
                st.metric("Research Duration", report.get('duration', 'N/A'))
            
            st.divider()
            
            # Report content
            st.markdown(report.get('content', ''))
            
            # Export options
            st.subheader("📤 Export Options")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.download_button(
                    "Download as Markdown",
                    data=report.get('content', ''),
                    file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
            
            with col2:
                # Convert to JSON for structured export
                json_data = json.dumps(report, indent=2)
                st.download_button(
                    "Download as JSON",
                    data=json_data,
                    file_name=f"research_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            with col3:
                if st.button("🔄 New Research"):
                    st.session_state.research_completed = False
                    st.session_state.final_report = None
                    st.session_state.research_goal = ""
                    st.session_state.current_session_id = None
                    st.rerun()

def show_research_history():
    """Display research history from database"""
    st.header("📋 Research History")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("← Back to Research"):
            st.session_state.show_history = False
            st.rerun()
    
    try:
        db_ops = DatabaseOperations()
        recent_sessions = db_ops.get_recent_sessions(limit=20)
        
        if not recent_sessions:
            st.info("No research sessions found. Start your first research above!")
            return
        
        st.write(f"Found {len(recent_sessions)} recent research sessions:")
        
        for session in recent_sessions:
            with st.expander(f"🔬 {session['research_goal'][:100]}..." if len(session['research_goal']) > 100 else f"🔬 {session['research_goal']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Status", session['status'].title())
                    st.write(f"**Created:** {session['created_at'][:19]}")
                
                with col2:
                    st.metric("Sources", session['total_sources'] or 0)
                    st.metric("Findings", session['total_findings'] or 0)
                
                with col3:
                    quality_score = session['quality_score'] or 0
                    st.metric("Quality Score", f"{quality_score:.2f}")
                    
                    if st.button(f"View Details", key=f"view_{session['session_id']}"):
                        show_session_details(session['session_id'])
        
    except Exception as e:
        st.error(f"Error loading research history: {str(e)}")

def show_session_details(session_id: str):
    """Show detailed view of a research session"""
    try:
        db_ops = DatabaseOperations()
        session_data = db_ops.get_research_session(session_id)
        
        if not session_data:
            st.error("Session not found")
            return
        
        st.subheader(f"Research Session: {session_data['research_goal']}")
        
        # Session metadata
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Status", session_data['status'].title())
        with col2:
            st.metric("Sources", session_data['total_sources'])
        with col3:
            st.metric("Citations", session_data['total_citations'])
        with col4:
            st.metric("Quality", f"{session_data['quality_score']:.2f}")
        
        # Configuration
        with st.expander("Configuration Details"):
            config = session_data['config']
            st.write(f"**Model:** {config['model_used']}")
            st.write(f"**Max Sources:** {config['max_sources']}")
            st.write(f"**Search Depth:** {config['search_depth']}")
            st.write(f"**Citation Style:** {config['citation_style']}")
        
        # Findings
        findings = db_ops.get_session_findings(session_id)
        if findings:
            st.subheader(f"Key Findings ({len(findings)})")
            for i, finding in enumerate(findings[:5], 1):
                with st.expander(f"Finding {i}: {finding['source_title'][:80]}..."):
                    st.write(f"**Source:** {finding['source_title']}")
                    st.write(f"**URL:** {finding['source_url']}")
                    st.write(f"**Relevance Score:** {finding['relevance_score']:.2f}")
                    
                    if finding['key_findings']:
                        st.write("**Key Points:**")
                        for point in finding['key_findings'][:3]:
                            st.write(f"• {point}")
        
        # Citations
        citations = db_ops.get_session_citations(session_id)
        if citations:
            st.subheader(f"Citations ({len(citations)})")
            for i, citation in enumerate(citations[:10], 1):
                st.write(f"{i}. {citation['title']} - {citation['url']}")
    
    except Exception as e:
        st.error(f"Error loading session details: {str(e)}")

def show_analytics_dashboard():
    """Show analytics dashboard"""
    st.header("📊 Research Analytics")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("← Back to Research"):
            st.session_state.show_analytics = False
            st.rerun()
    
    try:
        db_ops = DatabaseOperations()
        analytics = db_ops.get_analytics()
        
        if not analytics:
            st.info("No analytics data available yet.")
            return
        
        # Overview metrics
        st.subheader("Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sessions", analytics.get('total_sessions', 0))
        with col2:
            st.metric("Success Rate", f"{analytics.get('success_rate', 0):.1f}%")
        with col3:
            st.metric("Total Findings", analytics.get('total_findings', 0))
        with col4:
            st.metric("Total Citations", analytics.get('total_citations', 0))
        
        # Quality metrics
        st.subheader("Quality Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Avg Quality Score", analytics.get('average_quality_score', 0))
        with col2:
            st.metric("Avg Findings/Session", analytics.get('avg_findings_per_session', 0))
        with col3:
            st.metric("Avg Citations/Session", analytics.get('avg_citations_per_session', 0))
        
        # Recent activity
        st.subheader("Recent Activity")
        st.metric("Sessions (Last 7 Days)", analytics.get('recent_sessions_7d', 0))
        
        # Tips based on analytics
        st.subheader("Optimization Tips")
        success_rate = analytics.get('success_rate', 0)
        avg_quality = analytics.get('average_quality_score', 0)
        
        if success_rate < 70:
            st.warning("Consider enabling 'Optimize for Free Tier' to improve success rates")
        if avg_quality < 0.6:
            st.info("Try using more specific research goals for higher quality results")
        if analytics.get('avg_findings_per_session', 0) < 5:
            st.info("Increase max sources or use deeper search for more comprehensive results")
    
    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")

if __name__ == "__main__":
    main()
