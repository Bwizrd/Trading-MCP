# Implementation Plan

- [x] 1. Create basic HTML interface structure
  - Create single-page HTML file with basic layout
  - Add CSS for clean, readable design
  - Display placeholder for 4 workflow stages
  - Add basic navigation and progress indicators
  - _Requirements: 5.1_

- [x] 2. Add prompt templates to HTML interface
  - Create prompt template constants for all 4 workflow stages
  - Embed Stage 1 prompt (Extract Trading Logic) in HTML
  - Embed Stage 2 prompt (Clarify Ambiguities) in HTML
  - Embed Stage 3 prompt (Generate DSL JSON) in HTML
  - Add instructions for each stage
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 8.1, 8.2, 8.3, 8.4, 8.5, 5.2_

- [ ]* 2.1 Write property test for prompt template completeness
  - **Property 1: Prompt template completeness**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 8.1, 8.2, 8.3, 8.4, 8.5**

- [ ]* 2.2 Write property test for stage template display
  - **Property 6: Stage template display completeness**
  - **Validates: Requirements 5.2**

- [x] 3. Add interactive features to HTML interface
  - Implement clipboard copy functionality for prompt templates
  - Add progress tracking with localStorage
  - Add "Mark Complete" buttons for each stage
  - Display completion status visually
  - _Requirements: 5.3, 5.4_

- [ ]* 3.1 Write property test for completion tracking
  - **Property 7: Stage completion tracking**
  - **Validates: Requirements 5.4**

- [x] 4. Create MCP server structure
  - Create directory structure for strategy_builder MCP server
  - Create server entry point with basic MCP setup
  - Set up tool registration framework
  - _Requirements: 7.1, 7.4_

- [x] 5. Implement DSL validation tool
  - Create validation tool that wraps existing schema_validator
  - Implement input parameter validation
  - Implement error message formatting
  - Return validation results with strategy type and errors
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ]* 5.1 Write property test for missing field detection
  - **Property 2: Validation detects missing required fields**
  - **Validates: Requirements 4.2**

- [ ]* 5.2 Write property test for invalid syntax detection
  - **Property 3: Validation detects invalid condition syntax**
  - **Validates: Requirements 4.3**

- [ ]* 5.3 Write property test for specific error messages
  - **Property 4: Validation error messages are specific**
  - **Validates: Requirements 4.4**

- [ ]* 5.4 Write property test for validation success confirmation
  - **Property 5: Validation confirms valid strategies**
  - **Validates: Requirements 4.5**

- [ ]* 5.5 Write property test for tool input validation
  - **Property 12: Tool input validation**
  - **Validates: Requirements 7.2**

- [ ]* 5.6 Write property test for descriptive error messages
  - **Property 13: Error messages are descriptive**
  - **Validates: Requirements 7.3**

- [x] 6. Update HTML interface with validation integration
  - Add section in Stage 4 for validation
  - Display instructions for using validation MCP tool
  - Add example validation commands
  - Show expected validation output format
  - _Requirements: 5.5_

- [x] 7. Implement DSL save tool
  - Create save tool that writes DSL JSON to dsl_strategies directory
  - Implement filename generation from strategy name
  - Implement file path sanitization
  - Handle file overwrite scenarios
  - Return full file path on success
  - _Requirements: 6.1, 6.2, 6.3_

- [ ]* 7.1 Write property test for correct directory saving
  - **Property 8: Save tool writes to correct directory**
  - **Validates: Requirements 6.1**

- [ ]* 7.2 Write property test for filename generation
  - **Property 9: Filename generation from strategy name**
  - **Validates: Requirements 6.2**

- [ ]* 7.3 Write property test for file path return
  - **Property 10: Save tool returns complete file path**
  - **Validates: Requirements 6.3**

- [ ]* 7.4 Write property test for save-then-load round trip
  - **Property 11: Save-then-load round trip**
  - **Validates: Requirements 6.4, 6.5**

- [x] 8. Update HTML interface with save integration
  - Add section in Stage 4 for saving strategies
  - Display instructions for using save MCP tool
  - Add example save commands
  - Show expected file path output
  - _Requirements: 5.5_

- [x] 9. Implement DSL list tool
  - Create list tool that scans dsl_strategies directory
  - Extract strategy metadata from each JSON file
  - Return list of strategies with name, type, version, description
  - Handle empty directory case
  - _Requirements: 6.5_

- [x] 10. Finalize MCP server
  - Register all tools (validation, save, list)
  - Implement error handling and descriptive error messages
  - Ensure independent request handling
  - Test all tools are accessible
  - _Requirements: 7.2, 7.3, 7.5_

- [ ]* 10.1 Write property test for independent request handling
  - **Property 14: Independent request handling**
  - **Validates: Requirements 7.5**

- [ ] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Create workflow documentation
  - Create README or documentation file explaining the workflow
  - Document all 4 stages with purpose, instructions, inputs, and outputs
  - Include instructions for validation and backtesting after completion
  - Add examples of successful transcript-to-DSL conversions
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ]* 12.1 Write property test for stage documentation completeness
  - **Property 15: Stage documentation completeness**
  - **Validates: Requirements 9.2, 9.3, 9.4**

- [ ] 13. Update HTML interface with documentation links
  - Add link to workflow documentation
  - Add "Help" section with quick tips
  - Add troubleshooting section
  - Include example transcript snippets
  - _Requirements: 9.1, 9.5_

- [ ] 14. Configure MCP server
  - Add strategy-builder configuration to .kiro/settings/mcp.json
  - Set appropriate environment variables
  - Configure auto-approve for list_dsl_strategies tool
  - Test MCP server registration
  - _Requirements: 7.4_

- [ ] 15. Integration testing
  - Test complete workflow from HTML interface through to backtest
  - Test validation tool with various valid and invalid inputs
  - Test save tool and verify file creation
  - Test list tool and verify results
  - Verify generated strategies work with backtest engine
  - _Requirements: All_

- [ ] 16. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
