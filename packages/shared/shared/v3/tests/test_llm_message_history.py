# import uuid

# import pytest
# from database.db import get_session
# from database.models_v2 import RuntimeLlmMessage, RuntimeLlmMessageHistory
# from database.models import Tag
# from shared.v3 import LlmMessage, LlmMessageHistory, MessageKind


# @pytest.fixture
# def message() -> LlmMessage:
#     return LlmMessage(message_kind=MessageKind.USER, content="Hello, world!")


# @pytest.fixture
# def organization_id() -> str:
#     return "org_123"


# @pytest.fixture
# def user_id() -> str:
#     return "user_123"


# def test_llm_message_to_persistent_llm_message(message: LlmMessage) -> None:
#     persistent_message: RuntimeLlmMessage = message.to_persistent_llm_message()
#     assert persistent_message.llm_message_json == message.model_dump()


# def test_llm_message_history_to_persistent_llm_message_history(
#     message: LlmMessage,
#     organization_id: str,
#     user_id: str,
# ) -> None:
#     message_history = LlmMessageHistory(messages=[message])
#     message_history.save()
#     persistent_message_history: RuntimeLlmMessageHistory = (
#         message_history.to_persistent_llm_message_history()
#     )
#     assert persistent_message_history.id == message_history.id
#     assert persistent_message_history.organization_id == organization_id
#     assert persistent_message_history.user_id == user_id


# def test_llm_message_history_add_message(message: LlmMessage) -> None:
#     message_history = LlmMessageHistory()
#     message_history.add_message(message)
#     assert message_history.messages == [message]


# def test_llm_message_history_to_anthropic() -> None:
#     message_history = LlmMessageHistory(
#         messages=[
#             LlmMessage(content="System1", message_kind=MessageKind.SYSTEM),
#             LlmMessage(content="System2", message_kind=MessageKind.SYSTEM),
#             LlmMessage(content="User query", message_kind=MessageKind.USER),
#             LlmMessage(
#                 content="Assistant response", message_kind=MessageKind.ASSISTANT
#             ),
#         ]
#     )
#     messages, system_message = message_history.to_anthropic()
#     assert system_message == "System1\n\nSystem2"
#     assert messages == [
#         {"role": "user", "content": "User query"},
#         {"role": "assistant", "content": "Assistant response"},
#     ]


# def test_llm_message_history_copy(message: LlmMessage) -> None:
#     original = LlmMessageHistory(messages=[message])
#     copied = original.copy()

#     # Check that it's a different object but with the same content
#     assert original is not copied
#     assert len(original.messages) == len(copied.messages)
#     assert original.messages[0].content == copied.messages[0].content

#     # Verify that modifying the copy doesn't affect the original
#     copied.messages[0].content = "Modified content"
#     assert original.messages[0].content != copied.messages[0].content


# def test_llm_message_history_empty() -> None:
#     history = LlmMessageHistory()
#     assert len(history.messages) == 0

#     # Test that an empty history can be converted to different formats
#     messages, system_message = history.to_anthropic()
#     assert messages == []
#     assert system_message is None


# def test_llm_message_history_with_system_message() -> None:
#     system_message = LlmMessage(
#         content="This is a system message", message_kind=MessageKind.SYSTEM
#     )
#     user_message = LlmMessage(
#         content="This is a user message", message_kind=MessageKind.USER
#     )

#     history = LlmMessageHistory(messages=[system_message, user_message])
#     messages, combined_system = history.to_anthropic()

#     # Check that system message is extracted correctly
#     assert combined_system == "This is a system message"
#     # Check that only the user message is in the regular messages
#     assert len(messages) == 1
#     assert messages[0]["role"] == "user"


