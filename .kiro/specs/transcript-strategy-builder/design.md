# Design Document: Transcript Strategy Builder

## Overview

The Transcript Strategy Builder is a prompt-based workflow system that guides traders through converting YouTube trading strategy transcripts into executable DSL strategy cartridges. The system consists of:

1. **Prompt Templates**: A series of carefully crafted prompts that guide LLMs (Claude, ChatGPT) through progressive refinement
2. **HTML Interface**: A simple web page displaying the workflow stages and prompt templates
3. **MCP Tools**: Validation and file-saving tools that integrate with the existing backtest infrastructure
4. **Workflow Documentation**: Clear instructions for using the system effectively

The design leverages LLMs for natural language processing rather than implementing custom parsing logic, making it flexible and maintainable.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    User Workflow                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Paste Transcript → HTML Interface                       │
│  2. Copy Prompt Template → LLM (Claude/ChatGPT)             │
│  3. Paste Transcript + Prompt → Get Structured Output       │
│  4. Repeat for Each Stage → Progressive Refinement          │
│  5. Final DSL JSON → Validate via MCP Tool                  │
│  6. Save via MCP Tool → Ready for Backtest                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  Technical Components                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  HTML Interface  │      │  MCP Server      │            │
│  │  - Prompt Display│      │  - Validate Tool │            │
│  │  - Copy to       │      │  - Save Tool     │            │
│  │    Clipboard     │      │  - List Tool     │            │
│  │  - Progress      │      └──────────────────┘            │
│  │    Tracking      │               │                       │
│  └──────────────────┘               │                       │
│           │                          │                       │
│           │                          ▼                       │
│           │              ┌──────────────────────┐           │
│           │              │  DSL Validator       │           │
│           │              │  (schema_validator)  │           │
│           │              └──────────────────────┘           │
│           │                          │                       │
│           │                          ▼                       │
│           │              ┌──────────────────────┐           │
│           └─────────────▶│  dsl_strategies/     │           │
│                          │  (JSON files)        │           │
│                          └──────────────────────┘           │
│                                     │                        │
│                                     ▼                        │
│                          ┌──────────────────────┐           │
│                          │  Backtest Engine     │           │
│                          │  (existing)          │           │
│                          └──────────────────────┘           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Workflow Stages

The system implements a 4-stage progressive refinement workflow:

**Stage 1: Extract Trading Logic**
- Input: Raw YouTube transcript
- Output: Structured trading logic (entry/exit conditions, indicators, timing)
- Purpose: Convert natural language to structured information

**Stage 2: Clarify Ambiguities**
- Input: Structured trading logic from Stage 1
- Output: Refined logic with ambiguities resolved
- Purpose: Ensure all strategy elements are clearly defined

**Stage 3: Generate DSL JSON**
- Input: Refined trading logic from Stage 2
- Output: Complete DSL JSON configuration
- Purpose: Convert structured logic to executable format

**Stage 4: Validate and Save**
- Input: DSL JSON from Stage 3
- Output: Validated and saved strategy cartridge
- Purpose: Ensure correctness and integrate with backtest system

## Components and Interfaces

### 1. Prompt Templates

Each prompt template is a carefully crafted instruction that guides the LLM through a specific refinement step.

#### Stage 1 Prompt Template

```
You are a trading strategy extraction expert. Your task is to analyze a YouTube transcript 
and extract the core trading logic.

TRANSCRIPT:
[User pastes transcript here]

INSTRUCTIONS:
1. Ignore timestamps, speaker labels, and filler words
2. Focus on identifying:
   - Entry conditions (when to BUY)
   - Exit conditions (when to SELL)
   - Indicators mentioned (SMA, EMA, RSI, VWAP, etc.)
   - Timing information (specific times, reference points)
   - Risk management (stop loss, take profit)

3. Output your findings in this structured format:

STRATEGY NAME: [Descriptive name]

ENTRY CONDITIONS:
- [Condition 1]
- [Condition 2]

EXIT CONDITIONS:
- [Condition 1]
- [Condition 2]

INDICATORS:
- [Indicator 1: type, period, purpose]
- [Indicator 2: type, period, purpose]

TIMING:
- Reference Time: [HH:MM or "N/A"]
- Reference Price: [open/high/low/close or "N/A"]
- Signal Time: [HH:MM or "N/A"]

RISK MANAGEMENT:
- Stop Loss: [X pips or "not specified"]
- Take Profit: [X pips or "not specified"]

AMBIGUITIES:
- [List any unclear or missing information]
```

