# Implementation Plan: AI Integration (LLM-Powered Result Interpretation)

## Overview

This plan implements AI-powered interpretation of statistical results in NEVEN. All AI logic lives in Python (`startup/startup.py`) and is exposed as `P.ai_call()`, `P.ai_setup()`, `P.ai_list_prompts()` via the existing auto-registration mechanism. No C++ changes are needed for MVP — users call `=NEVEN.P("ai_call('data', 'prompt', 'context')")` or the auto-registered `=P.ai_call(data, prompt, context)`.

## Tasks

- [x] 1. Implement AI helper functions in startup.py
  - [ ] 1.1 Add `_read_ai_config()` function
    - Read AI section from neven-config.json using NEVEN_HOME/RJ2XCL_HOME env vars
    - Validate enabled flag, provider, apiKey, endpoint, maxTokens (clamp 100-16000), temperature (clamp 0.0-2.0)
    - Return config dict on success or Spanish error message string on failure
    - Handle missing file, missing AI section, disabled state, missing API key for cloud providers
    - Resolve default endpoints per provider (openai, ollama, lmstudio)
    - Resolve promptsDirectory with env var expansion, default to %USERPROFILE%\Documents\NEVEN\prompts
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 7.1, 7.2, 7.3_

  - [ ] 1.2 Add `_load_prompt(name, prompts_dir)` function
    - Load `<name>.txt` from prompts_dir, read as UTF-8
    - Strip comment lines (lines starting with `#`)
    - Validate file exists, size ≤ 50,000 chars
    - Return template content or error message with available prompts list
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.9, 3.10_

  - [ ] 1.3 Add `_substitute_placeholders(template, data_str, context)` function
    - Replace `{{resultado}}` and `{{datos}}` with data_str
    - Replace `{{contexto}}` with context
    - Missing data replaced with empty string (no raw placeholders left)
    - _Requirements: 3.5, 3.6, 3.7, 3.8_

  - [ ] 1.4 Add `_build_request(config, prompt)` function
    - Build headers dict with Content-Type and Authorization (skip auth for ollama/lmstudio)
    - Build JSON body with model, messages array, max_tokens, temperature
    - Return (headers, json_body_string) tuple
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ] 1.5 Add `_http_post(url, headers, body, timeout=60)` function
    - Enforce HTTPS for non-localhost endpoints
    - Use urllib.request for HTTP POST
    - Extract choices[0].message.content from response JSON
    - Handle HTTP errors: 401/403 → auth error, 429 → rate limit, 5xx → server error
    - Handle timeout, network unreachable, invalid JSON
    - All error messages in Spanish with "❌ Error AI:" prefix
    - _Requirements: 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 6.6, 11.1, 11.2, 11.4, 11.5, 11.6, 11.7_

  - [ ] 1.6 Add `_mask_api_key(key)` and `_list_prompt_names(prompts_dir)` utility functions
    - _mask_api_key: show first 4 chars + "****", handle short/empty keys
    - _list_prompt_names: list .txt files in directory (without extension), return empty list if dir missing
    - _Requirements: 6.2, 6.4, 12.4_

  - [ ] 1.7 Add rate limiting with `_ai_lock` and `_rate_limited_post()`
    - Module-level threading.Lock and last_request_time
    - Enforce 1-second minimum interval between requests
    - Sequential execution via lock
    - _Requirements: 10.3, 10.4_

  - [ ]* 1.8 Write property tests for helper functions (Properties 1-6, 11, 13, 14)
    - **Property 1: Placeholder substitution completeness** — no raw placeholders remain after substitution
    - **Validates: Requirements 1.3, 1.4, 1.5, 3.5, 3.6, 3.7, 3.8**
    - **Property 2: AI config parsing round-trip** — valid config serialized/parsed produces equivalent values
    - **Validates: Requirements 2.1**
    - **Property 3: maxTokens clamping** — values outside [100, 16000] default to 1000
    - **Validates: Requirements 2.7**
    - **Property 4: Temperature clamping** — values outside [0.0, 2.0] default to 0.3
    - **Validates: Requirements 2.8**
    - **Property 5: Endpoint override** — non-empty endpoint used regardless of provider
    - **Validates: Requirements 2.6**
    - **Property 6: API key required for cloud providers** — empty key with non-local provider returns error
    - **Validates: Requirements 2.4**
    - **Property 11: HTTPS enforcement** — non-localhost HTTP URLs rejected
    - **Validates: Requirements 6.6**
    - **Property 13: Server error status mapping** — HTTP 5xx returns error with status code
    - **Validates: Requirements 5.8**
    - **Property 14: Prompt listing filters .txt only** — only .txt files returned
    - **Validates: Requirements 12.2, 12.4**

