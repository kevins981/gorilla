import json
import time
from copy import deepcopy

from bfcl.constant import RESULT_PATH, VERSION_PREFIX
from bfcl.eval_checker.multi_turn_eval.multi_turn_utils import (
    STATELESS_CLASSES,
    execute_multi_turn_func_call,
    is_empty_execute_response,
)
from bfcl.model_handler.constant import (
    DEFAULT_USER_PROMPT_FOR_ADDITIONAL_FUNCTION_FC,
    DEFAULT_USER_PROMPT_FOR_ADDITIONAL_FUNCTION_PROMPTING,
    MAXIMUM_STEP_LIMIT,
)
from bfcl.model_handler.utils import get_translator_system_prompt

from bfcl.model_handler.model_style import ModelStyle
from bfcl.utils import load_file, make_json_serializable, sort_key
from overrides import final

#def englishfy_tool_definition(tools) -> str:
#    # Takes the string in JSON format that describes available tools. Convert into English
#    out_string = ""
#
#    for tool in tools:
#        out_string += f"\nFunction name: {tool['name']}"
#        description = tool['description']
#        out_string += description.replace('Note that the provided function is in Python 3 syntax.','')
#        out_string += "The function takes the following inputs: "
#        for param, details in tool['parameters']['properties'].items():
#            out_string += f"\n  - {param}: {details['type']} type. {details['description']}"
#        out_string += "\n This function returns following outputs: \n"
#        for resp_var, resp_details in tool['response']['properties'].items():
#            out_string += f"  - {resp_var}: {resp_details['type']} type. {resp_details['description']}"
#        out_string += f"\n\n"
#
#    return out_string