# def test_llm_message_history_with_multiple_message_kinds() -> None:
#     messages = [
#         LlmMessage(content="System instruction", message_kind=MessageKind.SYSTEM),
#         LlmMessage(content="User query", message_kind=MessageKind.USER),
#         LlmMessage(content="Assistant response", message_kind=MessageKind.ASSISTANT),
#         LlmMessage(content="Tool call", message_kind=MessageKind.TOOL_CALL_REQUEST),
#         LlmMessage(
#             content="Tool response", message_kind=MessageKind.TOOL_CALL_RESPONSE
#         ),
#     ]

#     history = LlmMessageHistory(messages=messages)

#     # Check total message count
#     assert len(history.messages) == 5

#     # Test conversion to Anthropic format
#     anthropic_messages, system_content = history.to_anthropic()

#     # System message should be separate
#     assert system_content == "System instruction"

#     # Should have 4 regular messages (excluding system)
#     assert len(anthropic_messages) == 4

#     # Check roles are mapped correctly
#     assert anthropic_messages[0]["role"] == "user"  # USER
#     assert anthropic_messages[1]["role"] == "assistant"  # ASSISTANT
#     assert anthropic_messages[2]["role"] == "assistant"  # TOOL_CALL_REQUEST
#     assert anthropic_messages[3]["role"] == "user"  # TOOL_CALL_RESPONSE


# def test_llm_message_history_load(message_history: LlmMessageHistory) -> None:
#     message_history.save()
#     loaded_message_history = LlmMessageHistory.load(message_history.id)
#     assert loaded_message_history.id == message_history.id
#     assert loaded_message_history.messages == message_history.messages


# def test_llm_message_history_complex_save_load(
#     organization_id: str, user_id: str
# ) -> None:
#     """Test saving and loading a complex message history with multiple message types."""
#     # Create a complex message history with various message kinds
#     complex_messages = [
#         LlmMessage(content="System instruction 1", message_kind=MessageKind.SYSTEM),
#         LlmMessage(
#             content="Parsing description", message_kind=MessageKind.PARSING_DESCRIPTION
#         ),
#         LlmMessage(content="Initial user query", message_kind=MessageKind.USER),
#         LlmMessage(
#             content="First assistant response", message_kind=MessageKind.ASSISTANT
#         ),
#         LlmMessage(content="Developer message", message_kind=MessageKind.DEVELOPER),
#         LlmMessage(
#             content="Tool call request 1", message_kind=MessageKind.TOOL_CALL_REQUEST
#         ),
#         LlmMessage(
#             content="Tool call response 1", message_kind=MessageKind.TOOL_CALL_RESPONSE
#         ),
#         LlmMessage(
#             content="Second assistant response", message_kind=MessageKind.ASSISTANT
#         ),
#         LlmMessage(content="Iteration message", message_kind=MessageKind.ITERATION),
#         LlmMessage(content="Follow-up question", message_kind=MessageKind.USER),
#         LlmMessage(content="System instruction 2", message_kind=MessageKind.SYSTEM),
#         LlmMessage(content="Final response", message_kind=MessageKind.ASSISTANT),
#     ]

#     # Create the message history
#     complex_history = LlmMessageHistory(
#         messages=complex_messages,
#         organization_id=organization_id,
#         user_id=user_id,
#     )

#     # Save the message history
#     complex_history.save()

#     # Load the message history
#     loaded_history = LlmMessageHistory.load(complex_history.id)

#     # Assert that the loaded history has the same ID
#     assert loaded_history.id == complex_history.id

#     # Assert that all messages are preserved
#     assert len(loaded_history.messages) == len(complex_messages)

#     # Verify each message was preserved correctly
#     for i, original_message in enumerate(complex_messages):
#         loaded_message = loaded_history.messages[i]
#         assert loaded_message.content == original_message.content
#         assert loaded_message.message_kind == original_message.message_kind

#     # Verify the conversion to Anthropic format still works correctly
#     anthropic_messages, system_content = loaded_history.to_anthropic()

#     # Check that system messages are combined properly
#     assert "System instruction 1" in system_content
#     assert "Parsing description" in system_content
#     assert "System instruction 2" in system_content
