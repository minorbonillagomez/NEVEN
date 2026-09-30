# Requirements Document — AI Integration (LLM-Powered Result Interpretation)

## Introduction

NEVEN is a C++17 Excel XLL add-in that integrates R 4.4.1, Julia 1.12.6, and Python 3.13 as scripting engines. Users execute statistical functions like `=R.MR_Lineal(Y, X, 1)` and get numerical results (coefficients, R², p-values). However, interpreting these results requires statistical knowledge that many users lack. This feature adds AI-powered interpretation by calling LLM APIs (OpenAI, Claude, Gemini, or any OpenAI-compatible endpoint) to explain statistical results in plain language. The AI call is routed through ControlPython.exe since Python has the best HTTP libraries and is already integrated. The feature is entirely optional — NEVEN works perfectly without it.

## Glossary

- **AI_Engine**: The subsystem within ControlPython.exe responsible for making HTTP requests to LLM API endpoints and returning the response text.
- **LLM_Endpoint**: An HTTP API that accepts chat completion requests in the OpenAI-compatible format (`/v1/chat/completions`) and returns generated text.
- **Prompt_Template**: A UTF-8 `.txt` file stored in the Prompts_Directory containing instructions for the LLM with placeholder tokens for dynamic data substitution.
- **Prompts_Directory**: The user-editable directory where prompt templates are stored, located at `%USERPROFILE%\Documents\NEVEN\prompts\` by default.
- **Placeholder**: A token in a Prompt_Template delimited by double curly braces (e.g., `{{resultado}}`, `{{datos}}`, `{{contexto}}`) that the AI_Engine replaces with actual data before sending to the LLM_Endpoint.
- **AI_Config**: The `"AI"` section within `neven-config.json` that stores provider settings, API key, model name, endpoint URL, and generation parameters.
- **API_Key**: The authentication credential for the LLM_Endpoint, stored in the AI_Config section of `neven-config.json`.
- **Provider**: A named LLM service (e.g., "openai", "azure", "ollama", "lmstudio", "custom") that determines the endpoint URL format and authentication headers.
- **Cell_Response**: A text response short enough to fit directly in an Excel cell (256 characters or fewer).
- **WebView2_Response**: A text response longer than 256 characters that is rendered as formatted markdown in a WebView2 viewer window.
- **Setup_Function**: The `=NEVEN.AI.SETUP()` Excel function that guides the user through initial AI configuration interactively.

## Requirements

### Requirement 1: NEVEN.AI() Excel Function

**User Story:** As a user, I want to call `=NEVEN.AI()` in an Excel cell with my data and a prompt name, so that I get a natural language interpretation of my statistical results without leaving Excel.

#### Acceptance Criteria

1. THE XLL SHALL register a function `NEVEN.AI` that accepts three parameters: a data range (string representation of cell values), a prompt template name (string), and an optional context string.
2. WHEN `NEVEN.AI` is called with a valid data range and prompt name, THE AI_Engine SHALL load the corresponding Prompt_Template from the Prompts_Directory, substitute placeholders, send the request to the configured LLM_Endpoint, and return the response text.
3. WHEN `NEVEN.AI` is called with an empty data range and a valid prompt name, THE AI_Engine SHALL send the prompt with the `{{resultado}}` and `{{datos}}` placeholders replaced by empty strings.
4. WHEN the optional context parameter is provided, THE AI_Engine SHALL substitute the `{{contexto}}` placeholder with the context string value.
5. WHEN the optional context parameter is omitted, THE AI_Engine SHALL substitute the `{{contexto}}` placeholder with an empty string.
6. WHEN the LLM_Endpoint returns a successful response, THE AI_Engine SHALL extract the generated text from the response JSON (`choices[0].message.content`).
7. WHEN the response text is 256 characters or fewer, THE NEVEN.AI function SHALL return the text directly in the calling cell as a Cell_Response.
8. WHEN the response text exceeds 256 characters, THE NEVEN.AI function SHALL open the response in a WebView2 viewer as formatted markdown and return a summary string in the cell indicating the full response is displayed in the viewer.

### Requirement 2: API Key and Provider Configuration

**User Story:** As a user, I want to configure my LLM provider and API key in `neven-config.json`, so that NEVEN knows which AI service to call and can authenticate requests.

#### Acceptance Criteria

1. THE ConfigService SHALL read an `"AI"` section from `neven-config.json` containing the fields: `enabled` (boolean), `provider` (string), `apiKey` (string), `model` (string), `endpoint` (string), `maxTokens` (integer), `temperature` (number), and `promptsDirectory` (string).
2. WHEN the `"AI"` section is absent from `neven-config.json`, THE AI_Engine SHALL treat AI as disabled and return a setup instruction message when `NEVEN.AI` is called.
3. WHEN `"enabled"` is set to `false`, THE AI_Engine SHALL return a message indicating that AI is disabled in the configuration.
4. WHEN `"apiKey"` is an empty string and the provider is not "ollama" or "lmstudio", THE AI_Engine SHALL return a message instructing the user to configure their API key.
5. THE AI_Engine SHALL support the following providers without additional configuration beyond the API key: "openai" (endpoint `https://api.openai.com/v1/chat/completions`), "azure" (user-provided endpoint), "ollama" (default endpoint `http://localhost:11434/v1/chat/completions`, no API key required), "lmstudio" (default endpoint `http://localhost:1234/v1/chat/completions`, no API key required), and "custom" (user-provided endpoint).
6. WHEN the `"endpoint"` field is provided, THE AI_Engine SHALL use it as the LLM_Endpoint URL regardless of the provider value.
7. THE AI_Engine SHALL default `maxTokens` to 1000 if not specified or if the value is outside the range 100–16000.
8. THE AI_Engine SHALL default `temperature` to 0.3 if not specified or if the value is outside the range 0.0–2.0.

