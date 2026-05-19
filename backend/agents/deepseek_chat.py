"""DeepSeek Chat 兼容层 — 处理 reasoning_content"""
from typing import Any, Dict, Optional, Union

import openai
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ChatMessage,
    FunctionMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_openai.chat_models.base import BaseChatOpenAI

# 保存原始的函数引用
_original_convert_message_to_dict = None
_original_convert_delta = None


def _patched_convert_message_to_dict(message: BaseMessage) -> dict:
    """在原始函数基础上增加 reasoning_content 传递"""
    from langchain_openai.chat_models.base import (
        _format_message_content,
        _lc_invalid_tool_call_to_openai_tool_call,
        _lc_tool_call_to_openai_tool_call,
    )

    message_dict: Dict[str, Any] = {"content": _format_message_content(message.content)}
    if (name := message.name or message.additional_kwargs.get("name")) is not None:
        message_dict["name"] = name

    if isinstance(message, ChatMessage):
        message_dict["role"] = message.role
    elif isinstance(message, HumanMessage):
        message_dict["role"] = "user"
    elif isinstance(message, AIMessage):
        message_dict["role"] = "assistant"

        # === DeepSeek 兼容：传递 reasoning_content ===
        if "reasoning_content" in message.additional_kwargs:
            message_dict["reasoning_content"] = message.additional_kwargs[
                "reasoning_content"
            ]

        if "function_call" in message.additional_kwargs:
            message_dict["function_call"] = message.additional_kwargs["function_call"]
        if message.tool_calls or message.invalid_tool_calls:
            message_dict["tool_calls"] = [
                _lc_tool_call_to_openai_tool_call(tc) for tc in message.tool_calls
            ] + [
                _lc_invalid_tool_call_to_openai_tool_call(tc)
                for tc in message.invalid_tool_calls
            ]
        elif "tool_calls" in message.additional_kwargs:
            message_dict["tool_calls"] = message.additional_kwargs["tool_calls"]
            tool_call_supported_props = {"id", "type", "function"}
            message_dict["tool_calls"] = [
                {k: v for k, v in tool_call.items() if k in tool_call_supported_props}
                for tool_call in message_dict["tool_calls"]
            ]
        else:
            pass
        if "function_call" in message_dict or "tool_calls" in message_dict:
            message_dict["content"] = message_dict["content"] or None
    elif isinstance(message, SystemMessage):
        message_dict["role"] = "system"
    elif isinstance(message, FunctionMessage):
        message_dict["role"] = "function"
    elif isinstance(message, ToolMessage):
        message_dict["role"] = "tool"
        message_dict["tool_call_id"] = message.tool_call_id

        supported_props = {"content", "role", "tool_call_id"}
        message_dict = {k: v for k, v in message_dict.items() if k in supported_props}
    else:
        raise TypeError(f"Got unknown type {message}")
    return message_dict


def patch_langchain_openai():
    """Monkey-patch LangChain OpenAI 模块以支持 DeepSeek reasoning_content"""
    import langchain_openai.chat_models.base as base

    global _original_convert_message_to_dict
    if _original_convert_message_to_dict is None:
        _original_convert_message_to_dict = base._convert_message_to_dict
    base._convert_message_to_dict = _patched_convert_message_to_dict


class DeepSeekChat(BaseChatOpenAI):
    """兼容 DeepSeek reasoning 模型的 ChatOpenAI 子类"""

    def _create_chat_result(
        self,
        response: Union[dict, openai.BaseModel],
        generation_info: Optional[Dict] = None,
    ) -> ChatResult:
        from langchain_openai.chat_models.base import _convert_dict_to_message

        generations = []

        response_dict = (
            response if isinstance(response, dict) else response.model_dump()
        )
        if response_dict.get("error"):
            raise ValueError(response_dict.get("error"))

        token_usage = response_dict.get("usage", {})
        for res in response_dict["choices"]:
            message = _convert_dict_to_message(res["message"])

            # === DeepSeek 兼容：提取 reasoning_content ===
            msg_dict = res.get("message", {})
            if isinstance(msg_dict, dict) and "reasoning_content" in msg_dict:
                if isinstance(message, AIMessage):
                    message.additional_kwargs["reasoning_content"] = msg_dict[
                        "reasoning_content"
                    ]

            if token_usage and isinstance(message, AIMessage):
                message.usage_metadata = {
                    "input_tokens": token_usage.get("prompt_tokens", 0),
                    "output_tokens": token_usage.get("completion_tokens", 0),
                    "total_tokens": token_usage.get("total_tokens", 0),
                }
            generation_info = generation_info or {}
            generation_info["finish_reason"] = (
                res.get("finish_reason")
                if res.get("finish_reason") is not None
                else generation_info.get("finish_reason")
            )
            if "logprobs" in res:
                generation_info["logprobs"] = res["logprobs"]
            gen = ChatGeneration(message=message, generation_info=generation_info)
            generations.append(gen)
        llm_output = {
            "token_usage": token_usage,
            "model_name": response_dict.get("model", self.model_name),
            "system_fingerprint": response_dict.get("system_fingerprint", ""),
        }

        if isinstance(response, openai.BaseModel) and getattr(
            response, "choices", None
        ):
            message = response.choices[0].message
            if hasattr(message, "parsed"):
                generations[0].message.additional_kwargs["parsed"] = message.parsed
            if hasattr(message, "refusal"):
                generations[0].message.additional_kwargs["refusal"] = message.refusal
            # === DeepSeek 兼容：从 Pydantic model 提取 reasoning_content ===
            if hasattr(message, "reasoning_content") and message.reasoning_content:
                generations[0].message.additional_kwargs[
                    "reasoning_content"
                ] = message.reasoning_content

        return ChatResult(generations=generations, llm_output=llm_output)


def _patched_convert_delta_to_message_chunk(_dict, default_class):
    """在原始函数基础上增加 reasoning_content 提取"""
    global _original_convert_delta
    result = _original_convert_delta(_dict, default_class)

    # === DeepSeek 兼容：提取 reasoning_content ===
    if "reasoning_content" in _dict and hasattr(result, "additional_kwargs"):
        rc = _dict["reasoning_content"]
        if rc:
            result.additional_kwargs["reasoning_content"] = (
                result.additional_kwargs.get("reasoning_content", "") + rc
            )

    return result


def patch_langchain_delta():
    """Monkey-patch 流式 chunk 转换函数"""
    import langchain_openai.chat_models.base as base

    global _original_convert_delta
    if _original_convert_delta is None:
        _original_convert_delta = base._convert_delta_to_message_chunk
    base._convert_delta_to_message_chunk = _patched_convert_delta_to_message_chunk


# 自动应用 patch
patch_langchain_openai()
patch_langchain_delta()
