from shared.v3.llms.llm import LlmConfig


def test_llm_config_methods():
    # Test default method
    default_config = LlmConfig.default()
    assert isinstance(
        default_config, LlmConfig
    ), "Default config is not an instance of LlmConfig"
    print("Default method test passed.")

    # Test from_name method with a valid model name
    try:
        specific_config = LlmConfig.from_name("gpt_4o")
        assert isinstance(
            specific_config, LlmConfig
        ), "Specific config is not an instance of LlmConfig"
        print("from_name method test with valid model name passed.")
    except ValueError as e:
        print(f"from_name method test with valid model name failed: {e}")

    # Test from_name method with an invalid model name
    try:
        LlmConfig.from_name("invalid_model_name")
        print(
            "from_name method test with invalid model name failed: No exception raised."
        )
    except ValueError:
        print(
            "from_name method test with invalid model name passed: Exception raised as expected."
        )


# Run the tests
test_llm_config_methods()