### Requirement 3: Prompt Template System

**User Story:** As a user, I want to create and edit prompt templates as plain text files, so that I can customize how the AI interprets different types of statistical results.

#### Acceptance Criteria

1. THE AI_Engine SHALL load prompt templates from the Prompts_Directory configured in `AI.promptsDirectory`, defaulting to `%USERPROFILE%\Documents\NEVEN\prompts\` if not specified.
2. WHEN `NEVEN.AI` is called with a prompt name, THE AI_Engine SHALL look for a file named `<prompt_name>.txt` in the Prompts_Directory.
3. IF the specified prompt template file does not exist, THEN THE AI_Engine SHALL return an error message indicating the prompt was not found and listing the available prompts in the directory.
4. THE AI_Engine SHALL read prompt template files as UTF-8 encoded text, supporting Spanish, English, and any other language that uses UTF-8 encoding.
5. THE AI_Engine SHALL replace the placeholder `{{resultado}}` with the string representation of the data range values passed to `NEVEN.AI`.
6. THE AI_Engine SHALL replace the placeholder `{{datos}}` with the same data range values as `{{resultado}}` (alias for flexibility in prompt authoring).
7. THE AI_Engine SHALL replace the placeholder `{{contexto}}` with the optional context parameter passed to `NEVEN.AI`.
8. WHEN a placeholder token appears in the template but no corresponding data is provided, THE AI_Engine SHALL replace it with an empty string rather than leaving the raw placeholder in the sent prompt.
9. THE AI_Engine SHALL support prompt templates up to 50,000 characters in length.
10. IF a prompt template exceeds 50,000 characters, THEN THE AI_Engine SHALL return an error message indicating the template is too large.

### Requirement 4: Default Prompt Templates

**User Story:** As a user, I want NEVEN to ship with pre-built prompt templates for common statistical analyses, so that I can start using AI interpretation immediately without writing my own prompts.

#### Acceptance Criteria

1. THE Installer SHALL create the Prompts_Directory and deploy default prompt template files during installation.
2. THE Installer SHALL deploy the following default prompt templates: `interpretar_regresion.txt` (linear regression interpretation), `detectar_outliers.txt` (outlier detection), `explicar_acp.txt` (PCA explanation), `resumir_descriptiva.txt` (descriptive statistics summary), `interpretar_series.txt` (time series interpretation), `evaluar_modelo.txt` (model evaluation), and `comparar_modelos.txt` (model comparison).
3. WHEN a default prompt template already exists in the Prompts_Directory, THE Installer SHALL preserve the user-modified version and not overwrite it.
4. THE default prompt templates SHALL be written in Spanish and include instructions for the LLM to respond in Spanish.
5. THE default prompt templates SHALL use all three placeholders (`{{resultado}}`, `{{datos}}`, `{{contexto}}`) to demonstrate the template system.
6. THE default prompt templates SHALL include a brief comment header (lines starting with `#`) explaining the purpose and expected input format.

### Requirement 5: HTTP Request to LLM Endpoint

**User Story:** As a user, I want NEVEN to send my data to the configured LLM API and handle the response correctly, so that I get reliable AI interpretations.

#### Acceptance Criteria

