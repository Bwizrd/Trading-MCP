# Requirements Document

## Introduction

The Transcript Strategy Builder is a prompt-based workflow system that guides users through converting YouTube trading strategy transcripts into executable DSL strategy cartridges. The system provides a series of carefully crafted prompts that users paste into LLMs (Claude, ChatGPT) to progressively refine raw transcripts into valid DSL JSON configurations.

## Glossary

- **Transcript**: Text extracted from a YouTube video describing a trading strategy
- **Strategy Cartridge**: A self-contained DSL JSON file that defines a complete trading strategy
- **DSL (Domain-Specific Language)**: A JSON-based configuration format for defining trading strategies
- **Backtest Engine**: The existing system component that validates strategies against historical data
- **Trading Logic**: The entry/exit conditions, indicators, and timing rules that define a strategy
- **Prompt Template**: A pre-written instruction that guides an LLM to perform a specific refinement step
- **Workflow Stage**: A distinct phase in the transcript-to-DSL conversion process
- **LLM**: Large Language Model such as Claude or ChatGPT used for text processing
- **Validation Tool**: An MCP tool that checks if generated DSL JSON is valid

## Requirements

### Requirement 1

**User Story:** As a trader, I want a clear prompt template for extracting trading logic from transcripts, so that I can paste it into an LLM and get structured strategy information.

#### Acceptance Criteria

1. WHEN a user accesses the first prompt template THEN the Prompt Template SHALL instruct the LLM to identify entry conditions
2. WHEN a user accesses the first prompt template THEN the Prompt Template SHALL instruct the LLM to identify exit conditions
3. WHEN a user accesses the first prompt template THEN the Prompt Template SHALL instruct the LLM to identify indicators mentioned
4. WHEN a user accesses the first prompt template THEN the Prompt Template SHALL instruct the LLM to identify timing information
5. WHEN a user accesses the first prompt template THEN the Prompt Template SHALL instruct the LLM to output structured data in a consistent format

### Requirement 2

**User Story:** As a trader, I want a prompt template that generates clarifying questions, so that I can resolve ambiguities in the extracted strategy logic.

#### Acceptance Criteria

1. WHEN a user accesses the second prompt template THEN the Prompt Template SHALL instruct the LLM to identify ambiguous elements
2. WHEN the LLM identifies ambiguities THEN the Prompt Template SHALL instruct the LLM to generate specific clarifying questions
3. WHEN multiple interpretations exist THEN the Prompt Template SHALL instruct the LLM to present options
4. WHEN required parameters are missing THEN the Prompt Template SHALL instruct the LLM to request those parameters
5. WHEN the user provides answers THEN the Prompt Template SHALL guide the LLM to incorporate answers into refined strategy information

### Requirement 3

**User Story:** As a trader, I want a prompt template that generates valid DSL JSON, so that I can create a strategy cartridge ready for backtesting.

#### Acceptance Criteria

1. WHEN a user accesses the third prompt template THEN the Prompt Template SHALL include the complete DSL schema specification
2. WHEN the LLM generates DSL JSON THEN the Prompt Template SHALL instruct the LLM to follow the schema exactly
3. WHEN the LLM generates DSL JSON THEN the Prompt Template SHALL instruct the LLM to include all required fields
4. WHEN the LLM generates DSL JSON THEN the Prompt Template SHALL provide example DSL cartridges as reference
5. WHEN the LLM outputs JSON THEN the Prompt Template SHALL instruct the LLM to output only valid JSON without additional commentary

### Requirement 4

**User Story:** As a trader, I want an MCP tool to validate my generated DSL JSON, so that I know it will work with the backtest engine before saving it.

#### Acceptance Criteria

1. WHEN a user invokes the validation tool with DSL JSON THEN the Validation Tool SHALL parse the JSON structure
2. WHEN validating THEN the Validation Tool SHALL check that all required DSL fields are present
3. WHEN validating THEN the Validation Tool SHALL verify that condition syntax is correct
4. WHEN validation fails THEN the Validation Tool SHALL return specific error messages
5. WHEN validation succeeds THEN the Validation Tool SHALL confirm the cartridge is valid and ready for use

### Requirement 5

**User Story:** As a trader, I want a simple HTML interface that displays the prompt templates, so that I can easily copy them and track my progress through the workflow.

#### Acceptance Criteria

1. WHEN the HTML interface loads THEN the HTML Interface SHALL display all workflow stages in order
2. WHEN a user views a stage THEN the HTML Interface SHALL display the complete prompt template for that stage
3. WHEN a user clicks a prompt template THEN the HTML Interface SHALL copy the template to the clipboard
4. WHEN a user completes a stage THEN the HTML Interface SHALL allow marking that stage as complete
5. WHEN a user views the final stage THEN the HTML Interface SHALL display instructions for saving and validating the DSL JSON

### Requirement 6

**User Story:** As a trader, I want an MCP tool to save validated DSL JSON to the correct location, so that it integrates seamlessly with my existing backtest workflow.

#### Acceptance Criteria

1. WHEN a user invokes the save tool with valid DSL JSON THEN the Save Tool SHALL write the file to the dsl_strategies directory
2. WHEN saving a cartridge THEN the Save Tool SHALL use a filename based on the strategy name
3. WHEN a cartridge is saved THEN the Save Tool SHALL return the full file path
4. WHEN a cartridge is saved THEN the Backtest Engine SHALL be able to discover and load it
5. WHEN the user lists available strategies THEN the Save Tool SHALL ensure the new cartridge appears in the list

### Requirement 7

**User Story:** As a developer, I want the strategy builder tools implemented as an MCP server, so that validation and saving integrate cleanly with the existing MCP architecture.

#### Acceptance Criteria

1. WHEN the MCP server starts THEN the MCP Server SHALL register the validation tool and save tool
2. WHEN a tool is invoked THEN the MCP Server SHALL validate input parameters
3. WHEN processing fails THEN the MCP Server SHALL return descriptive error messages
4. WHEN the MCP server is configured THEN the MCP Server SHALL appear in the available tools list
5. WHEN multiple requests occur THEN the MCP Server SHALL handle them independently

### Requirement 8

**User Story:** As a trader, I want the prompt templates to guide the LLM to handle common transcript variations, so that I don't need to pre-process the text before submission.

#### Acceptance Criteria

1. WHEN a transcript contains timestamps THEN the Prompt Template SHALL instruct the LLM to ignore timestamp markers
2. WHEN a transcript contains speaker labels THEN the Prompt Template SHALL instruct the LLM to focus on content
3. WHEN a transcript contains filler words THEN the Prompt Template SHALL instruct the LLM to extract meaningful trading logic
4. WHEN a transcript uses informal language THEN the Prompt Template SHALL instruct the LLM to interpret trading concepts correctly
5. WHEN a transcript is incomplete THEN the Prompt Template SHALL instruct the LLM to identify missing information

### Requirement 9

**User Story:** As a trader, I want clear documentation of the complete workflow, so that I understand how to use the prompt templates effectively.

#### Acceptance Criteria

1. WHEN a user accesses the workflow documentation THEN the Documentation SHALL list all workflow stages in order
2. WHEN a user views a workflow stage THEN the Documentation SHALL explain the purpose of that stage
3. WHEN a user views a workflow stage THEN the Documentation SHALL provide instructions for using the prompt template
4. WHEN a user views a workflow stage THEN the Documentation SHALL show expected inputs and outputs
5. WHEN a user completes all stages THEN the Documentation SHALL provide instructions for validation and backtesting
