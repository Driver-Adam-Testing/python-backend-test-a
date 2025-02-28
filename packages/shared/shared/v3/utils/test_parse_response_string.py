from shared.v3.utils.parse_response_string import parse_response_string

TEST_STRINGS = [
    """Certainly, I'll execute a tool to gather more context about initializing the ADXL355 driver. Let's use the HybridSearchTool to search for specific information about the initialization process.

{
    "search_query": "the correct search query",
    "parseable_class_name": "HybridSearchTool"
}""",
    """Certainly, I'll execute a tool to gather more context about initializing the ADXL355 driver. Let's use the HybridSearchTool to search for specific information about the initialization process.

```{
    "search_query": "the correct search query",
    "parseable_class_name": "HybridSearchTool"
}```""",
    """

{
    "search_query": "the correct search query",
    "parseable_class_name": "HybridSearchTool",
    "extra_field": {
        "extra_field_1": "extra_field_1_value",
        "extra_field_2": "extra_field_2_value"
    }
}randomtext
""",
    """
```json
{
    "search_query": "the correct search query",
    "parseable_class_name": "HybridSearchTool",
    "extra_field": {
        "extra_field_1": "extra_field_1_value",
        "extra_field_2": "extra_field_2_value"
    }
}```
""",
    """
```json
{
    "search_query": "the correct search query",
    "parseable_class_name": "HybridSearchTool",
    "extra_field": {
        "extra_field_1": "extra_field_1_value",
        "extra_field_2": "extra_field_2_value"
    }
}```
```json
{
    "search_query": "the correct search query",
    "parseable_class_name": "HybridSearchTool",
    "extra_field": {
        "extra_field_1": "extra_field_1_value",
        "extra_field_2": "extra_field_2_value"
    }
}```
""",
    """
```json
[{
    "search_query": "the correct search query",
    "parseable_class_name": "HybridSearchTool",
    "extra_field": {
        "extra_field_1": "extra_field_1_value",
        "extra_field_2": "extra_field_2_value"
    }
},
{
    "search_query": "the correct search query",
    "parseable_class_name": "HybridSearchTool",
    "extra_field": {
        "extra_field_1": "extra_field_1_value",
        "extra_field_2": "extra_field_2_value"
    }
}]```
""",
    """```json
{
    "shanes_thoughts": "I'm excited to engage and provide helpful responses!",
    "shanes_action": "Preparing to assist you with any queries you have.",
    "parseable_class_name": "TestWithShaneResponse"
}
```""",
    """
{
    "list_formatted_response": "Based on the information gathered, here's how to configure the communication interface:

1. Identify the communication protocol:
   - Determine if you're using I2C, SPI, or another protocol (e.g., USB CDC ACM).

2. Initialize the interface:
   - For I2C:
     - Use functions like `I2C_Init()` to set up the I2C peripheral.
     - Configure clock frequency, enable interrupts, and set transfer rate.
     - Set up SCL and SDA pins.

   - For SPI:
     - Initialize SPI-specific settings (not detailed in the provided information).

   - For USB CDC ACM:
     - Configure the `comm_interface_descriptor` with appropriate settings.
     - Set interface number, class, subclass, and protocol.
     - Define endpoints for input and output data transmission.

3. Set up device-specific parameters:
   - Use structures like `adt7420_init_param` to hold initialization parameters.
   - Configure the `interface_init` member with either I2C or SPI settings.

4. Initialize the device:
   - Call device-specific initialization functions (e.g., `AD5111_Init()`).
   - Set up necessary GPIO pins and other hardware-specific configurations.

5. Configure additional features (if applicable):
   - For RF transceivers like ADRV9001, set up features such as Digital Pre-Distortion (DPD).
   - Use structures like `adi_adrv9001_DpdInitCfg_t` to configure DPD settings.

6. Set up networking (if required):
   - For applications using networking, initialize network settings.
   - Use functions like `lwip_network_setup()` to configure TCP/IP parameters.

7. Verify initialization:
   - Check return values of initialization functions for success/failure.
   - Implement error handling for unsuccessful configurations.",
    "rationale": "The response is formatted as a numbered list to provide a clear, step-by-step guide for configuring the communication interface. This format makes it easy for users to follow the process sequentially. The steps are organized from general identification of the protocol to specific initialization procedures, device-specific setups, and additional configurations. This structure ensures that users can apply these steps to various communication interfaces and devices while highlighting the importance of proper initialization and error checking.",
    "parseable_class_name": "ListResponse"
}
""",
]


for test_string in TEST_STRINGS:
    try:
        print(parse_response_string(test_string))
    except Exception as e:
        print(f"Error parsing string: {e}")
