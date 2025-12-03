"""
Prompt Templates for Transcript Strategy Builder

Contains the prompt templates for all 4 workflow stages.
"""

# Stage 1: Extract Trading Logic
STAGE_1_EXTRACT_LOGIC = """You are a trading strategy extraction expert. Your task is to analyze a YouTube transcript 
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
"""

# Stage 2: Clarify Ambiguities
STAGE_2_CLARIFY_AMBIGUITIES = """You are a trading strategy refinement expert. Your task is to clarify ambiguities 
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
"""

# Stage 3: Generate DSL JSON
STAGE_3_GENERATE_DSL = """You are a DSL JSON generation expert. Your task is to convert refined trading logic 
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
  - type: string ("SMA", "EMA", "RSI", or "MACD")
  - period: integer (1-200) - required for SMA, EMA, RSI
  - alias: string (unique identifier for this indicator)
  - For MACD only (all optional, defaults: 12, 26, 9):
    - fast_period: integer (default: 12)
    - slow_period: integer (default: 26)
    - signal_period: integer (default: 9)
- conditions: object
  - buy: object
    - compare: string (comparison using indicator aliases)
    - crossover: boolean (optional, true if crossover required)
  - sell: object
    - compare: string (comparison using indicator aliases)
    - crossover: boolean (optional, true if crossover required)
- risk_management: object (same as time-based)

MACD INDICATOR NOTES:
- MACD generates three values: macd line, signal line, and histogram
- Use alias for MACD line (e.g., "macd")
- Signal line is available as "{alias}_signal" (e.g., "macd_signal")
- Histogram is available as "{alias}_histogram" (e.g., "macd_histogram")
- Common conditions:
  - Crossover: "macd > macd_signal" with crossover: true
  - Zero line: "macd > 0" or "macd < 0"
  - Histogram: "macd_histogram > 0"

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

EXAMPLE INDICATOR-BASED STRATEGY (MA Crossover):
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

EXAMPLE MACD STRATEGY:
{
  "name": "MACD Crossover Strategy",
  "version": "1.0.0",
  "description": "MACD signal line crossover with zero line filter",
  "indicators": [
    {"type": "MACD", "alias": "macd"}
  ],
  "conditions": {
    "buy": {"compare": "macd > macd_signal", "crossover": true},
    "sell": {"compare": "macd < macd_signal", "crossover": true}
  },
  "risk_management": {
    "stop_loss_pips": 25,
    "take_profit_pips": 40,
    "max_daily_trades": 5
  }
}

INSTRUCTIONS:
1. Determine if this is a time-based or indicator-based strategy
2. If the strategy uses unsupported indicators or features:
   - DO NOT refuse to create the DSL
   - SIMPLIFY the strategy to use supported indicators (SMA, EMA, RSI, MACD)
   - APPROXIMATE the behavior using available indicators
   - ADD a comment in the description explaining the simplification
3. Generate valid DSL JSON following the appropriate schema
4. Ensure all required fields are present
5. Use appropriate comparison operators: >, <, >=, <=, ==, !=
6. Output ONLY the JSON, no additional text

HANDLING UNSUPPORTED FEATURES:
- If strategy uses unsupported indicators (e.g., Stochastic, ADX):
  → Use similar supported indicators (RSI for oscillators, MACD for momentum)
- If strategy has complex multi-candle logic:
  → Simplify to single-candle crossover conditions
- If strategy has trailing stops or advanced exits:
  → Use standard stop loss and take profit
- ALWAYS output a valid DSL JSON, even if simplified

OUTPUT:
[Valid DSL JSON only]
"""

# All prompt templates
PROMPT_TEMPLATES = {
    1: STAGE_1_EXTRACT_LOGIC,
    2: STAGE_2_CLARIFY_AMBIGUITIES,
    3: STAGE_3_GENERATE_DSL
}


def get_prompt_template(stage: int) -> str:
    """
    Get the prompt template for a specific stage.
    
    Args:
        stage: Stage number (1-3)
        
    Returns:
        Prompt template string
        
    Raises:
        ValueError: If stage number is invalid
    """
    if stage not in PROMPT_TEMPLATES:
        raise ValueError(f"Invalid stage number: {stage}. Must be 1-3.")
    
    return PROMPT_TEMPLATES[stage]
