# Autonomous Research Agent

A comprehensive AI-powered research agent built with Streamlit and CloudGROQ that conducts autonomous research with proper citations and quality assurance.

## Features

### Core Capabilities
- **Autonomous Research**: Breaks down research goals into actionable subtasks
- **Multi-Source Retrieval**: Web search and academic paper retrieval (arXiv)
- **Citation Management**: Supports APA, MLA, and Chicago citation styles
- **Quality Assurance**: Self-critique and validation at each research phase
- **Memory Management**: Vector-based storage for efficient information retrieval
- **Report Generation**: Comprehensive Markdown reports with proper citations

### Technical Architecture
- **Modular Design**: Separate modules for parsing, planning, retrieval, and analysis
- **Rate Limit Management**: Intelligent handling of API rate limits with backoff
- **Batch Processing**: Process sources in batches to manage API constraints
- **Error Recovery**: Robust error handling and fallback mechanisms

## Quick Start

### Prerequisites
- Python 3.11+
- CloudGROQ API key ([Get one here](https://console.groq.com/))

### Installation
The application uses UV for package management. Required dependencies:
- streamlit
- groq
- duckduckgo-search
- arxiv
- chromadb
- requests
- trafilatura

### Running the Application
```bash
streamlit run app.py --server.port 5000
```

### Configuration
1. Enter your CloudGROQ API key in the sidebar
2. Configure research parameters:
   - Max sources per query (1-10)
   - Search depth (shallow/medium/deep)
   - Citation style (APA/MLA/Chicago)
3. Enable "Optimize for Free Tier" for rate limit management

## Usage

### Basic Research
1. Enter a focused research goal (e.g., "Impact of AI on healthcare diagnostics in 2023-2024")
2. Click "Start Research"
3. Monitor progress in real-time
4. Download the generated report in Markdown or JSON format

### Optimization Tips
- **Free Tier Users**: Enable "Optimize for Free Tier" to reduce API usage
- **Token Management**: Keep research goals focused and specific
- **Model Selection**: Use llama3-8b-8192 for faster, cheaper responses
- **Batch Processing**: Enable for better rate limit handling

## API Rate Limits

### CloudGROQ Free Tier Limits
- 6,000 tokens per minute for llama3-70b-8192
- Lower limits for other models
- Rate limit resets every minute

### Built-in Optimizations
- Automatic retry with exponential backoff
- Intelligent token usage estimation
- Batch processing with delays
- Reduced response lengths for free tier

## Example Research Goals

### Good Examples (Focused)
- "AI applications in medical imaging 2023-2024"
- "Remote work productivity trends post-COVID"
- "Electric vehicle adoption barriers in Europe"

### Avoid (Too Broad)
- "Everything about artificial intelligence"
- "History of technology"
- "Climate change effects globally"

## Troubleshooting

### Rate Limit Errors
- Enable "Optimize for Free Tier"
- Use smaller models (llama3-8b-8192)
- Wait for rate limits to reset (usually 1 minute)
- Reduce max sources to 2-3

### No Results Found
- Check internet connection
- Try broader search terms
- Verify CloudGROQ API key is valid
- Ensure search sources are accessible

### Performance Issues
- Enable batch processing
- Use shallow search depth
- Reduce max tokens in advanced settings
- Choose faster models

## Architecture

### Module Structure
```
modules/
├── goal_parser.py          # Research goal decomposition
├── planner.py              # Execution planning
├── retriever.py            # Information retrieval
├── memory_manager.py       # Vector storage
├── llm_tools.py            # CloudGROQ interface
├── citation_engine.py      # Citation management
├── execution_agent.py      # Main orchestrator
├── self_critique.py        # Quality assurance
├── report_compiler.py      # Report generation
├── rate_limiter.py         # Rate limit handling
├── batch_processor.py      # Batch processing
└── config_optimizer.py     # Configuration optimization
```

### Data Flow
1. **Goal Parsing**: Break down research objective
2. **Planning**: Create execution phases
3. **Retrieval**: Gather information from sources
4. **Memory**: Store and index findings
5. **Analysis**: Extract key information
6. **Synthesis**: Combine findings across phases
7. **Quality Check**: Validate research quality
8. **Report**: Generate final document

## Contributing

This is a modular system designed for easy extension:
- Add new retrieval sources in `retriever.py`
- Implement new citation styles in `citation_engine.py`
- Extend quality criteria in `self_critique.py`
- Add new export formats in `report_compiler.py`

## License

Open source - feel free to adapt and extend for your research needs.