#### Stage 2 Prompt Template

```
You are a trading strategy refinement expert. Your task is to clarify ambiguities 
and ensure all strategy elements are well-defined.

EXTRACTED STRATEGY:
[User pastes output from Stage 1]

INSTRUCTIONS:
1. Review the extracted strategy for:
   - Missing required information
   - Ambiguous conditions
   - Unclear indicator specifications
   - Incomplete timing information

2. For each ambiguity, generate a specific clarifying question with options

3. Output in this format:

CLARIFYING QUESTIONS:

Q1: [Specific question about ambiguity 1]
   Option A: [Interpretation 1]
   Option B: [Interpretation 2]
   Option C: [Interpretation 3]

Q2: [Specific question about ambiguity 2]
   Option A: [Interpretation 1]
   Option B: [Interpretation 2]

[Continue for all ambiguities]

REQUIRED INFORMATION:
- [List any missing required fields]

After the user provides answers, incorporate them and output:

REFINED STRATEGY:
[Complete strategy with all ambiguities resolved]
```

#### Stage 3 Prompt Template

```
You are a DSL JSON generation expert. Your task is to convert refined trading logic 
into a valid DSL JSON configuration.

REFINED STRATEGY:
[User pastes refined strategy from Stage 2]

DSL SCHEMA:
The DSL supports two types of strategies:

TYPE 1: TIME-BASED STRATEGIES
Required fields:
- name: string (strategy name)
- version: string (semantic version, e.g., "1.0.0")
- description: string (detailed description)
- timing: object
  - reference_time: string (HH:MM format)
  - reference_price: string ("open", "high", "low", or "close")
  - signal_time: string (HH:MM format, must be after reference_time)
- conditions: object
  - buy: object
    - compare: string (comparison using signal_price and reference_price)
  - sell: object
    - compare: string (comparison using signal_price and reference_price)
- risk_management: object
  - stop_loss_pips: number (1-1000)
  - take_profit_pips: number (1-1000)
  - max_daily_trades: integer (1-10, optional, default: 1)
  - min_pip_distance: number (optional, default: 0.0001)

TYPE 2: INDICATOR-BASED STRATEGIES
Required fields:
- name: string (strategy name)
- version: string (semantic version)
- description: string (detailed description)
- indicators: array of objects
  - type: string ("SMA", "EMA", or "RSI")
  - period: integer (1-200)
  - alias: string (unique identifier for this indicator)
- conditions: object
  - buy: object
    - compare: string (comparison using indicator aliases)
    - crossover: boolean (optional, true if crossover required)
  - sell: object
    - compare: string (comparison using indicator aliases)
    - crossover: boolean (optional, true if crossover required)
- risk_management: object (same as time-based)

EXAMPLE TIME-BASED STRATEGY:
{
  "name": "10am vs 9:30am Price Compare",
  "version": "1.0.0",
  "description": "Buy if 10am price > 9:30am close, Sell if lower",
  "timing": {
    "reference_time": "09:30",
    "reference_price": "close",
    "signal_time": "10:00"
  },
  "conditions": {
    "buy": {"compare": "signal_price > reference_price"},
    "sell": {"compare": "signal_price < reference_price"}
  },
  "risk_management": {
    "stop_loss_pips": 15,
    "take_profit_pips": 25,
    "max_daily_trades": 1
  }
}

EXAMPLE INDICATOR-BASED STRATEGY:
{
  "name": "MA Crossover Strategy",
  "version": "1.0.0",
  "description": "Moving Average Crossover using SMA 20 and SMA 50",
  "indicators": [
    {"type": "SMA", "period": 20, "alias": "fast_ma"},
    {"type": "SMA", "period": 50, "alias": "slow_ma"}
  ],
  "conditions": {
    "buy": {"compare": "fast_ma > slow_ma", "crossover": true},
    "sell": {"compare": "fast_ma < slow_ma", "crossover": true}
  },
  "risk_management": {
    "stop_loss_pips": 20,
    "take_profit_pips": 30,
    "max_daily_trades": 3
  }
}

INSTRUCTIONS:
1. Determine if this is a time-based or indicator-based strategy
2. Generate valid DSL JSON following the appropriate schema
3. Ensure all required fields are present
4. Use appropriate comparison operators: >, <, >=, <=, ==, !=
5. Output ONLY the JSON, no additional text

OUTPUT:
[Valid DSL JSON only]
```

