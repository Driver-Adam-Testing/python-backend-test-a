import concurrent.futures
import time

from prettytable import PrettyTable
from shared.interfaces.agents.data_scope import DataScope
from shared.v3.llms.clients.llm_client import LlmClient
from shared.v3.pipelines.smart_instruction import run_smart_instruction

BEFORE = [
    "",
    "",
    "ADXL355 No-OS Driver Setup: Communication Protocols (SPI/I2C): Determine communication type at initialization: Use ADXL355_SPI_COMM or ADXL355_I2C_COMM in adxl355_init_param. SPI Communication: Initialize using no_os_spi_init. Employ commands ADXL355_SPI_READ and ADXL355_SPI_WRITE. I2C Communication: Initialize using no_os_i2c_init. GPIO Requirements: SPI requires SCK, MOSI, MISO, and CS lines. I2C requires SDA and SCL lines. Initial API Calls: Initialize Device: Use adxl355_init. Configures communication and checks readiness. Set Measurement Range: Use adxl355_set_range. Configure Filters (Optional): Use adxl355_set_odr_lpf for output data rate and low-pass filter. Use adxl355_set_hpf_corner for high-pass filter settings. Relevant Setup Parameters: adxl355_init_param contains communication and device type details. Set device mode with adxl355_set_op_mode. Initialize range and power settings at start-up. Error Checking Procedures: Compare received data with known reset values using GET_ADXL355_RESET_VAL. Verify device ID and status post-initialization. Common error codes: -EINVAL: Invalid parameters. -ENOMEM: Memory allocation issues. -EAGAIN: Retry required operation. API Utilization Checklist: Initialize Communication: adxl355_init_param init; init.comm_type = ADXL355_SPI_COMM; // or ADXL355_I2C_COMM adxl355_init(&device, init); Set Range: adxl355_set_range(device, ADXL355_RANGE_4G); Set Filters (Optional): adxl355_set_odr_lpf(device, ADXL355_ODR_500HZ); adxl355_set_hpf_corner(device, ADXL355_HPF_0_0238); Ensure hardware pin configurations match the selected protocol for successful implementation. ADXL355 Driver: Key Details and Configuration",
]
AFTER = [
    "",
    "",
    "   Key Register Descriptions Device ID Registers: ADXL355_DEVID_AD (0x00) - Analog Devices ID. ADXL355_DEVID_MST (0x01) - Master ID. ADXL355_PARTID (0x02) - Model ID (0xED for ADXL355). Status Register: ADXL355_STATUS (0x04) - Data Ready, FIFO Full, FIFO Overrun flags. Data Registers: ADXL355_TEMP (0x06) - Temperature data. ADXL355_XDATA, ADXL355_YDATA, ADXL355_ZDATA (0x08-0x0E) - Acceleration data for X, Y, Z axes. Control Registers: ADXL355_RANGE (0x2C) - Measurement range setting. ADXL355_POWER_CTL (0x2D) - Power modes and operation control. ADXL355_INT_MAP (0x2A) - Interrupt pin mapping. Configuration Sequences Initialization: Initialize communication peripherals (SPI/I2C). Verify device presence and model by reading Device IDs. Set and retrieve shadow register values. Important Register Settings Range Settings: Use ADXL355_RANGE to switch between 2g, 4g, 8g ranges. Power Control: Configure operating modes using ADXL355_POWER_CTL. Default Register Values On reset, registers like ADXL355_DEVID_AD return specific default values (e.g., 0xAD). Bit Field Descriptions Status Register Flags: DATA_RDY, FIFO_FULL, FIFO_OVR for data status. NVM_BUSY for non-volatile memory operation status. Data Acquisition Measurement Procedures: Acquire raw data for each axis (X, Y, Z) using adxl355_get_raw_xyz(). Convert to g units with adxl355_get_xyz(), factoring in the device's scale setting. Data Formats: Raw data comes as 20-bit values in 24-bit registers. Use adxl355_accel_array_conv() to convert to a readable format. Conversion Factors: Physical unit conversion is done using the scale factors ADXL355_ACC_SCALE_FACTOR_MUL and ADXL355_ACC_SCALE_FACTOR_DIV, based on the range (±2g, ±4g, ±8g). Control Operations Device State Management: Initialize the device with adxl355_init(), which sets it to a default state, confirms communication setup, and hardware presence. Supported Operating Modes and Configurations: Manage operating mode through adxl355_set_op_mode() to choose between standby and measurement modes. Error Handling Mechanisms: Functions return error codes for issues like communication failure. Use adxl355_get_sts_reg() to check register statuses, including NVM_BUSY and FIFO_OVR. Operation Modes Overview of Available Modes: Modes include standby, measurement (with/without temperature data), accessible via adxl355_get_op_mode(). Detailed Mode Configuration Guidelines: Mode configuration involves writing to the POWER_CTL register, detailed in adxl355_set_op_mode(). Transition Procedures for Mode Switching: Use adxl355_set_op_mode() to change modes, ensuring the device isn't measuring data during significant changes, especially filter settings. Structure Definitions The adxl355_dev structure is essential for ADXL355 operation. It holds parameters and settings necessary for communication and management. struct adxl355_dev {\n    enum adxl355_type dev_type;\n    union adxl355_comm_desc com_desc;\n    enum adxl355_comm_type comm_type;\n    enum adxl355_op_mode op_mode;\n    enum adxl355_odr_lpf odr_lpf;\n    enum adxl355_hpf_corner hpf_corner;\n    enum adxl355_range range;\n    uint16_t x_offset;\n    uint16_t y_offset;\n    uint16_t z_offset;\n    uint8_t fifo_samples;\n    union adxl355_act_en_flags act_en;\n    uint8_t act_cnt;\n    uint16_t act_thr;\n    uint8_t comm_buff[289];\n};\n Fields include: Device type (dev_type) Communication descriptor (com_desc) Communication type (comm_type) Operational mode (op_mode) Range and filter configurations (range, odr_lpf, hpf_corner) Calibration offsets (x_offset, y_offset, z_offset) FIFO configuration (fifo_samples) Activity settings (act_en, act_cnt, act_thr) Communication buffer (comm_buff) Parameter Setup To initialize, set up the device's communication parameters and specific settings. Example: int adxl355_init(struct adxl355_dev **device, struct adxl355_init_param init_param) {\n    struct adxl355_dev *dev;\n    int ret;\n    uint8_t reg_value;\n\n    switch (init_param.dev_type) {\n    case ID_ADXL355:\n    case ID_ADXL357:\n    case ID_ADXL359:\n        break;\n    default:\n        return -EINVAL;\n    }\n\n    dev = (struct adxl355_dev *)no_os_calloc(1, sizeof(*dev));\n    if (!dev)\n        return -ENOMEM;\n\n    dev->comm_type = init_param.comm_type;\n    \n    if (dev->comm_type == ADXL355_SPI_COMM) {\n        ret = no_os_spi_init(&dev->com_desc.spi_desc, &(init_param.comm_init.spi_init));\n        if (ret)\n            goto error_dev;\n    } else {\n        ret = no_os_i2c_init(&dev->com_desc.i2c_desc, &init_param.comm_init.i2c_init);\n        if (ret)\n            goto error_dev;\n    }\n\n    dev->dev_type = init_param.dev_type;\n\n    ret = adxl355_read_device_data(dev, ADXL355_ADDR(ADXL355_DEVID_AD),\n                                   GET_ADXL355_TRANSF_LEN(ADXL355_DEVID_AD), ®_value);\n    if (ret || (reg_value != GET_ADXL355_RESET_VAL(ADXL355_DEVID_AD)))\n        goto error_com;\n\n    *device = dev;\n    return 0;\n\nerror_com:\n    if (dev->comm_type == ADXL355_SPI_COMM)\n        no_os_spi_remove(dev->com_desc.spi_desc);\n    else\n        no_os_i2c_remove(dev->com_desc.i2c_desc);\n    no_os_free(dev);\n    return -EIO;\n\nerror_dev:\n    no_os_free(dev);\n    return ret;\n}\n Error Handling Error handling is implemented by returning error codes and cleaning up resources: Memory Allocation Failure: Return -ENOMEM. Communication Initialization Failure: Clean up communication resources. Device ID Verification: Confirm device presence and return error if invalid. This setup ensures reliable initialization and resource management for the ADXL355 accelerometer. #include \"adxl355.h\"\n\n// Function to read data from the ADXL355 sensor\nint read_accel_data(struct adxl355_dev *dev, uint32_t *x, uint32_t *y, uint32_t *z) {\n    uint32_t raw_x, raw_y, raw_z;\n    int ret = adxl355_get_raw_xyz(dev, &raw_x, &raw_y, &raw_z);\n    \n    if (ret == 0) {\n        *x = raw_x;\n        *y = raw_y;\n        *z = raw_z;\n    }\n    \n    return ret;\n}\n\n// Function to write configuration data to the ADXL355 sensor\nint write_config_data(struct adxl355_dev *dev, uint8_t reg, uint8_t value) {\n    return adxl355_write_device_data(dev, reg, 1, &value);\n}\n\n// Function to configure the ADXL355 sensor range\nint configure_range(struct adxl355_dev *dev, enum adxl355_range range) {\n    return adxl355_set_range(dev, range);\n}\n\n// Function to switch the ADXL355 sensor mode\nint switch_mode(struct adxl355_dev *dev, enum adxl355_op_mode mode) {\n    return adxl355_set_op_mode(dev, mode);\n}\n These code snippets use the ADXL355 no-OS driver to demonstrate reading data, writing configuration, configuring the sensor range, and switching operation modes. For further implementation details, refer to adxl355.c and adxl355.h. Error Checking Error checking ensures operations like reading, writing, and initialization proceed correctly. The following function demonstrates error handling: int adxl355_read_device_data(struct adxl355_dev *dev, uint8_t base_address,\n                             uint16_t size, uint8_t *read_data) {\n    int ret;\n\n    if (dev->comm_type == ADXL355_SPI_COMM) {\n        dev->comm_buff[0] = ADXL355_SPI_READ | (base_address << 1);\n        ret = no_os_spi_write_and_read(dev->com_desc.spi_desc, dev->comm_buff, 1 + size);\n        for (uint16_t idx = 0; idx < size; idx++)\n            read_data[idx] = dev->comm_buff[idx+1];\n    } else {\n        ret = no_os_i2c_write(dev->com_desc.i2c_desc, &base_address, 1, 0);\n        if (ret)\n            return ret;\n        ret = no_os_i2c_read(dev->com_desc.i2c_desc, read_data, size, 1);\n    }\n\n    return ret;\n}\n Each communication operation checks the ret variable to handle errors effectively. Recovery Procedures The adxl355_init function executes recovery procedures for error conditions, preventing resource leaks through appropriate cleanup actions: int adxl355_init(struct adxl355_dev **device,\n                 struct adxl355_init_param init_param) {\n    struct adxl355_dev *dev;\n    int ret;\n    uint8_t reg_value;\n\n    switch (init_param.dev_type) {\n    case ID_ADXL355:\n    case ID_ADXL357:\n    case ID_ADXL359:\n        break;\n    default:\n        return -EINVAL;\n    }\n\n    dev = (struct adxl355_dev *)no_os_calloc(1, sizeof(*dev));\n    if (!dev)\n        return -ENOMEM;\n\n    dev->comm_type = init_param.comm_type;\n\n    ret = (dev->comm_type == ADXL355_SPI_COMM) ?\n          no_os_spi_init(&dev->com_desc.spi_desc, &(init_param.comm_init.spi_init)) :\n          no_os_i2c_init(&dev->com_desc.i2c_desc, &init_param.comm_init.i2c_init);\n    if (ret)\n        goto error_dev;\n\n    ret = adxl355_read_device_data(dev, ADXL355_ADDR(ADXL355_DEVID_AD),\n                                   GET_ADXL355_TRANSF_LEN(ADXL355_DEVID_AD), ®_value);\n    if (ret || (reg_value != GET_ADXL355_RESET_VAL(ADXL355_DEVID_AD)))\n        goto error_com;\n\n    *device = dev;\n    return 0;\n\nerror_com:\n    if (dev->comm_type == ADXL355_SPI_COMM)\n        no_os_spi_remove(dev->com_desc.spi_desc);\n    else\n        no_os_i2c_remove(dev->com_desc.i2c_desc);\n    no_os_free(dev);\n    return -1;\n\nerror_dev:\n    no_os_free(dev);\n    return ret;\n}\n Resource Cleanup The adxl355_remove function ensures resource cleanup, preventing memory leaks: int adxl355_remove(struct adxl355_dev *dev) {\n    int ret;\n\n    if (dev->comm_type == ADXL355_SPI_COMM)\n        ret = no_os_spi_remove(dev->com_desc.spi_desc);\n    else\n        ret = no_os_i2c_remove(dev->com_desc.i2c_desc);\n\n    no_os_free(dev);\n\n    return ret;\n}\n This function releases device resources by freeing communication descriptors and the device.",
]
PROMPTS = [
    "What are the Interrupt setup procedures\n- Available interrupt types\n- Handler configuration\n- Priority settings\n- Interrupt vectors",
    "How do you initialize the ADXL355 driver?",
    "What are the key features of the ADXL355 accelerometer?",
    "How do you configure the communication interface?",
    "What are the steps to set the measurement range?",
    "How do you handle errors during ADXL355 initialization?",
    "What are the default register values?",
    "How do you read acceleration data from the ADXL355?",
    "What are the power modes available?",
    "How do you configure the filters on the ADXL355?",
    "What are the key components of the adxl355_dev structure?",
]


