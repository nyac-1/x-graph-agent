# Quick Start Guide

## Get Started in 2 Minutes

### 1. Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd x-graph-agent

# Add your API key
echo "GEMINI_API_KEY=your-actual-api-key-here" > .env
```

### 2. Run the System
```bash
# Use the run script (handles venv and dependencies automatically)
./run.sh

# Or run with a query
./run.sh -q "What is 25 * 47?"
```

## Try These Examples

### Simple Calculations (General Q&A)
```bash
./run.sh -q "What is 25 * 47?"
./run.sh -q "Calculate compound interest on $1000 at 5% for 10 years"
```

### Web Search (General Q&A)
```bash
./run.sh -q "What's the current weather in Paris?"
./run.sh -q "Who won the latest Nobel Prize in Physics?"
```

### Research Tasks (Research Agent)
```bash
./run.sh -q "Explain quantum computing and its recent developments"
./run.sh -q "Compare transformer and LSTM architectures in NLP"
```

## Commands

- `./run.sh` - Interactive mode
- `./run.sh -q "query"` - Single query mode
- `./run.sh -v -q "query"` - Verbose mode
- `./run.sh info` - Show system information

## How It Works

1. **Supervisor** analyzes your query
2. Routes to **General Q&A** for simple tasks or **Research** for complex queries
3. Agents use their tools to find answers
4. You get a comprehensive response!

## Available Tools

- **Python REPL**: Calculations, data processing
- **Web Search**: Current information via DuckDuckGo
- **Wikipedia**: Encyclopedic knowledge
- **ArXiv**: Research papers and academic content

## Tips

- Use specific queries for better routing
- Research agent is best for multi-faceted questions
- General Q&A is fastest for simple lookups
- Add `-v` flag to see detailed execution steps

## Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_system.py
``` 