1. THE AI_Engine SHALL construct an HTTP POST request to the LLM_Endpoint with `Content-Type: application/json` and an `Authorization: Bearer <API_Key>` header.
2. THE AI_Engine SHALL format the request body as an OpenAI-compatible chat completion: `{"model": "<model>", "messages": [{"role": "user", "content": "<substituted_prompt>"}], "max_tokens": <maxTokens>, "temperature": <temperature>}`.
3. WHEN the provider is "ollama" or "lmstudio", THE AI_Engine SHALL omit the `Authorization` header from the request.
4. THE AI_Engine SHALL set a request timeout of 60 seconds by default.
5. WHEN the HTTP response status is 200, THE AI_Engine SHALL parse the JSON response and extract `choices[0].message.content` as the result text.
6. WHEN the HTTP response status is 401 or 403, THE AI_Engine SHALL return an error message indicating the API key is invalid or expired.
7. WHEN the HTTP response status is 429, THE AI_Engine SHALL return an error message indicating rate limiting and suggesting the user wait before retrying.
8. WHEN the HTTP response status is 500 or above, THE AI_Engine SHALL return an error message indicating a server error with the status code.
9. IF the HTTP request times out, THEN THE AI_Engine SHALL return an error message indicating the request timed out and suggesting the user check their network connection.
10. IF the network is unreachable, THEN THE AI_Engine SHALL return an error message indicating no network connectivity.
11. THE AI_Engine SHALL use Python's `urllib.request` module for HTTP calls, falling back gracefully if `requests` is not installed.

### Requirement 6: Security and API Key Protection

**User Story:** As a user, I want my API key to be handled securely, so that it is never exposed in logs, error messages, or sent to other language engines.

#### Acceptance Criteria

1. THE AI_Engine SHALL read the API_Key exclusively from the AI_Config section of `neven-config.json` at the time of each request.
2. THE AI_Engine SHALL never write the API_Key value to any log file, console output, or error message.
3. THE AI_Engine SHALL never transmit the API_Key to ControlR.exe or ControlJulia.exe processes.
4. WHEN logging AI requests for debugging, THE AI_Engine SHALL mask the API_Key as `"sk-****"` or equivalent, showing only the first 4 characters.
5. THE AI_Engine SHALL never include the API_Key in Excel cell return values or error messages displayed to the user.
6. THE AI_Engine SHALL transmit the API_Key only over HTTPS connections, except when the provider is "ollama" or "lmstudio" (localhost connections).

### Requirement 7: Graceful Degradation When AI Is Not Configured

**User Story:** As a user, I want NEVEN to work perfectly without AI configured, so that the AI feature is truly optional and does not interfere with existing functionality.

#### Acceptance Criteria

1. WHEN the AI_Config section is missing from `neven-config.json`, THE NEVEN.AI function SHALL return the message: "AI no configurado. Use =NEVEN.AI.SETUP() para configurar o edite la sección AI en neven-config.json".
2. WHEN `AI.enabled` is `false`, THE NEVEN.AI function SHALL return the message: "AI deshabilitado. Cambie enabled:true en neven-config.json para activar."
3. WHEN the API_Key is empty and the provider requires authentication, THE NEVEN.AI function SHALL return the message: "API key no configurada. Agregue su clave en neven-config.json → AI → apiKey".
4. THE absence of AI configuration SHALL NOT affect the startup, registration, or operation of any other NEVEN function (R, Julia, Python, WebView2, Pluto, Quarto).
5. THE XLL SHALL register the `NEVEN.AI` and `NEVEN.AI.SETUP` functions regardless of whether AI is configured, so that users can discover the feature through the function wizard.

### Requirement 8: Interactive Setup Function

**User Story:** As a user, I want a `=NEVEN.AI.SETUP()` function that guides me through configuring AI step by step, so that I can set up the feature without manually editing JSON.

#### Acceptance Criteria

1. THE XLL SHALL register a function `NEVEN.AI.SETUP` that takes no parameters.
2. WHEN `NEVEN.AI.SETUP` is called, THE Setup_Function SHALL open a WebView2 dialog presenting a configuration form with fields for: provider selection (dropdown), API key (password input), model name, endpoint URL (pre-filled based on provider), max tokens, and temperature.
3. WHEN the user submits the configuration form, THE Setup_Function SHALL validate that the API key is non-empty (unless provider is ollama/lmstudio), the endpoint URL is a valid URL, maxTokens is between 100 and 16000, and temperature is between 0.0 and 2.0.
4. WHEN validation passes, THE Setup_Function SHALL write the AI_Config section to `neven-config.json`, preserving all other existing configuration sections.
5. WHEN the configuration is saved successfully, THE Setup_Function SHALL return the message "AI configurado correctamente. Pruebe con =NEVEN.AI(A1:D5, \"interpretar_regresion\")".
6. IF writing to `neven-config.json` fails, THEN THE Setup_Function SHALL return an error message indicating the file could not be written and suggesting the user check file permissions.