def inject_pipeline_requests() -> list[dict]:
    pipeline_requests = []
    for _ in range(5):
        import random

        pipeline_requests.append(
            {
                "prompt": random.choice(PROMPTS),
                "node_ids": ["bce8a419-4cd4-4717-8d20-08b92ee97c29"],
                "steps": [],
                "block_kind": "ANY",
                "context": {
                    "selected_text": "",
                    "before_selected_text": random.choice(BEFORE),
                    "after_selected_text": random.choice(AFTER),
                },
            }
        )
    return pipeline_requests


def run_and_time_pipeline() -> None:
    pipeline_requests = inject_pipeline_requests()
    client_timings = {}

    def process_request(request: dict, client: LlmClient) -> float:
        start_time = time.time()
        response = run_smart_instruction(
            user_prompt=request["prompt"],
            text_before_instruction=request["context"]["before_selected_text"],
            text_after_instruction=request["context"]["after_selected_text"],
            datascope=DataScope(
                node_ids=request["node_ids"],
                organization_id="org_s76pU1v8LAYhTOWB",
                user_id="org_s76pU1v8LAYhTOWB",
            ),
        )
        print(f"\033[38;5;82mTime taken: {time.time() - start_time}\033[0m")
        print(f"\033[38;5;214mClient: {client.config.model_name}\033[0m")
        print(f"\033[38;5;45mRequest: {request['prompt']}\033[0m")
        print(f"\033[38;5;196mResponse: {response['final_response']}\033[0m")
        total_references = len(response["references"])
        top_references = response["references"][:5]
        for idx, reference in enumerate(top_references, start=1):
            print(f"\033[38;5;82mReference {idx}:\033[0m")
            print(f"  Content: {reference.content[:100]} ...")
            print(f"  Score: {reference.score}")
            print(f"  Version Display Name: {reference.version_display_name}")
            print(f"  Relative Path: {reference.relative_path}")
            print(f"  Version ID: {reference.version_id}")
            print(f"  Node ID: {reference.node_id}")
            print(f"  Metadata: {reference.metadata}")
        print(f"\033[38;5;82mTotal References: {total_references}\033[0m")

        end_time = time.time()
        return end_time - start_time

    llm_clients = [
        LlmClient.gpt_4o(),
        LlmClient.gpt_4o_mini(),
        LlmClient.gpt_4o_mini_chat(),
        LlmClient.o1(),
        LlmClient.o1_mini(),
        LlmClient.o3_mini(),
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(process_request, request, client): (request, client)
            for request in pipeline_requests
            for client in llm_clients
        }
        for future in concurrent.futures.as_completed(futures):
            request, client = futures[future]
            client_id = client.config.model_name
            time_taken = future.result()
            if client_id not in client_timings:
                client_timings[client_id] = []
            client_timings[client_id].append(time_taken)

    table = PrettyTable()
    table.field_names = ["Client ID", "Best Time", "Average Time", "Worst Time"]

    for client_id, times in client_timings.items():
        best_time = round(min(times), 2)
        worst_time = round(max(times), 2)
        average_time = round(sum(times) / len(times), 2)
        table.add_row([client_id, best_time, average_time, worst_time])

    print(table)


if __name__ == "__main__":
    run_and_time_pipeline()

"""
Performance of the pipeline:
+------------------+-----------+--------------+------------+
|    Client ID     | Best Time | Average Time | Worst Time |
+------------------+-----------+--------------+------------+
|      gpt_4o      |   22.71   |    25.19     |   30.22    |
| gpt_4o_mini_chat |   24.08   |    32.36     |    47.0    |
|        o1        |   24.18   |    29.89     |   38.17    |
|   gpt_4o_mini    |   21.76   |    26.34     |   33.61    |
|     o1_mini      |   24.13   |    27.06     |   30.96    |
|     o3_mini      |   19.58   |    24.14     |   30.49    |
+------------------+-----------+--------------+------------+
"""