### 2. HTML Interface

A simple, single-page HTML interface that displays the workflow and prompt templates.

**Features:**
- Display all 4 workflow stages
- Show prompt template for each stage
- One-click copy to clipboard
- Progress tracking (mark stages as complete)
- Instructions for each stage
- Links to MCP tools for validation and saving

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Transcript Strategy Builder                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Progress: [✓] Stage 1  [✓] Stage 2  [ ] Stage 3  [ ]  │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ Stage 1: Extract Trading Logic                 │    │
│  │                                                 │    │
│  │ Instructions:                                   │    │
│  │ 1. Copy the prompt template below              │    │
│  │ 2. Paste it into Claude or ChatGPT             │    │
│  │ 3. Paste your transcript where indicated       │    │
│  │ 4. Copy the LLM's output for Stage 2           │    │
│  │                                                 │    │
│  │ [Copy Prompt] [Mark Complete]                  │    │
│  │                                                 │    │
│  │ ┌─────────────────────────────────────────┐   │    │
│  │ │ Prompt Template:                        │   │    │
│  │ │ [Full prompt text displayed here]       │   │    │
│  │ └─────────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  [Similar sections for Stages 2, 3, 4]                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 3. MCP Server Tools

The MCP server provides three tools for validation, saving, and listing strategies.

#### Tool 1: validate_dsl_strategy

**Purpose:** Validate DSL JSON against the schema

**Input:**
```python
{
  "dsl_json": str  # The DSL JSON as a string
}
```

**Output:**
```python
{
  "valid": bool,
  "errors": List[str],  # Empty if valid
  "strategy_type": str,  # "time-based" or "indicator-based"
  "strategy_name": str
}
```

**Implementation:** Uses existing `schema_validator.py`

#### Tool 2: save_dsl_strategy

**Purpose:** Save validated DSL JSON to the dsl_strategies directory

**Input:**
```python
{
  "dsl_json": str,  # The DSL JSON as a string
  "filename": str   # Optional, auto-generated from strategy name if not provided
}
```

**Output:**
```python
{
  "success": bool,
  "file_path": str,  # Full path to saved file
  "message": str
}
```

**Implementation:** 
1. Validate the JSON first
2. Generate filename from strategy name if not provided
3. Save to `shared/strategies/dsl_strategies/`
4. Return full path

#### Tool 3: list_dsl_strategies

**Purpose:** List all available DSL strategy cartridges

**Input:** None

**Output:**
```python
{
  "strategies": List[Dict],  # List of strategy info
  "count": int
}
```

Each strategy dict contains:
```python
{
  "name": str,
  "filename": str,
  "type": str,  # "time-based" or "indicator-based"
  "version": str,
  "description": str
}
```

## Data Models

### Prompt Template Model

```python
@dataclass
class PromptTemplate:
    stage: int
    name: str
    description: str
    instructions: str
    template_text: str
    expected_input: str
    expected_output: str
```

### Workflow Stage Model