class BaseHandler:
    model_name: str
    model_style: ModelStyle

    def __init__(self, model_name, temperature) -> None:
        self.model_name = model_name
        # Replace the slash with underscore to avoid creating subdirectories
        # Replace the dash and dot with underscore for valid variable name
        self.model_name_underline_replaced = (
            model_name.replace("/", "_").replace("-", "_").replace(".", "_")
        )
        self.temperature = temperature
        self.is_fc_model = False  # Whether the model is a function calling model
    


    def inference(self, test_entry: dict, include_input_log: bool, exclude_state_log: bool):
        # This method is used to retrive model response for each model.

        # FC model
        # TODO: Let all models have the is_fc_model attribute and remove the "FC" check
        if "FC" in self.model_name or self.is_fc_model:
            if "multi_turn" in test_entry["id"]:
                return self.inference_multi_turn_FC(test_entry, include_input_log, exclude_state_log)
            else:
                return self.inference_single_turn_FC(test_entry, include_input_log)
        # Prompting model
        else:
            if "multi_turn" in test_entry["id"]:
                return self.inference_multi_turn_prompting(
                    test_entry, include_input_log, exclude_state_log
                )
            else:
                return self.inference_single_turn_prompting(
                    test_entry, include_input_log
                )

    @final
    def inference_multi_turn_FC(
        self, test_entry: dict, include_input_log: bool, exclude_state_log: bool
    ) -> tuple[list[list], dict]:
        initial_config: dict = test_entry["initial_config"]
        involved_classes: list = test_entry["involved_classes"]
        test_entry_id: str = test_entry["id"]
        test_category: str = test_entry_id.rsplit("_", 1)[0]

        # This is only for the miss function category
        # A mapping from turn index to function to holdout
        holdout_function: dict[int, list] = test_entry.get("missed_function", {})

        total_input_token_count: list[list[float]] = []
        total_output_token_count: list[list[float]] = []
        total_latency: list[list[float]] = []
        all_model_response: list[list] = (
            []
        )  # The model response that will be used for later evaluation
        all_inference_log: list[list[dict]] = (
            []
        )  # The debugging log for human to understand
        force_quit = False  # Whether the model has been forced to quit. If True, this whole entry will be failed.

        # Execute no function call, but just to get a reference to all the instances to get the initial state for logging purpose
        if not exclude_state_log:
            _, involved_instances = execute_multi_turn_func_call(
                [],
                initial_config,
                involved_classes,
                self.model_name_underline_replaced,
                test_entry_id,
                long_context=(
                    "long_context" in test_category or "composite" in test_category
                ),
                is_evaL_run=False,
            )
            state_log = []
            for class_name, class_instance in involved_instances.items():
                if class_name in STATELESS_CLASSES:
                    continue
                class_instance = deepcopy(class_instance)  # Avoid modification in future turns
                state_log.append(
                    {
                        "role": "state_info",
                        "class_name": class_name,
                        "content": {
                            key: value
                            for key, value in vars(class_instance).items()
                            if not key.startswith("_")
                        },
                    }
                )
            all_inference_log.append(state_log)

        inference_data: dict = {}
        inference_data = self._pre_query_processing_FC(inference_data, test_entry)
        inference_data = self._compile_tools(inference_data, test_entry)

        all_multi_turn_messages: list[list[dict]] = test_entry["question"]
        for turn_idx, current_turn_message in enumerate(all_multi_turn_messages):
            current_turn_message: list[dict]

            if str(turn_idx) in holdout_function:
                test_entry["function"].extend(holdout_function[str(turn_idx)])
                # Since we have added new functions, we need to recompile the tools
                inference_data = self._compile_tools(inference_data, test_entry)
                assert (
                    len(current_turn_message) == 0
                ), "Holdout turn should not have user message."
                current_turn_message = [
                    {
                        "role": "user",
                        "content": DEFAULT_USER_PROMPT_FOR_ADDITIONAL_FUNCTION_FC,
                    }
                ]

            if turn_idx == 0:
                inference_data = self.add_first_turn_message_FC(
                    inference_data, current_turn_message
                )
            else:
                inference_data = self._add_next_turn_user_message_FC(
                    inference_data, current_turn_message
                )

            current_turn_response = []
            current_turn_inference_log: list[dict] = {"begin_of_turn_query": current_turn_message}
            current_turn_input_token_count: list[float] = []
            current_turn_output_token_count: list[float] = []
            current_turn_latency: list[float] = []

            count = 0
            while True:
                print("-" * 100)
                print(
                    f"ID: {test_entry_id.replace('multi_turn_', '')}, Turn: {turn_idx}, Step: {count}"
                )
                current_step_inference_log: list[dict] = []
                # Add to the current_turn_inference_log at beginning of each step so that we don't need to bother dealing with the break statements
                current_turn_inference_log[f"step_{count}"] = current_step_inference_log

                api_response, query_latency = self._query_FC(inference_data)

                # This part of logging is disabled by default because it is too verbose and will make the result file extremely large
                # It is only useful to see if the inference pipeline is working as expected (eg, does it convert all the inputs correctly)
                if include_input_log:
                    current_step_inference_log.append(
                        {
                            "role": "inference_input",
                            "content": inference_data.get("inference_input_log", ""),
                        }
                    )

                # Try parsing the model response
                model_response_data = self._parse_query_response_FC(api_response)
                model_responses = model_response_data["model_responses"]

                # Add the assistant message to the chat history
                inference_data = self._add_assistant_message_FC(
                    inference_data, model_response_data
                )

                # Process the metadata
                current_turn_input_token_count.append(model_response_data["input_token"])
                current_turn_output_token_count.append(model_response_data["output_token"])
                current_turn_latency.append(query_latency)

                current_turn_response.append(model_responses)
                current_step_inference_log.append(
                    {"role": "assistant", "content": model_responses}
                )

                # Try decoding the model response
                try:
                    print("!!!!!!!!!! before decode ")
                    decoded_model_responses = self.decode_execute(model_responses)
                    print("!!!!!!!!!! after decode ", decoded_model_responses)
                    current_step_inference_log.append(
                        {
                            "role": "handler_log",
                            "content": "Successfully decoded model response.",
                            "model_response_decoded": decoded_model_responses,
                        }
                    )

                    if is_empty_execute_response(decoded_model_responses):
                        print("Empty response from the model. Proceed to next turn.")
                        current_step_inference_log.append(
                            {
                                "role": "handler_log",
                                "content": f"Empty response from the model. Proceed to next turn.",
                                "model_response_decoded": decoded_model_responses,
                            }
                        )
                        break

                except Exception as e:
                    print("Failed to decode the model response. Proceed to next turn.")
                    current_step_inference_log.append(
                        {
                            "role": "handler_log",
                            "content": f"Error decoding the model response. Proceed to next turn.",
                            "error": str(e),
                        }
                    )
                    break

                # Obtain the execution results
                execution_results, involved_instances = execute_multi_turn_func_call(
                    decoded_model_responses,
                    initial_config,
                    involved_classes,
                    self.model_name_underline_replaced,
                    test_entry_id,
                    long_context=(
                        "long_context" in test_category or "composite" in test_category
                    ),
                    is_evaL_run=False,
                )

                # Add the execution results to the chat history for the next turn
                inference_data = self._add_execution_results_FC(
                    inference_data, execution_results, model_response_data
                )

                for execution_result in execution_results:
                    current_step_inference_log.append(
                        {
                            "role": "tool",
                            "content": execution_result,
                        }
                    )

                count += 1
                # Force quit after too many steps
                if count > MAXIMUM_STEP_LIMIT:
                    force_quit = True
                    current_step_inference_log.append(
                        {
                            "role": "handler_log",
                            "content": f"Model has been forced to quit after {MAXIMUM_STEP_LIMIT} steps.",
                        }
                    )

                    break

            # Add to the total list
            all_model_response.append(current_turn_response)
            all_inference_log.append(current_turn_inference_log)
            total_input_token_count.append(current_turn_input_token_count)
            total_output_token_count.append(current_turn_output_token_count)
            total_latency.append(current_turn_latency)

            if not exclude_state_log:
                state_log = []
                for class_name, class_instance in involved_instances.items():
                    if class_name in STATELESS_CLASSES:
                        continue
                    class_instance = deepcopy(class_instance)  # Avoid modification in future turns
                    state_log.append(
                        {
                            "role": "state_info",
                            "class_name": class_name,
                            "content": {
                                key: value
                                for key, value in vars(class_instance).items()
                                if not key.startswith("_")
                            },
                        }
                    )
                all_inference_log.append(state_log)

            if force_quit:
                break

        metadata = {
            "input_token_count": total_input_token_count,
            "output_token_count": total_output_token_count,
            "latency": total_latency,
            "inference_log": all_inference_log,
        }

        return all_model_response, metadata

    @final
    def inference_multi_turn_prompting(
        self, test_entry: dict, include_input_log: bool, exclude_state_log: bool
    ) -> tuple[list[list], dict]:

        initial_config: dict = test_entry["initial_config"]
        involved_classes: list = test_entry["involved_classes"]
        test_entry_id: str = test_entry["id"]
        test_category: str = test_entry_id.rsplit("_", 1)[0]

        # This is only for the miss function category
        # A mapping from turn index to function to holdout
        holdout_function: dict[int, list] = test_entry.get("missed_function", {})

        total_input_token_count: list[list[float]] = []
        total_output_token_count: list[list[float]] = []
        total_latency: list[list[float]] = []
        all_model_response: list[list] = (
            []
        )  # The model response that will be used for later evaluation
        all_inference_log: list[list[dict]] = (
            []
        )  # The debugging log for human to understand
        force_quit = False  # Whether the model has been forced to quit. If True, this whole entry will be failed.

        # Execute no function call, but just to get a reference to all the instances to get the initial state for logging purpose
        if not exclude_state_log:
            _, involved_instances = execute_multi_turn_func_call(
                [],
                initial_config,
                involved_classes,
                self.model_name_underline_replaced,
                test_entry_id,
                long_context=(
                    "long_context" in test_category or "composite" in test_category
                ),
                is_evaL_run=False,
            )
            state_log = []
            for class_name, class_instance in involved_instances.items():
                if class_name in STATELESS_CLASSES:
                    continue
                class_instance = deepcopy(class_instance)  # Avoid modification in future turns
                state_log.append(
                    {
                        "role": "state_info",
                        "class_name": class_name,
                        "content": {
                            key: value
                            for key, value in vars(class_instance).items()
                            if not key.startswith("_")
                        },
                    }
                )
            all_inference_log.append(state_log)

        functions: list = test_entry["function"]
        translator_system_prompt = get_translator_system_prompt(functions)

        # Reasoning call needs englishfied function docs
        #Translator call needs the original JSON function docs
        #functions_english_str = englishfy_tool_definition(functions)
        #functions_english_str = [functions_english_str] # make it a list
        #test_entry["function"] = functions_english_str 

        inference_data: dict = self._pre_query_processing_prompting(test_entry)

        all_multi_turn_messages: list[list[dict]] = test_entry["question"]
        for turn_idx, current_turn_message in enumerate(all_multi_turn_messages):
            current_turn_message: list[dict]

            if str(turn_idx) in holdout_function:
                assert (
                    len(current_turn_message) == 0
                ), "Holdout turn should not have user message."
                current_turn_message = [
                    {
                        "role": "user",
                        "content": DEFAULT_USER_PROMPT_FOR_ADDITIONAL_FUNCTION_PROMPTING.format(
                            functions=holdout_function[str(turn_idx)]
                        ),
                    }
                ]

            #print("######### functions type", type(functions[0]))
            #print("######### function english string", functions_english_str)

            if turn_idx == 0:
                inference_data = self.add_first_turn_message_prompting(
                    inference_data, current_turn_message
                )
            else:
                inference_data = self._add_next_turn_user_message_prompting(
                    inference_data, current_turn_message
                )

            current_turn_response = []
            current_turn_inference_log: list[dict] = {"begin_of_turn_query": current_turn_message}
            current_turn_input_token_count: list[float] = []
            current_turn_output_token_count: list[float] = []
            current_turn_latency: list[float] = []

            count = 0
            while True:
                print("-" * 100)
                print(
                    f"ID: {test_entry_id.replace('multi_turn_', '')}, Turn: {turn_idx}, Step: {count}"
                )
                current_step_inference_log: list[dict] = []
                # Add to the current_turn_inference_log at beginning of each step so that we don't need to bother dealing with the break statements
                current_turn_inference_log[f"step_{count}"] = current_step_inference_log

                #print("######## Kevin reasoning stage input", inference_data)

                api_response, query_latency = self._query_prompting(inference_data)
                
                #print("######## Kevin reasoning stage output", api_response.choices[0].text)
                # translate 
                translator_input = {}
                # messages need to have system role and user role plus content for each
                translator_content_system = {'role': 'system', 'content': translator_system_prompt} 
                translator_content_user = {'role': 'user', 'content': "Function description: " + api_response.choices[0].text} 
                translator_content = [translator_content_system, translator_content_user]
                #print("######## Kevin translator in", translator_content)
                translator_input["message"] = translator_content 
                translator_input["function"] = "" # unused

                api_response, query_latency = self._query_prompting(translator_input)
                #print("######## Kevin translator out", api_response.choices[0].text)

                # This part of logging is disabled by default because it is too verbose and will make the result file extremely large
                # It is only useful to see if the inference pipeline is working as expected (eg, does it convert all the inputs correctly)
                if include_input_log:
                    current_step_inference_log.append(
                        {
                            "role": "inference_input",
                            "content": inference_data.get("inference_input_log", ""),
                        }
                    )

                # Try parsing the model response
                model_response_data = self._parse_query_response_prompting(api_response)
                model_responses = model_response_data["model_responses"]

                # Add the assistant message to the chat history
                inference_data = self._add_assistant_message_prompting(
                    inference_data, model_response_data
                )

                # Process the metadata
                current_turn_input_token_count.append(model_response_data["input_token"])
                current_turn_output_token_count.append(model_response_data["output_token"])
                current_turn_latency.append(query_latency)

                current_turn_response.append(model_responses)
                current_step_inference_log.append(
                    {"role": "assistant", "content": model_responses}
                )

                # Try decoding the model response
                try:
                    decoded_model_responses = self.decode_execute(model_responses)
                    current_step_inference_log.append(
                        {
                            "role": "handler_log",
                            "content": "Successfully decoded model response.",
                            "model_response_decoded": decoded_model_responses,
                        }
                    )

                    model_response_data["model_responses_decoded"] = decoded_model_responses
                    if is_empty_execute_response(decoded_model_responses):
                        print("Empty response from the model. Proceed to next turn.")
                        current_step_inference_log.append(
                            {
                                "role": "handler_log",
                                "content": f"Empty response from the model. Proceed to next turn.",
                                "model_response_decoded": decoded_model_responses,
                            }
                        )
                        break

                except Exception as e:
                    print("Failed to decode the model response. Proceed to next turn.")
                    current_step_inference_log.append(
                        {
                            "role": "handler_log",
                            "content": f"Error decoding the model response. Proceed to next turn.",
                            "error": str(e),
                        }
                    )
                    break

                # Obtain the execution results
                execution_results, involved_instances = execute_multi_turn_func_call(
                    decoded_model_responses,
                    initial_config,
                    involved_classes,
                    self.model_name_underline_replaced,
                    test_entry_id,
                    long_context=(
                        "long_context" in test_category or "composite" in test_category
                    ),
                    is_evaL_run=False,
                )

                # Add the execution results to the chat history for the next turn
                inference_data = self._add_execution_results_prompting(
                    inference_data, execution_results, model_response_data
                )

                for execution_result in execution_results:
                    current_step_inference_log.append(
                        {
                            "role": "tool",
                            "content": execution_result,
                        }
                    )

                count += 1
                # Force quit after too many steps
                if count > MAXIMUM_STEP_LIMIT:
                    force_quit = True
                    current_step_inference_log.append(
                        {
                            "role": "handler_log",
                            "content": f"Model has been forced to quit after {MAXIMUM_STEP_LIMIT} steps.",
                        }
                    )
                    break

            # Add to the total list
            all_model_response.append(current_turn_response)
            all_inference_log.append(current_turn_inference_log)
            total_input_token_count.append(current_turn_input_token_count)
            total_output_token_count.append(current_turn_output_token_count)
            total_latency.append(current_turn_latency)

            if not exclude_state_log:
                state_log = []
                for class_name, class_instance in involved_instances.items():
                    if class_name in STATELESS_CLASSES:
                        continue
                    class_instance = deepcopy(class_instance)  # Avoid modification in future turns
                    state_log.append(
                        {
                            "role": "state_info",
                            "class_name": class_name,
                            "content": {
                                key: value
                                for key, value in vars(class_instance).items()
                                if not key.startswith("_")
                            },
                        }
                    )
                all_inference_log.append(state_log)

            if force_quit:
                break

        metadata = {
            "input_token_count": total_input_token_count,
            "output_token_count": total_output_token_count,
            "latency": total_latency,
            "inference_log": all_inference_log,
        }

        return all_model_response, metadata

    @final
    def inference_single_turn_FC(
        self, test_entry: dict, include_input_log: bool
    ) -> tuple[any, dict]:
        inference_data: dict = {}
        inference_data = self._pre_query_processing_FC(inference_data, test_entry)
        inference_data = self._compile_tools(inference_data, test_entry)
        inference_data = self.add_first_turn_message_FC(
            inference_data, test_entry["question"][0]
        )

        api_response, query_latency = self._query_FC(inference_data)

        # Try parsing the model response
        model_response_data = self._parse_query_response_FC(api_response)

        # Process the metadata
        metadata = {}
        if include_input_log:
            metadata["inference_log"] = [
                {
                    "role": "inference_input",
                    "content": inference_data.get("inference_input_log", ""),
                }
            ]
        metadata["input_token_count"] = model_response_data["input_token"]
        metadata["output_token_count"] = model_response_data["output_token"]
        metadata["latency"] = query_latency

        return model_response_data["model_responses"], metadata

    @final
    def inference_single_turn_prompting(
        self, test_entry: dict, include_input_log: bool
    ) -> tuple[any, dict]:
        inference_data: dict = self._pre_query_processing_prompting(test_entry)

        # get translator system prompt
        functions: list = test_entry["function"]
        translator_system_prompt = get_translator_system_prompt(functions)
        #print("######## Kevin translator system prompt", translator_system_prompt)

        inference_data = self.add_first_turn_message_prompting(
            inference_data, test_entry["question"][0]
        )

        api_response, query_latency = self._query_prompting(inference_data)

        translator_input = {}
        translator_input["function"] = "" # function field is unused for Llama _format_prompt
        # messages need to have system role and user role plus content for each
        translator_content_system = {'role': 'system', 'content': translator_system_prompt} 
        translator_content_user = {'role': 'user', 'content': "Function description: " + api_response.choices[0].text} 
        translator_content = [translator_content_system, translator_content_user]
        #print("######## Kevin translator in", translator_content)
        translator_input["message"] = translator_content 

        # call translator

        api_response, query_latency = self._query_prompting(translator_input)
        #print("######## Kevin translator out", api_response)

        # Try parsing the model response
        model_response_data = self._parse_query_response_prompting(api_response)

        # Process the metadata
        metadata = {}
        if include_input_log:
            metadata["inference_log"] = [
                {
                    "role": "inference_input",
                    "content": inference_data.get("inference_input_log", ""),
                    "translator_content": translator_input.get("inference_input_log", ""),
                }
            ]
        metadata["input_token_count"] = model_response_data["input_token"]
        metadata["output_token_count"] = model_response_data["output_token"]
        metadata["latency"] = query_latency

        return model_response_data["model_responses"], metadata

    def decode_ast(self, result, language="Python"):
        """
        This method takes raw model output (from `_parse_query_response_xxx`) and convert it to standard AST checker input.
        """
        raise NotImplementedError

    def decode_execute(self, result):
        """
        This method takes raw model output (from `_parse_query_response_xxx`) and convert it to standard execute checker input.
        """
        raise NotImplementedError

    @final
    def write(self, result, result_dir, update_mode=False):
        model_name_dir = self.model_name.replace("/", "_")
        model_result_dir = result_dir / model_name_dir
        model_result_dir.mkdir(parents=True, exist_ok=True)

        if isinstance(result, dict):
            result = [result]

        # Collect and format each entry for JSON compatibility
        entries_to_write = [make_json_serializable(entry) for entry in result]

        # Group entries by their `test_category` for efficient file handling
        file_entries = {}
        for entry in entries_to_write:
            test_category = entry["id"].rsplit("_", 1)[0]
            file_name = f"{VERSION_PREFIX}_{test_category}_result.json"
            file_path = model_result_dir / file_name
            file_entries.setdefault(file_path, []).append(entry)

        for file_path, entries in file_entries.items():
            if update_mode:
                # Load existing entries from the file
                existing_entries = {}
                if file_path.exists():
                    existing_entries = {entry["id"]: entry for entry in load_file(file_path)}

                # Update existing entries with new data
                for entry in entries:
                    existing_entries[entry["id"]] = entry

                # Sort entries by `id` and write them back to ensure order consistency
                sorted_entries = sorted(existing_entries.values(), key=sort_key)
                with open(file_path, "w") as f:
                    for entry in sorted_entries:
                        f.write(json.dumps(entry) + "\n")

            else:
                # Normal mode: Append in sorted order
                entries.sort(key=sort_key)
                with open(file_path, "a") as f:
                    for entry in entries:
                        f.write(json.dumps(entry) + "\n")

    #### FC methods ####

    def _query_FC(self, inference_data: dict):
        """
        Call the model API in FC mode to get the response.
        Return the response object that can be used to feed into the `_parse_query_response_FC` method.
        """
        raise NotImplementedError

    def _pre_query_processing_FC(self, inference_data: dict, test_entry: dict) -> dict:
        """
        Preprocess the testset entry before sending it to the model.
        This might includes transforming the input user message into the format expected by the model, extract out the system prompt (if any), and any other necessary preprocessing steps. Those steps can also be done in the `add_first_turn_message_FC` and `_add_next_turn_user_message_FC` methods, but it's usually cleaner to do it here.
        The inference_data dict is updated in place and returned.

        Note: This method has different signature from its Prompting version.
        """
        raise NotImplementedError

    def _compile_tools(self, inference_data: dict, test_entry: dict) -> dict:
        """
        [Only for FC mode]
        This method is used to prepare/compile the tools from the test entry and add them to the inference data to use for model query in FC mode.
        Function docs usually need to be transformed to the format expected by the model, done through the `convert_to_tool` function from `model_handler/utils.py`.
        The inference_data dict is updated in place and returned.
        """
        raise NotImplementedError

    def _parse_query_response_FC(self, api_response: any) -> dict:
        """
        Parses the raw response from the model API to extract the result, input token count, and output token count.

        Args:
            api_response (any): The raw response from the model API.

        Returns:
            A dict containing the following elements:
                - model_responses (any): The parsed result that can be directly used as input to the decode method.
                - input_token (int): The number of tokens used in the input to the model.
                - output_token (int): The number of tokens generated by the model as output.
                - tool_call_ids (list[str]): The IDs of the tool calls that are generated by the model. Optional.
                - Any other metadata that is specific to the model.
        """
        raise NotImplementedError

    def add_first_turn_message_FC(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        """
        Add the first turn message to the chat history, in the format that the model expects.

        Args:
            inference_data (dict): The inference data from previous processing steps.
            first_turn_message (list[dict]): The first turn message from the test entry. It has variable length. It might contain one or more of the following roles:
                - "system": The system message. This role will only appear at most once, at the beginning of the first turn. For most entry, this role will not appear.
                - "user": The user message.
                - "assistant": The assistant message. For most entry, this role will not appear.

        Returns:
            inference_data (dict): The updated inference data that will be send to `_query_FC` to call the model API.
        """
        raise NotImplementedError

    def _add_next_turn_user_message_FC(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        """
        [Only for multi-turn]
        Add next turn user message to the chat history for query.
        user_message is a list of 1 element, which is guaranteed to be a `user` role message.
        """
        raise NotImplementedError

    def _add_assistant_message_FC(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """
        Add assistant message to the chat history.
        """
        raise NotImplementedError

    def _add_execution_results_FC(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        """
        Add the execution results to the chat history to prepare for the next turn of query.
        Some models may need to add additional information to the chat history, such as tool call IDs.
        """
        raise NotImplementedError

    #### Prompting methods ####

    def _query_prompting(self, inference_data: dict):
        """
        Call the model API in prompting mode to get the response.
        Return the response object that can be used to feed into the decode method.
        """
        raise NotImplementedError

    def _pre_query_processing_prompting(self, test_entry: dict) -> dict:
        """
        Preprocess the testset entry before sending it to the model.
        This might includes transforming the input user message into the format expected by the model, extract out the system prompt (if any), and any other necessary preprocessing steps. Those steps can also be done in the `add_first_turn_message_prompting` and `_add_next_turn_user_message_prompting` methods, but it's usually cleaner to do it here.
        The function docs are usually supplied to the prompting models as part of the system prompt, done via the `system_prompt_pre_processing_chat_model` function from `model_handler/utils.py`, unless the model has a different way of handling it.
        Returns a dict that contains all the necessary information for the query method.
        Things like `system_prompt` and `chat_history` are optional, specific to the model.

        Note: This method has different signature from its FC version.
        """
        raise NotImplementedError

    def _parse_query_response_prompting(self, api_response: any) -> dict:
        """
        Parses the raw response from the model API to extract the result, input token count, and output token count.

        Args:
            api_response (any): The raw response from the model API.

        Returns:
            A dict containing the following elements:
                - model_responses (any): The parsed result that can be directly used as input to the decode method.
                - input_token (int): The number of tokens used in the input to the model.
                - output_token (int): The number of tokens generated by the model as output.
                - Any other metadata that is specific to the model.
        """
        raise NotImplementedError

    def add_first_turn_message_prompting(
        self, inference_data: dict, first_turn_message: list[dict]
    ) -> dict:
        """
        Add the first turn message to the chat history, in the format that the model expects.

        Args:
            inference_data (dict): The inference data from previous processing steps.
            first_turn_message (list[dict]): The first turn message from the test entry. It has variable length. It might contain one or more of the following roles:
                - "system": The system message. This role will only appear at most once, at the beginning of the first turn.
                - "user": The user message.
                - "assistant": The assistant message. For most entry, this role will not appear.

        Returns:
            inference_data (dict): The updated inference data that will be send to `_query_prompting` to call the model API.
        """
        raise NotImplementedError

    def _add_next_turn_user_message_prompting(
        self, inference_data: dict, user_message: list[dict]
    ) -> dict:
        """
        [Only for multi-turn]
        Add next turn user message to the chat history for query.
        user_message is a list of 1 element, which is guaranteed to be a `user` role message.
        """
        raise NotImplementedError

    def _add_assistant_message_prompting(
        self, inference_data: dict, model_response_data: dict
    ) -> dict:
        """
        Add assistant message to the chat history.
        """
        raise NotImplementedError

    def _add_execution_results_prompting(
        self, inference_data: dict, execution_results: list[str], model_response_data: dict
    ) -> dict:
        """
        Add the execution results to the chat history to prepare for the next turn of query.
        By default, execution results are added back as a `user` role message, as most models don't support the `tool` role in prompting mode.
        """
        raise NotImplementedError
