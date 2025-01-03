MAXIMUM_STEP_LIMIT = 10

DEFAULT_SYSTEM_PROMPT_WITHOUT_FUNC_DOC = """
You are an expert in using tools. You are given a question and a set of possible tools. Based on the question, you will need to make one or more function/tool calls to achieve the purpose.
If none of the function can be used, point it out. If the given question lacks the parameters required by the function, also point it out.

To use a tool, specify the tool name and the inputs to the tool. For example, to call the add(a, b) tool with inputs 2 and 3, you can say: use tool add() with argument a=2 and argument b=3.
Check how many arguments are listed in the tool. Make sure the number of inputs called match the tool definition. Make sure the inputs match.

At each turn, your should try your best to complete the tasks requested by the user within the current turn. Continue to output tools to call until you have fulfilled the user's request to the best of your ability. Once you have no more tools to call, simply say there are no more tools to call.

Think step by step. 
"""

ENGLISH_CONVERSION_SYSTEM_PROMPT = """
You are an expert in composing functions. You are given a description of how to invoke a function in natural language. Your task is to translate the given description and convert it into the format of [func_name1(params_name1=params_value1, params_name2=params_value2...), func_name2(params)]. Replace func_name, params_name,and params_value with names specified in the description. 
You MUST use this output format. You SHOULD NOT include any other text in the response.

If the description says there are no more tools to call, simply output nothing.

Here is a list of functions that you can invoke.\n{functions}\n
"""

DEFAULT_SYSTEM_PROMPT = (
    DEFAULT_SYSTEM_PROMPT_WITHOUT_FUNC_DOC
    + """
Here is a list of functions in JSON format that you can invoke.\n{functions}\n
"""
)

ENGLISH_TOOL_DESCRIPTION_SYSTEM_PROMPT = (
    DEFAULT_SYSTEM_PROMPT_WITHOUT_FUNC_DOC
    + """
Here is a list of functions that you can invoke.\n{functions}\n

To use a tool, specify the tool name and the inputs to the tool using plain English.
Check how many arguments are listed in the tool. Make sure the number of inputs called match the tool definition. Make sure the inputs match.

Think step by step. Explicitly state your hypotheses. Explain why a tool should be used at each step. 

At the end, summarize how to use the tools. 
"""
)


DEFAULT_USER_PROMPT_FOR_ADDITIONAL_FUNCTION_FC = "I have updated some more functions you can choose from. What about now?"

DEFAULT_USER_PROMPT_FOR_ADDITIONAL_FUNCTION_PROMPTING = "{functions}\n" + DEFAULT_USER_PROMPT_FOR_ADDITIONAL_FUNCTION_FC

GORILLA_TO_OPENAPI = {
    "integer": "integer",
    "number": "number",
    "float": "number",
    "string": "string",
    "boolean": "boolean",
    "bool": "boolean",
    "array": "array",
    "list": "array",
    "dict": "object",
    "object": "object",
    "tuple": "array",
    "any": "string",
    "byte": "integer",
    "short": "integer",
    "long": "integer",
    "double": "number",
    "char": "string",
    "ArrayList": "array",
    "Array": "array",
    "HashMap": "object",
    "Hashtable": "object",
    "Queue": "array",
    "Stack": "array",
    "Any": "string",
    "String": "string",
    "Bigint": "integer",
}

GORILLA_TO_PYTHON = {
    "integer": "int",
    "number": "float",
    "float": "float",
    "string": "str",
    "boolean": "bool",
    "bool": "bool",
    "array": "list",
    "list": "list",
    "dict": "dict",
    "object": "dict",
    "tuple": "tuple",
    "any": "str",
    "byte": "int",
    "short": "int",
    "long": "int",
    "double": "float",
    "char": "str",
    "ArrayList": "list",
    "Array": "list",
    "HashMap": "dict",
    "Hashtable": "dict",
    "Queue": "list",
    "Stack": "list",
    "Any": "str",
    "String": "str",
    "Bigint": "int",
}


JAVA_TYPE_CONVERSION = {
    "byte": int,
    "short": int,
    "integer": int,
    "float": float,
    "double": float,
    "long": int,
    "boolean": bool,
    "char": str,
    "Array": list,
    "ArrayList": list,
    "Set": set,
    "HashMap": dict,
    "Hashtable": dict,
    "Queue": list,  # this can be `queue.Queue` as well, for simplicity we check with list
    "Stack": list,
    "String": str,
    "any": str,
}

JS_TYPE_CONVERSION = {
    "String": str,
    "integer": int,
    "float": float,
    "Bigint": int,
    "Boolean": bool,
    "dict": dict,
    "array": list,
    "any": str,
}

UNDERSCORE_TO_DOT = [
    # TODO: Use the model style to determine this, single source of truth
    "DeepSeek-V3",
    "o1-2024-12-17-FC",
    "gpt-4o-2024-11-20-FC",
    "gpt-4o-mini-2024-07-18-FC",
    "gpt-4-turbo-2024-04-09-FC",
    "gpt-3.5-turbo-0125-FC",
    "claude-3-opus-20240229-FC",
    "claude-3-sonnet-20240229-FC",
    "claude-3-5-sonnet-20240620-FC",
    "claude-3-5-sonnet-20241022-FC",
    "claude-3-haiku-20240307-FC",
    "claude-3-5-haiku-20241022-FC",
    "nova-pro-v1.0",
    "nova-lite-v1.0",
    "nova-micro-v1.0",
    "open-mistral-nemo-2407-FC",
    "open-mixtral-8x22b-FC",
    "mistral-large-2407-FC",
    "mistral-large-2407-FC",
    "mistral-small-2402-FC",
    "mistral-small-2402-FC",
    "gemini-exp-1206-FC",
    "gemini-2.0-flash-exp-FC",
    "gemini-1.5-pro-002-FC",
    "gemini-1.5-pro-001-FC",
    "gemini-1.5-flash-002-FC",
    "gemini-1.5-flash-001-FC",
    "gemini-1.0-pro-002-FC",
    "meetkai/functionary-small-v3.1-FC",
    "meetkai/functionary-small-v3.2-FC",
    "meetkai/functionary-medium-v3.1-FC",
    "NousResearch/Hermes-2-Pro-Llama-3-8B",
    "NousResearch/Hermes-2-Pro-Llama-3-70B",
    "NousResearch/Hermes-2-Pro-Mistral-7B",
    "NousResearch/Hermes-2-Theta-Llama-3-8B",
    "NousResearch/Hermes-2-Theta-Llama-3-70B",
    "command-r-plus-FC",
    "command-r7b-12-2024-FC",
    "THUDM/glm-4-9b-chat",
    "ibm-granite/granite-20b-functioncalling",
    "yi-large-fc",
    "openbmb/MiniCPM3-4B-FC",
    "grok-beta",
]
