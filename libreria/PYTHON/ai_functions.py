"""
NEVEN Python AI Functions

AI/LLM integration functions for the NEVEN Excel add-in.
Provides: Py.ai_call, Py.ai_setup, Py.ai_list_prompts

These functions are registered during startup.py execution and become
available as Excel-callable functions via the Py. prefix.
"""

import os
import json


# ─── Prompt Templates ─────────────────────────────────────────────────────────

PROMPT_TEMPLATES = {
    "explain": {
        "name": "explain",
        "description": "Explain code or concept",
        "template": "Please explain the following:\n\n{input}"
    },
    "generate": {
        "name": "generate",
        "description": "Generate Python code from description",
        "template": "Generate Python code for the following task:\n\n{input}\n\nReturn only the code, no explanation."
    },
    "review": {
        "name": "review",
        "description": "Review code for issues",
        "template": "Review the following code for bugs, performance issues, and best practices:\n\n```python\n{input}\n```"
    },
    "document": {
        "name": "document",
        "description": "Generate documentation",
        "template": "Generate comprehensive documentation for the following code:\n\n```python\n{input}\n```"
    },
    "summarize": {
        "name": "summarize",
        "description": "Summarize data or text",
        "template": "Summarize the following:\n\n{input}"
    },
    "translate": {
        "name": "translate",
        "description": "Translate code between languages",
        "template": "Translate the following code to {target_language}:\n\n```\n{input}\n```"
    }
}


def ai_apply_template(template_name, input_text, **kwargs):
    """Apply a prompt template to input text.

    Args:
        template_name: Name of the template (explain, generate, review, etc.)
        input_text: The input to apply the template to
        **kwargs: Additional template variables

    Returns:
        Formatted prompt string, or error message if template not found
    """
    if template_name not in PROMPT_TEMPLATES:
        return f"[Unknown template: {template_name}. Available: {', '.join(PROMPT_TEMPLATES.keys())}]"

    template = PROMPT_TEMPLATES[template_name]["template"]
    try:
        return template.format(input=input_text, **kwargs)
    except KeyError as e:
        return f"[Template '{template_name}' requires parameter: {e}]"


def ai_batch_call(prompts, context=None):
    """Call AI with multiple prompts.

    Args:
        prompts: List of prompt strings
        context: Optional shared context

    Returns:
        List of response strings
    """
    results = []
    for prompt in prompts:
        result = ai_call(prompt, context)
        results.append(result)
    return results


def ai_get_config():
    """Return current AI configuration (without exposing the key).

    Returns:
        Dict with model, configured status, and available templates
    """
    return {
        "configured": _ai_configured,
        "model": _ai_model,
        "templates": list(PROMPT_TEMPLATES.keys()),
        "has_openai": _check_openai_available()
    }


def _check_openai_available():
    """Check if the openai package is importable."""
    try:
        import openai
        return True
    except ImportError:
        return False


# ─── Registration ─────────────────────────────────────────────────────────────

def _register_ai_functions():
    """Register AI functions with the NEVEN function registry."""
    register_function("ai_apply_template", "Apply an AI prompt template", "AI",
                      [{"name": "template_name", "description": "Template name"},
                       {"name": "input_text", "description": "Input text"}])
    register_function("ai_batch_call", "Call AI with multiple prompts", "AI",
                      [{"name": "prompts", "description": "List of prompts"}])
    register_function("ai_get_config", "Get AI configuration status", "AI")


_register_ai_functions()