### Requirement 9: Response Display and WebView2 Overflow

**User Story:** As a user, I want short AI responses in my cell and long responses in a formatted viewer, so that I can read interpretations comfortably regardless of length.

#### Acceptance Criteria

1. WHEN the AI response text is 256 characters or fewer, THE NEVEN.AI function SHALL return the full text directly in the Excel cell.
2. WHEN the AI response text exceeds 256 characters, THE NEVEN.AI function SHALL open a WebView2 viewer window displaying the response rendered as markdown (with headers, bold, lists, and code blocks formatted).
3. WHEN the response overflows to WebView2, THE NEVEN.AI function SHALL return a truncated preview (first 200 characters followed by "... [ver visor]") in the Excel cell.
4. THE WebView2 viewer for AI responses SHALL use the same viewer infrastructure as `NEVEN.v()`, respecting the `maxViewers` and `maxMemoryMB` configuration limits.
5. WHEN the AI response contains markdown formatting, THE WebView2 viewer SHALL render it with appropriate CSS styling for readability (font size, line spacing, code highlighting).
6. THE AI response text SHALL be limited to 32,767 characters (Excel cell maximum) even when displayed in WebView2, truncating with a notice if the LLM returns more.

### Requirement 10: Processing Indicator and Asynchronous Behavior

**User Story:** As a user, I want to see that NEVEN is processing my AI request, so that I know the system is working and has not frozen.

#### Acceptance Criteria

1. WHEN an AI request is sent to the LLM_Endpoint, THE NEVEN.AI function SHALL immediately return the text "⏳ Procesando..." in the cell while waiting for the response.
2. WHEN the LLM_Endpoint returns a response, THE NEVEN.AI function SHALL update the cell value with the actual response text, replacing the processing indicator.
3. WHEN multiple `NEVEN.AI` calls are made simultaneously, THE AI_Engine SHALL process them sequentially (one request at a time) to respect API rate limits.
4. THE AI_Engine SHALL enforce a minimum interval of 1 second between consecutive API requests to avoid rate limiting.

### Requirement 11: Error Messages in User Language

**User Story:** As a user, I want error messages from the AI feature to be in Spanish and clearly explain what went wrong, so that I can fix issues without technical knowledge.

#### Acceptance Criteria

1. WHEN an error occurs during AI processing, THE NEVEN.AI function SHALL return a descriptive error message in Spanish directly in the Excel cell.
2. THE error messages SHALL follow the format: "❌ Error AI: <descripción del problema>".
3. WHEN the prompt template is not found, THE NEVEN.AI function SHALL return: "❌ Error AI: Prompt '<nombre>' no encontrado en <directorio>. Prompts disponibles: <lista>".
4. WHEN the API returns an authentication error, THE NEVEN.AI function SHALL return: "❌ Error AI: Clave API inválida o expirada. Verifique apiKey en neven-config.json".
5. WHEN the API returns a rate limit error, THE NEVEN.AI function SHALL return: "❌ Error AI: Límite de solicitudes alcanzado. Espere unos segundos e intente de nuevo."
6. WHEN the request times out, THE NEVEN.AI function SHALL return: "❌ Error AI: Tiempo de espera agotado (60s). Verifique su conexión a internet."
7. WHEN the network is unreachable, THE NEVEN.AI function SHALL return: "❌ Error AI: Sin conexión a internet. Verifique su red."

### Requirement 12: Prompt Template Listing

**User Story:** As a user, I want to see which prompt templates are available, so that I know what interpretations I can request.

#### Acceptance Criteria

1. THE XLL SHALL register a function `NEVEN.AI.PROMPTS` that takes no parameters.
2. WHEN `NEVEN.AI.PROMPTS` is called, THE function SHALL return a comma-separated list of available prompt template names (filenames without the `.txt` extension) found in the Prompts_Directory.
3. WHEN the Prompts_Directory does not exist or is empty, THE function SHALL return the message: "No hay prompts disponibles. Cree archivos .txt en <directorio>".
4. THE function SHALL list only files with the `.txt` extension, ignoring other file types in the directory.