```python
@dataclass
class WorkflowStage:
    stage_number: int
    name: str
    description: str
    prompt_template: PromptTemplate
    completed: bool = False
```

### DSL Strategy Model

The DSL strategy model is already defined in the existing codebase. It supports two types:

**Time-Based Strategy:**
```python
{
  "name": str,
  "version": str,
  "description": str,
  "timing": {
    "reference_time": str,
    "reference_price": str,
    "signal_time": str
  },
  "conditions": {
    "buy": {"compare": str},
    "sell": {"compare": str}
  },
  "risk_management": {
    "stop_loss_pips": float,
    "take_profit_pips": float,
    "max_daily_trades": int,
    "min_pip_distance": float
  }
}
```

**Indicator-Based Strategy:**
```python
{
  "name": str,
  "version": str,
  "description": str,
  "indicators": [
    {
      "type": str,
      "period": int,
      "alias": str
    }
  ],
  "conditions": {
    "buy": {
      "compare": str,
      "crossover": bool
    },
    "sell": {
      "compare": str,
      "crossover": bool
    }
  },
  "risk_management": {
    "stop_loss_pips": float,
    "take_profit_pips": float,
    "max_daily_trades": int,
    "min_pip_distance": float
  }
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Prompt template completeness
*For any* prompt template in the system, the template SHALL contain all required instruction elements for its stage (entry/exit conditions, indicators, timing, output format, ambiguity handling, schema specification, or transcript variation handling as appropriate)
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 8.1, 8.2, 8.3, 8.4, 8.5**

### Property 2: Validation detects missing required fields
*For any* DSL JSON with missing required fields, the validation tool SHALL identify and report all missing fields
**Validates: Requirements 4.2**

### Property 3: Validation detects invalid condition syntax
*For any* DSL JSON with invalid condition syntax, the validation tool SHALL identify and report the syntax errors
**Validates: Requirements 4.3**

### Property 4: Validation error messages are specific
*For any* invalid DSL JSON, the validation tool SHALL return error messages that identify the specific problem (not generic errors)
**Validates: Requirements 4.4**

### Property 5: Validation confirms valid strategies
*For any* valid DSL JSON, the validation tool SHALL return a success confirmation indicating the cartridge is ready for use
**Validates: Requirements 4.5**

### Property 6: Stage template display completeness
*For any* workflow stage, the HTML interface SHALL display the complete prompt template for that stage
**Validates: Requirements 5.2**

### Property 7: Stage completion tracking
*For any* workflow stage, when marked as complete, the HTML interface SHALL persist and display that completion state
**Validates: Requirements 5.4**

### Property 8: Save tool writes to correct directory
*For any* valid DSL JSON, the save tool SHALL write the file to the dsl_strategies directory
**Validates: Requirements 6.1**

### Property 9: Filename generation from strategy name
*For any* strategy name, the save tool SHALL generate a valid filename based on that name (sanitized, with .json extension)
**Validates: Requirements 6.2**

### Property 10: Save tool returns complete file path
*For any* saved cartridge, the save tool SHALL return the full absolute file path to the saved file
**Validates: Requirements 6.3**

### Property 11: Save-then-load round trip
*For any* valid DSL JSON, after saving via the save tool, the backtest engine SHALL be able to discover and load the cartridge, and the list tool SHALL include it in the strategies list
**Validates: Requirements 6.4, 6.5**

### Property 12: Tool input validation
*For any* MCP tool invocation with invalid parameters, the MCP server SHALL reject the request and return a validation error
**Validates: Requirements 7.2**

### Property 13: Error messages are descriptive
*For any* processing failure in the MCP server, the error message SHALL describe the specific failure (not generic errors)
**Validates: Requirements 7.3**

### Property 14: Independent request handling
*For any* sequence of multiple MCP tool requests, each request SHALL be handled independently without state interference from other requests
**Validates: Requirements 7.5**

### Property 15: Stage documentation completeness
*For any* workflow stage in the documentation, the documentation SHALL include the stage purpose, usage instructions, and expected inputs/outputs
**Validates: Requirements 9.2, 9.3, 9.4**

## Error Handling

### Validation Errors

**Invalid JSON Structure:**
- Error: "Invalid JSON: [specific parsing error]"
- Action: Return error to user with specific location of JSON syntax error
- Recovery: User fixes JSON and re-validates

**Missing Required Fields:**
- Error: "Missing required field: [field_name]"
- Action: Return list of all missing required fields
- Recovery: User adds missing fields and re-validates

**Invalid Field Values:**
- Error: "Invalid value for [field_name]: [specific issue]"
- Action: Return specific validation error with expected format
- Recovery: User corrects field value and re-validates

**Schema Mismatch:**
- Error: "Strategy type mismatch: has both 'timing' and 'indicators' fields"
- Action: Return error explaining the conflict
- Recovery: User removes inappropriate fields and re-validates

### File System Errors

**Save Failures:**
- Error: "Failed to save strategy: [specific file system error]"
- Action: Return error with file path and permission details
- Recovery: User checks permissions and retries

**Directory Not Found:**
- Error: "DSL strategies directory not found: [path]"
- Action: Create directory if possible, otherwise return error
- Recovery: User creates directory or fixes path configuration

**File Already Exists:**
- Error: "Strategy file already exists: [filename]"
- Action: Prompt user to confirm overwrite or provide new filename
- Recovery: User chooses to overwrite or provides new name

### MCP Server Errors

**Tool Not Found:**
- Error: "Tool [tool_name] not registered"
- Action: Return list of available tools
- Recovery: User checks MCP server configuration

**Invalid Parameters:**
- Error: "Invalid parameter [param_name]: [specific issue]"
- Action: Return parameter requirements and examples
- Recovery: User corrects parameters and retries

**Server Unavailable:**
- Error: "MCP server not responding"
- Action: Return connection error details
- Recovery: User restarts MCP server or checks configuration

## Testing Strategy

### Unit Testing

The system will use Python's `unittest` framework for unit testing. Tests will focus on:

**Prompt Template Tests:**
- Test that each prompt template contains required instruction keywords
- Test that templates are properly formatted and readable
- Test that example outputs in templates are valid

**Validation Tool Tests:**
- Test validation with valid time-based strategies
- Test validation with valid indicator-based strategies
- Test validation with various invalid inputs (missing fields, wrong types, invalid values)
- Test error message specificity

**Save Tool Tests:**
- Test filename generation from various strategy names
- Test file writing to correct directory
- Test path return values
- Test overwrite behavior

**List Tool Tests:**
- Test listing empty directory
- Test listing directory with multiple strategies
- Test strategy info extraction

### Property-Based Testing

The system will use `hypothesis` for property-based testing in Python. Each correctness property will be implemented as a property-based test.

**Configuration:**
- Minimum 100 iterations per property test
- Use hypothesis strategies to generate random but valid test data
- Tag each test with the property number and requirement it validates

**Test Generators:**

```python
# Generator for valid DSL JSON (both types)
@st.composite
def valid_dsl_strategy(draw):
    strategy_type = draw(st.sampled_from(["time-based", "indicator-based"]))
    if strategy_type == "time-based":
        return generate_time_based_strategy(draw)
    else:
        return generate_indicator_based_strategy(draw)