- [ ] 2. Implement main AI public functions in startup.py
  - [ ] 2.1 Add `ai_call(data_str, prompt_name, context="")` function
    - Orchestrate: read config → load prompt → substitute → rate-limited POST → cap at 32767 chars
    - Return response text or error message
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 9.6_

  - [ ] 2.2 Add `ai_setup()` function
    - Return HTML string with configuration form (provider dropdown, API key, model, endpoint, maxTokens, temperature)
    - Form posts config via window.chrome.webview.postMessage
    - _Requirements: 8.1, 8.2, 8.3_

  - [ ] 2.3 Add `ai_list_prompts()` function
    - Return comma-separated sorted list of prompt names from prompts directory
    - Handle missing/empty directory with informational message
    - _Requirements: 12.1, 12.2, 12.3, 12.4_

  - [ ]* 2.4 Write property tests for main functions (Properties 7, 8, 9, 10, 12, 17)
    - **Property 7: Response routing by length** — ≤256 chars returned directly, >256 triggers overflow
    - **Validates: Requirements 1.7, 1.8, 9.1, 9.2, 9.3**
    - **Property 8: Response JSON extraction** — choices[0].message.content extracted correctly
    - **Validates: Requirements 1.6, 5.5**
    - **Property 9: HTTP request body construction** — correct JSON structure with model, messages, max_tokens, temperature
    - **Validates: Requirements 5.1, 5.2**
    - **Property 10: API key never exposed in output** — full key never appears in error messages
    - **Validates: Requirements 6.2, 6.4, 6.5**
    - **Property 12: Error message format** — all errors start with "❌ Error AI:" in Spanish
    - **Validates: Requirements 11.1, 11.2**
    - **Property 17: Response length cap** — responses >32767 chars truncated with notice
    - **Validates: Requirements 9.6**

- [ ] 3. Checkpoint — Verify AI functions
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Add AI section to neven-config.json
  - [ ] 4.1 Update `Install/neven-config.json` with AI configuration block
    - Add "AI" section with: enabled (false), provider ("openai"), apiKey (""), model ("gpt-4o-mini"), endpoint ("https://api.openai.com/v1/chat/completions"), maxTokens (1000), temperature (0.3), promptsDirectory ("%USERPROFILE%\\Documents\\NEVEN\\prompts")
    - Preserve all existing sections (NEVEN, WebView2, Pluto)
    - Set enabled: false by default — user activates after setting API key
    - _Requirements: 2.1, 7.4_

  - [ ]* 4.2 Write unit tests for config loading with new AI section
    - Test config with AI section present and valid
    - Test config without AI section → setup message
    - Test config with enabled: false → disabled message
    - _Requirements: 2.2, 2.3, 7.1, 7.2_

- [ ] 5. Create default prompt templates
  - [ ] 5.1 Create `Install/prompts/interpretar_regresion.txt`
    - Linear regression interpretation prompt in Spanish
    - Include comment header explaining purpose and expected input
    - Use all three placeholders: {{resultado}}, {{datos}}, {{contexto}}
    - _Requirements: 4.2, 4.4, 4.5, 4.6_

  - [ ] 5.2 Create `Install/prompts/detectar_outliers.txt`
    - Outlier detection and explanation prompt in Spanish
    - Include comment header, use all three placeholders
    - _Requirements: 4.2, 4.4, 4.5, 4.6_

  - [ ] 5.3 Create `Install/prompts/explicar_acp.txt`
    - PCA component explanation prompt in Spanish
    - Include comment header, use all three placeholders
    - _Requirements: 4.2, 4.4, 4.5, 4.6_

  - [ ] 5.4 Create `Install/prompts/resumir_descriptiva.txt`
    - Descriptive statistics summary prompt in Spanish
    - Include comment header, use all three placeholders
    - _Requirements: 4.2, 4.4, 4.5, 4.6_

  - [ ] 5.5 Create `Install/prompts/interpretar_series.txt`
    - Time series analysis interpretation prompt in Spanish
    - Include comment header, use all three placeholders
    - _Requirements: 4.2, 4.4, 4.5, 4.6_

  - [ ] 5.6 Create `Install/prompts/evaluar_modelo.txt`
    - Model evaluation (AIC, BIC, residuals) prompt in Spanish
    - Include comment header, use all three placeholders
    - _Requirements: 4.2, 4.4, 4.5, 4.6_

  - [ ] 5.7 Create `Install/prompts/comparar_modelos.txt`
    - Model comparison and selection prompt in Spanish
    - Include comment header, use all three placeholders
    - _Requirements: 4.2, 4.4, 4.5, 4.6_

- [ ] 6. Update installer to deploy prompts
  - [ ] 6.1 Update `Install/Install-NEVEN.ps1` to create prompts directory and copy defaults
    - Create `$env:USERPROFILE\Documents\NEVEN\prompts\` directory
    - Copy all .txt files from Install/prompts/ to the prompts directory
    - Only copy if file does not already exist (preserve user modifications)
    - _Requirements: 4.1, 4.3_

- [ ] 7. Final checkpoint — End-to-end verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All AI functions go in `startup/startup.py` so they auto-register as `P.ai_call()`, `P.ai_setup()`, `P.ai_list_prompts()`
- No C++ changes needed — users call via `=P.ai_call(data, prompt, context)` or `=NEVEN.P("ai_call(...)")`
- For WebView2 overflow: `=NEVEN.V(P.ai_call(A1:D5, "interpretar_regresion"))`
- Config has AI enabled: false by default — user must set their API key first
- Property tests use `pytest` + `hypothesis` library
- All HTTP mocked in tests — no real API calls needed