# Generator for invalid DSL JSON (missing fields)
@st.composite
def invalid_dsl_missing_fields(draw):
    strategy = draw(valid_dsl_strategy())
    required_fields = ["name", "version", "description", "conditions", "risk_management"]
    field_to_remove = draw(st.sampled_from(required_fields))
    del strategy[field_to_remove]
    return strategy, field_to_remove

# Generator for strategy names
@st.composite
def strategy_name(draw):
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
        min_size=5,
        max_size=50
    ))
```

**Property Test Examples:**

```python
@given(valid_dsl_strategy())
def test_property_5_validation_confirms_valid_strategies(strategy):
    """
    Feature: transcript-strategy-builder, Property 5: Validation confirms valid strategies
    Validates: Requirements 4.5
    """
    result = validate_dsl_strategy(strategy)
    assert result["valid"] == True
    assert "ready" in result["message"].lower() or "valid" in result["message"].lower()

@given(invalid_dsl_missing_fields())
def test_property_2_validation_detects_missing_fields(strategy_and_missing):
    """
    Feature: transcript-strategy-builder, Property 2: Validation detects missing required fields
    Validates: Requirements 4.2
    """
    strategy, missing_field = strategy_and_missing
    result = validate_dsl_strategy(strategy)
    assert result["valid"] == False
    assert missing_field in str(result["errors"])

@given(strategy_name())
def test_property_9_filename_generation(name):
    """
    Feature: transcript-strategy-builder, Property 9: Filename generation from strategy name
    Validates: Requirements 6.2
    """
    filename = generate_filename(name)
    assert filename.endswith(".json")
    assert len(filename) > 5  # At least some content + .json
    # Verify no invalid filename characters
    assert not any(c in filename for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|'])
```

### Integration Testing

**End-to-End Workflow Test:**
1. Load HTML interface
2. Verify all stages are displayed
3. Copy prompt template
4. Simulate LLM interaction (use pre-generated outputs)
5. Validate generated DSL JSON
6. Save strategy cartridge
7. Verify file exists in correct location
8. List strategies and verify new cartridge appears
9. Load strategy in backtest engine
10. Run backtest to verify strategy executes

**MCP Server Integration Test:**
1. Start MCP server
2. Verify tools are registered
3. Call validation tool with valid and invalid inputs
4. Call save tool and verify file creation
5. Call list tool and verify results
6. Verify error handling for invalid requests

### Manual Testing

**Prompt Template Quality:**
- Test prompts with real LLMs (Claude, ChatGPT)
- Verify LLM outputs match expected format
- Test with various transcript styles
- Verify ambiguity detection works
- Verify DSL generation is accurate

**HTML Interface Usability:**
- Test clipboard copy functionality
- Test progress tracking
- Test on different browsers
- Verify responsive design
- Test accessibility features

**Real Transcript Testing:**
- Test with 5-10 real YouTube trading strategy transcripts
- Verify complete workflow from transcript to backtest
- Document any issues or edge cases
- Refine prompts based on results

## Implementation Notes

### Prompt Template Storage

Prompt templates will be stored as Python string constants in a dedicated module:

```python
# prompt_templates.py

STAGE_1_EXTRACT_LOGIC = """
You are a trading strategy extraction expert...
[Full template text]
"""

STAGE_2_CLARIFY_AMBIGUITIES = """
You are a trading strategy refinement expert...
[Full template text]
"""

STAGE_3_GENERATE_DSL = """
You are a DSL JSON generation expert...
[Full template text]
"""
```

### HTML Interface Implementation

The HTML interface will be a single static HTML file with embedded CSS and JavaScript:
- No server-side processing required
- Can be opened directly in a browser
- Uses localStorage for progress tracking
- Clipboard API for copy functionality

### MCP Server Structure

```
mcp_servers/
  strategy_builder/
    __init__.py
    server.py          # MCP server implementation
    validators.py      # Validation logic (uses existing schema_validator)
    file_operations.py # Save and list operations
    prompt_templates.py # Prompt template constants
```

### Integration with Existing Code

The strategy builder integrates with existing components:
- Uses `shared/strategies/dsl_interpreter/schema_validator.py` for validation
- Saves to `shared/strategies/dsl_strategies/` directory
- Generated strategies work with existing `universal_backtest_engine.py`
- No modifications to existing code required

### Configuration

MCP server configuration in `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "strategy-builder": {
      "command": "python",
      "args": ["-m", "mcp_servers.strategy_builder.server"],
      "env": {},
      "disabled": false,
      "autoApprove": ["list_dsl_strategies"]
    }
  }
}
```
