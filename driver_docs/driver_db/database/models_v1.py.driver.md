# Purpose
This Python source code file defines a set of SQLAlchemy ORM models using the SQLModel library, which is an extension of SQLAlchemy designed to simplify the creation of database models. The file is structured to represent various entities and their relationships within a database, likely for a web application or service. The models include `RuntimeLogAgentInstance`, `RuntimeLogAgentMessage`, `DocumentSource`, `DerivedContent`, `Tag`, `ChunkAndEmbedding`, `InspectorRun`, `UsageSession`, `UsageEvent`, `GithubAppInstallation`, `Subscription`, `GitProviderApp`, and `GitProviderAppInstallation`. Each class corresponds to a database table, with fields representing columns and relationships defining associations between tables. The code also includes several enumerations to define specific types and statuses, such as `Enum_Derived_Content_Status`, `UsageSessionStatus`, `UsageEventType`, `PlanType`, `BillingFrequency`, `SubscriptionStatus`, and `GitProviderKind`.

The primary purpose of this file is to define the schema and relationships for a database that supports functionalities related to logging, content management, usage tracking, subscription management, and integration with external services like GitHub and GitLab. The models are equipped with fields for timestamps, unique identifiers, and various metadata, ensuring that the database can efficiently store and retrieve information. Additionally, the file includes event listeners to update timestamps and maintain data integrity across related tables. This code is intended to be part of a larger application, serving as a foundational component for database interactions and providing a structured way to manage and query data.
# Imports and Dependencies

---
- `enum`
- `uuid`
- `datetime`
- `Any`
- `UUID`
- `sqlalchemy.dialects.postgresql`
- `strawberry`
- `pgvector.sqlalchemy.Vector`
- `sqlalchemy.Column`
- `sqlalchemy.Computed`
- `sqlalchemy.Connection`
- `sqlalchemy.DateTime`
- `sqlalchemy.Index`
- `sqlalchemy.Integer`
- `sqlalchemy.String`
- `sqlalchemy.UniqueConstraint`
- `sqlalchemy.event`
- `sqlalchemy.func`
- `sqlalchemy.text`
- `sqlalchemy.update`
- `sqlalchemy.dialects.postgresql.JSONB`
- `sqlalchemy.dialects.postgresql.UUID`
- `sqlalchemy.orm.Mapper`
- `sqlmodel.JSON`
- `sqlmodel.Field`
- `sqlmodel.Relationship`
- `sqlmodel.SQLModel`
- `sqlmodel.select`
- `.custom_types.TSVector`
- `.models_v2.Node`
- `.models_v2.PrimaryAsset`
- `.models_v2.Version`
- `.models_v2_enums.ContentKind`


# Global Variables

---
### ACTIVE 
- **Type**: `str`
- **Description**: `ACTIVE` is a string constant representing the status of a subscription in the system. It indicates that the subscription is currently active and operational.
- **Use**: This variable is used to set or check the status of a subscription within the application.


---
### ADDITIONAL_PLATFORM_USAGE_CREDIT 
- **Type**: `str`
- **Description**: `ADDITIONAL_PLATFORM_USAGE_CREDIT` is an enumeration value within the `UsageEventType` class, representing a specific type of usage credit that can be applied to a user's account. It is part of a broader set of usage event types that track various usage metrics and credits associated with platform services.
- **Use**: This variable is used to categorize and identify events related to additional platform usage credits in the system.


---
### ADVANCED 
- **Type**: `str`
- **Description**: The `ADVANCED` variable is an enumeration value representing a subscription plan type in the system. It is part of the `PlanType` enum, which categorizes different subscription levels such as 'core', 'advanced', and 'enterprise'.
- **Use**: This variable is used to specify the subscription plan type for users in the application.


---
### AGENT_PIPELINE_USAGE_DEBIT 
- **Type**: `enum.IntEnum`
- **Description**: `AGENT_PIPELINE_USAGE_DEBIT` is a member of the `UsageEventType` enumeration, representing a specific type of usage event related to the agent pipeline. It is assigned the integer value of 1, which is used to categorize and track usage events in the system.
- **Use**: This variable is used to identify and log usage events specifically associated with agent pipeline operations.


---
### ANNUAL 
- **Type**: `str`
- **Description**: `ANNUAL` is a member of the `BillingFrequency` enum class, representing a billing frequency option for subscriptions. It is used to indicate that a subscription is billed on an annual basis.
- **Use**: This variable is used to define the billing frequency for subscriptions in the system.


---
### BASE_PLATFORM_USAGE_CREDIT 
- **Type**: `string`
- **Description**: The `BASE_PLATFORM_USAGE_CREDIT` is an enumeration value within the `UsageEventType` enum, representing a specific type of usage credit that can be applied to a user's account on the platform. This credit type is part of a broader system that tracks various usage events and their corresponding financial implications.
- **Use**: It is used to categorize and identify events related to credits granted for base platform usage in the application's usage tracking system.


---
### CANCELED 
- **Type**: `str`
- **Description**: `CANCELED` is a string constant representing the status of a subscription that has been canceled. It is part of the `SubscriptionStatus` enumeration, which defines various states a subscription can be in.
- **Use**: This variable is used to indicate the cancellation status of a subscription in the system.


---
### COMPLETED 
- **Type**: `str`
- **Description**: `COMPLETED` is a member of the `UsageSessionStatus` enumeration, representing the state of a usage session that has finished its execution. It is one of the possible statuses that can be assigned to a `UsageSession`, indicating that the session has successfully completed its intended operations.
- **Use**: This variable is used to define the status of a usage session in the `UsageSession` class.


---
### CORE 
- **Type**: `str`
- **Description**: `CORE` is an enumeration value representing the core subscription plan type in the application. It is part of the `PlanType` enum, which defines different subscription plans available to users.
- **Use**: This variable is used to specify the plan type for subscriptions in the application.


---
### ENTERPRISE 
- **Type**: `str`
- **Description**: `ENTERPRISE` is a member of the `PlanType` enumeration, representing a specific subscription plan type within the application. It is used to categorize and manage different subscription levels offered to users.
- **Use**: This variable is used to identify the 'enterprise' plan type in subscription-related functionalities.


---
### FAILED 
- **Type**: `str`
- **Description**: `FAILED` is a member of the `UsageSessionStatus` enumeration, representing a state in which a usage session has failed. This enum is used to track the status of various usage sessions within the application.
- **Use**: It is used to indicate the failure status of a `UsageSession` instance.


---
### GITLAB_ENTERPRISE_SELF_MANAGED 
- **Type**: `str`
- **Description**: `GITLAB_ENTERPRISE_SELF_MANAGED` is an enumeration value representing a specific type of Git provider, specifically for self-managed instances of GitLab Enterprise. It is part of the `GitProviderKind` enum, which categorizes different types of Git providers used in the application.
- **Use**: This variable is used to identify and differentiate self-managed GitLab Enterprise instances within the application.


---
### INSPECTOR_CODE_DIFF_USAGE_DEBIT 
- **Type**: `enum.IntEnum`
- **Description**: `INSPECTOR_CODE_DIFF_USAGE_DEBIT` is a member of the `UsageEventType` enumeration, representing a specific type of usage event related to code differences inspected by the system. It is assigned the integer value of 3, which is used to categorize and track usage events in the application.
- **Use**: This variable is used to identify and log events related to the inspection of code differences in the usage event tracking system.


---
### INSPECTOR_TECH_DOC_USAGE_DEBIT 
- **Type**: `enum.IntEnum`
- **Description**: `INSPECTOR_TECH_DOC_USAGE_DEBIT` is an enumeration value representing a specific type of usage event related to the inspector's technical documentation. It is part of the `UsageEventType` enum, which categorizes various usage events for tracking and billing purposes.
- **Use**: This variable is used to identify and categorize usage events specifically associated with technical documentation in the system.


---
### MONTHLY 
- **Type**: `str`
- **Description**: `MONTHLY` is a member of the `BillingFrequency` enumeration, representing a billing cycle that occurs every month. It is used to define the frequency of billing for subscriptions in the application.
- **Use**: This variable is utilized to specify the billing frequency for subscription plans.


---
### ONBOARDING_USAGE_DEBIT 
- **Type**: `enum.IntEnum`
- **Description**: `ONBOARDING_USAGE_DEBIT` is a member of the `UsageEventType` enumeration, representing a specific type of usage event related to onboarding activities. It is assigned the integer value of 4, which distinguishes it from other usage event types defined in the same enumeration.
- **Use**: This variable is used to categorize and identify onboarding-related usage events within the application.


---
### RUNNING 
- **Type**: `str`
- **Description**: `RUNNING` is a constant string value defined in the `UsageSessionStatus` enumeration, representing the current state of a usage session. It indicates that the session is actively in progress and has not yet completed or failed.
- **Use**: This variable is used to set the initial status of a `UsageSession` instance when it is created.


---
### SUMMARIZATION_USAGE_DEBIT 
- **Type**: `enum.IntEnum`
- **Description**: `SUMMARIZATION_USAGE_DEBIT` is a member of the `UsageEventType` enumeration, representing a specific type of usage event related to summarization services. It is assigned the integer value of 5, which categorizes it within the broader context of usage events that can be tracked in the application.
- **Use**: This variable is used to identify and categorize events related to summarization usage in the system.


---
### SUSPENDED 
- **Type**: `str`
- **Description**: `SUSPENDED` is a member of the `SubscriptionStatus` enumeration, representing a state where a subscription is temporarily inactive. This status indicates that the subscription is not currently active but may be reactivated in the future.
- **Use**: It is used to define the status of a subscription within the `Subscription` class.


---
### USER_SEAT_USAGE_CREDIT 
- **Type**: `string`
- **Description**: `USER_SEAT_USAGE_CREDIT` is an enumeration value within the `UsageEventType` class, representing a specific type of usage event related to credits allocated for user seat usage. This enum value is part of a broader system that tracks various usage events, including debits and credits associated with user activities.
- **Use**: It is used to categorize and identify events in the usage tracking system that pertain to credits for user seats.


---
### USER_SEAT_USAGE_DEBIT 
- **Type**: `string`
- **Description**: The `USER_SEAT_USAGE_DEBIT` is an enumeration value representing a specific type of usage event related to the debiting of user seat allocations within a system. It is part of the `UsageEventType` enum, which categorizes various usage events for tracking and billing purposes.
- **Use**: This variable is used to identify and categorize events where user seat allocations are deducted, facilitating accurate tracking of user seat usage.


---
### __table_args__ 
- **Type**: `tuple`
- **Description**: `__table_args__` is a global variable that defines additional constraints and indexes for the SQLAlchemy model. In this case, it creates a partial unique index on the `organization_id` column, ensuring that only active subscriptions are considered unique.
- **Use**: This variable is used to enforce database constraints and optimize queries related to active subscriptions.


---
### __tablename__ 
- **Type**: `string`
- **Description**: `__tablename__` is a string variable that defines the name of the database table associated with the `UsageSession` SQLModel class. It is used by SQLAlchemy to map the class to the corresponding table in the database.
- **Use**: This variable is utilized to specify the table name when the `UsageSession` model is created in the database.


---
### __ts_vector__ 
- **Type**: `any`
- **Description**: The `__ts_vector__` variable is a column in the `ChunkAndEmbedding` SQLModel class that stores a full-text search vector. It is computed from the `text` field using PostgreSQL's `to_tsvector` function, allowing for efficient text searching capabilities.
- **Use**: This variable is used to enable full-text search functionality on the text content of the `ChunkAndEmbedding` instances.


---
### agent_instance 
- **Type**: `SQLModel`
- **Description**: `agent_instance` is a global variable that holds an instance of the `RuntimeLogAgentInstance` class, which represents an agent's runtime log in a structured format. This instance includes attributes such as timestamps for creation and updates, a unique identifier, and relationships to messages associated with the agent.
- **Use**: This variable is used to manage and track the state and interactions of a specific agent instance throughout the application.


---
### agent_instance_id 
- **Type**: `string`
- **Description**: The `agent_instance_id` is a UUID that serves as a foreign key in the `RuntimeLogAgentMessage` class, linking each message to its corresponding agent instance in the `RuntimeLogAgentInstance` table. This relationship allows for the organization and retrieval of messages associated with specific agent instances.
- **Use**: It is used to establish a relationship between messages and their respective agent instances.


---
### app_installations 
- **Type**: `string`
- **Description**: The `app_installations` variable is a relationship field in the `GitProviderApp` class that holds a list of `GitProviderAppInstallation` instances associated with a specific Git provider application. This relationship allows for the management of multiple installations of a Git provider app for different organizations or users.
- **Use**: This variable is used to establish a one-to-many relationship between a Git provider app and its installations, enabling the retrieval and manipulation of installation data related to that app.


---
### billing_frequency 
- **Type**: `str, enum.Enum`
- **Description**: `billing_frequency` is a variable of type `BillingFrequency`, which is an enumeration representing the frequency of billing for a subscription. It can take values such as 'monthly' or 'annual', indicating how often the billing occurs.
- **Use**: This variable is used in the `Subscription` class to define the billing cycle for a subscription.


---
### bytes_in 
- **Type**: `int`
- **Description**: `bytes_in` is an integer field in the `UsageEvent` class that tracks the amount of data (in bytes) received during a usage event. It is initialized to zero and cannot be null, ensuring that every usage event records the incoming data size.
- **Use**: This variable is used to store and represent the total number of bytes received in a specific usage event.


---
### bytes_out 
- **Type**: `int`
- **Description**: `bytes_out` is an integer variable that represents the amount of data (in bytes) sent out during a specific usage event. It is part of the `UsageEvent` class, which tracks various metrics related to usage sessions.
- **Use**: This variable is used to quantify the outbound data transfer associated with a usage event.


---
### chunks_and_embeds 
- **Type**: `list[ChunkAndEmbedding]`
- **Description**: `chunks_and_embeds` is a list that holds instances of the `ChunkAndEmbedding` class, which represent segments of derived content along with their associated embeddings. This variable is part of the `DerivedContent` class, linking it to its corresponding chunks and embeddings for further processing or analysis.
- **Use**: This variable is used to establish a relationship between `DerivedContent` and its associated `ChunkAndEmbedding` instances, allowing for efficient retrieval and manipulation of content segments.


---
### client_id 
- **Type**: `str | None`
- **Description**: The `client_id` variable is a field in the `GitProviderApp` class that represents the unique identifier for an OAuth client associated with a Git provider application. It is defined as a string that can also be `None`, allowing for flexibility in cases where a client ID may not be assigned.
- **Use**: This variable is used to uniquely identify the OAuth client for authentication purposes in the context of Git provider applications.


---
### content 
- **Type**: `str | None`
- **Description**: The `content` variable is a field in the `DerivedContent` class, which represents a piece of content that can be associated with a node in a database. It is defined as a nullable string, allowing it to either hold textual content or be set to None if no content is available.
- **Use**: This variable is used to store the actual content of a derived entity, which can be retrieved or modified as needed.


---
### content_id 
- **Type**: `UUID`
- **Description**: The `content_id` variable is a field in the `ChunkAndEmbedding` class that serves as a foreign key linking to the `DerivedContent` table. It is defined as a non-nullable UUID, ensuring that each chunk and embedding is associated with a specific derived content entry.
- **Use**: This variable is used to establish a relationship between chunks and their corresponding derived content.


---
### content_kind 
- **Type**: `string`
- **Description**: The `content_kind` variable is defined as a field in the `DerivedContent` class, which is a SQLModel representing a table in a database. It is intended to store the type of content associated with a derived content entry, using the `ContentKind` enumeration to enforce valid values.
- **Use**: This variable is used to categorize the type of content in the `DerivedContent` table, allowing for better organization and retrieval of content based on its kind.


---
### content_name 
- **Type**: `str | None`
- **Description**: The `content_name` variable is an optional string field within the `DerivedContent` class, which represents the name or identifier of the content being derived. It can hold a string value or be set to `None`, indicating that the content name is not specified.
- **Use**: This variable is used to store the name of the derived content, which may be utilized for identification or categorization purposes.


---
### created_at 
- **Type**: `datetime | None`
- **Description**: The `created_at` variable is a field that stores the timestamp of when a record was created. It is defined as a nullable `datetime` type, with a default value set to the current time when a new record is inserted into the database.
- **Use**: This variable is used to track the creation time of instances of the `RuntimeLogAgentInstance`, `RuntimeLogAgentMessage`, `DerivedContent`, `Tag`, `ChunkAndEmbedding`, `InspectorRun`, `UsageSession`, `UsageEvent`, `GithubAppInstallation`, `Subscription`, `GitProviderApp`, and `GitProviderAppInstallation` classes.


---
### created_by 
- **Type**: `string`
- **Description**: The `created_by` variable is a string field in the `Tag` class that stores the identifier of the user or entity that created the tag. It is defined as a non-nullable column in the database schema, ensuring that every tag has an associated creator.
- **Use**: This variable is used to track the creator of a tag for auditing and ownership purposes.


---
### event_metadata 
- **Type**: `dict | None`
- **Description**: The `event_metadata` variable is a field in the `UsageEvent` class that stores additional metadata related to a specific usage event. It is defined as a dictionary that can be nullable, allowing for flexible storage of various event-specific details in JSON format.
- **Use**: This variable is used to capture and store supplementary information about usage events, which can be useful for analytics and reporting.


---
### event_type 
- **Type**: `UsageEventType`
- **Description**: The `event_type` variable is an instance of the `UsageEventType` enumeration, which defines various types of usage events that can occur within the application. Each type is represented by an integer value, corresponding to specific usage scenarios such as usage debits and credits.
- **Use**: This variable is used to categorize and identify the type of usage event being recorded in the `UsageEvent` model.


---
### generating 
- **Type**: `string`
- **Description**: `generating` is a string constant defined within the `Enum_Derived_Content_Status` enumeration, representing a specific state in a content generation process. It is used to indicate that a content generation task is currently in progress.
- **Use**: This variable is used to denote the status of a content generation operation.


---
### generation_complete 
- **Type**: `enum.Enum`
- **Description**: `generation_complete` is a member of the `Enum_Derived_Content_Status` enumeration, representing the state of content generation as completed. It is used to signify that a content generation process has successfully finished.
- **Use**: This variable is used to indicate the status of content generation in the application.


---
### generation_error 
- **Type**: `str`
- **Description**: `generation_error` is a string constant defined within the `Enum_Derived_Content_Status` enumeration, representing a specific state of content generation failure. This enum is used to categorize the status of derived content during processing, allowing for clear identification of errors in the generation workflow.
- **Use**: It is used to indicate that an error occurred during the content generation process.


---
### git_provider_app 
- **Type**: `class`
- **Description**: The `git_provider_app` variable represents a SQLModel class that defines the structure of the `git_provider_apps` table in the database. This class includes fields for various attributes of a Git provider application, such as its ID, provider kind, OAuth credentials, and timestamps for creation and updates.
- **Use**: This variable is used to create and manage instances of Git provider applications, facilitating interactions with the corresponding database table.


---
### git_provider_app_id 
- **Type**: `string`
- **Description**: `git_provider_app_id` is a UUID that serves as a foreign key linking a `GitProviderAppInstallation` to its corresponding `GitProviderApp`. This variable is crucial for maintaining the relationship between the installation of a Git provider application and the application itself.
- **Use**: It is used to associate a specific installation of a Git provider app with the app's details in the database.


---
### github_app_installation_id 
- **Type**: `string`
- **Description**: The `github_app_installation_id` is a string field that uniquely identifies a GitHub App installation associated with an organization. It is indexed for efficient querying and is part of a unique constraint that ensures no two installations can share the same ID within the same organization.
- **Use**: This variable is used to link GitHub App installations to their respective organizations in the database.


---
### hex_color 
- **Type**: `string`
- **Description**: The `hex_color` variable is a string that represents a color in hexadecimal format, typically used in web design and graphics. It is defined with a maximum length of 7 characters, allowing for the standard six-character hex code plus a leading hash symbol. This variable is part of the `Tag` class, which associates tags with specific colors.
- **Use**: The `hex_color` variable is used to store the color representation for a tag in the system.


---
### id 
- **Type**: `UUID | None`
- **Description**: The `id` variable is a unique identifier for instances of the `DerivedContent` class, generated using the `uuid.uuid4` function. It serves as the primary key for the table, ensuring that each record can be uniquely identified.
- **Use**: This variable is used to uniquely identify each `DerivedContent` record in the database.


---
### message 
- **Type**: `string`
- **Description**: The `message` variable is a dictionary that is part of the `RuntimeLogAgentMessage` class, which is used to store structured log messages related to an agent instance. It is defined as a field in the SQLModel, allowing it to be stored in a database as a JSON object.
- **Use**: This variable is used to capture and store log messages in a structured format for each instance of `RuntimeLogAgentMessage`.


---
### messages 
- **Type**: `list[RuntimeLogAgentMessage]`
- **Description**: The `messages` variable is a list that holds instances of `RuntimeLogAgentMessage`, which represent individual messages associated with a specific `RuntimeLogAgentInstance`. Each message contains details such as its content, creation time, and the order in which it was generated, allowing for structured logging and tracking of interactions within the agent instance.
- **Use**: This variable is used to establish a relationship between a `RuntimeLogAgentInstance` and its corresponding messages, enabling retrieval and management of all messages related to that instance.


---
### misc_metadata 
- **Type**: `dict | None`
- **Description**: The `misc_metadata` variable is a field in the `GitProviderAppInstallation` class that stores additional metadata related to the installation of a Git provider app. It is defined as a dictionary that can be nullable, allowing for flexible storage of various key-value pairs that may not fit into the predefined fields of the class.
- **Use**: This variable is used to hold extra information about the Git provider app installation that may be relevant for specific use cases.


---
### name 
- **Type**: `str`
- **Description**: The `name` variable represents the name of a `Tag` in the database, which is a unique identifier for categorizing or labeling content within an organization. It is defined as a string with a maximum length of 255 characters and cannot be null.
- **Use**: This variable is used to store and enforce the unique name of a tag associated with an organization.


---
### node 
- **Type**: `Node`
- **Description**: The `node` variable represents a relationship to a `Node` instance in the context of the `DocumentSource` class. It is used to establish a connection between document sources and their corresponding nodes, allowing for the retrieval of related node data.
- **Use**: This variable is utilized to link document sources to their respective nodes, facilitating data retrieval and management within the database.


---
### node_id 
- **Type**: `UUID | None`
- **Description**: The `node_id` variable is a field in the `DerivedContent` class that represents a unique identifier for a node in the system. It is defined as a UUID type and can be nullable, indicating that it may not always have a value assigned. This field is used to establish a foreign key relationship with the `v2_node` table, allowing for the association of derived content with specific nodes.
- **Use**: The `node_id` variable is used to link derived content to a specific node, facilitating relationships within the database.


---
### order 
- **Type**: `int | None`
- **Description**: The `order` variable is an integer field in the `DerivedContent` class that represents the sequence or position of the derived content within a collection. It can be set to `None`, indicating that the order is not defined, or it defaults to `0` if not specified.
- **Use**: This variable is used to determine the order of derived content items when they are retrieved or displayed.


---
### organization_id 
- **Type**: `string`
- **Description**: The `organization_id` variable is a string that represents the unique identifier for an organization within the system. It is used across various models to associate records with a specific organization, ensuring that data is correctly scoped and managed according to organizational boundaries.
- **Use**: This variable is utilized in multiple classes to link entities such as `UsageEvent`, `GithubAppInstallation`, and `Subscription` to their respective organizations.


---
### owner_organization_id 
- **Type**: `string`
- **Description**: The `owner_organization_id` variable is a string that represents the unique identifier of the organization that owns a specific Git provider application. It is indexed for efficient querying and is used to associate the application with its respective organization.
- **Use**: This variable is used to link a `GitProviderApp` instance to its owning organization, facilitating organization-specific operations and data management.


---
### page_node 
- **Type**: `UUID | None`
- **Description**: The `page_node` variable is a field in the `DocumentSource` class that represents a foreign key relationship to a `Node` instance. It is used to link a document source to a specific page node, allowing for the association of documents with their respective nodes in the database.
- **Use**: This variable is used to establish a relationship between the `DocumentSource` and the `Node` class, facilitating the retrieval of page node information related to document sources.


---
### page_node_id 
- **Type**: `UUID | None`
- **Description**: The `page_node_id` variable is a field in the `DocumentSource` class that represents a unique identifier for a page node in the database. It is defined as a UUID type and serves as a foreign key linking to the `v2_node` table, allowing for the association of document sources with specific nodes.
- **Use**: This variable is used to establish a relationship between the `DocumentSource` and the `Node` entities in the database.


---
### plan_type 
- **Type**: `enum`
- **Description**: The `plan_type` variable is an instance of the `PlanType` enum, which defines the different subscription plans available in the system, including 'CORE', 'ADVANCED', and 'ENTERPRISE'. This enum provides a clear and structured way to represent the various subscription options that an organization can choose from.
- **Use**: The `plan_type` variable is used within the `Subscription` class to specify the type of subscription plan associated with a particular subscription instance.


---
### primary_assets 
- **Type**: `list[PrimaryAsset]`
- **Description**: `primary_assets` is a list that holds instances of the `PrimaryAsset` class, representing the primary assets associated with a `Tag`. This relationship allows for the organization and categorization of primary assets under specific tags, facilitating better management and retrieval of related data.
- **Use**: This variable is used to establish a many-to-many relationship between `Tag` and `PrimaryAsset`, enabling the association of multiple primary assets with a single tag.


---
### provider_kind 
- **Type**: `GitProviderKind`
- **Description**: `provider_kind` is a variable of type `GitProviderKind`, which is an enumeration representing different types of Git providers. This variable is used to specify the kind of Git provider associated with a `GitProviderApp` instance, allowing for easy identification and differentiation between various Git services such as GitHub and GitLab.
- **Use**: This variable is used to define the specific Git provider type for a `GitProviderApp` instance.


---
### relative_path 
- **Type**: `string`
- **Description**: `relative_path` is a string variable that stores the relative path of a derived content item within the system. It is defined as a non-nullable field in the `DerivedContent` SQLModel, ensuring that every instance of derived content has a specified path.
- **Use**: This variable is used to identify and locate the derived content within the file structure or hierarchy of the application.


---
### session 
- **Type**: `str`
- **Description**: The `session` variable is a global variable that represents the current usage session in the application. It is typically used to track user interactions and events during a specific session, allowing for the collection of usage data and analytics.
- **Use**: This variable is used to manage and store information related to the current user's session.


---
### session_id 
- **Type**: `UUID`
- **Description**: The `session_id` variable is a unique identifier of type `UUID` that links a `UsageEvent` to its corresponding `UsageSession`. It serves as a foreign key in the `UsageEvent` table, ensuring that each event is associated with a specific session.
- **Use**: This variable is used to establish a relationship between a usage event and its session in the database.


---
### session_metadata 
- **Type**: `dict | None`
- **Description**: The `session_metadata` variable is a field in the `UsageSession` class that stores additional metadata related to a usage session. It is defined as a dictionary that can be nullable, allowing for flexible storage of session-specific information in JSON format.
- **Use**: This variable is used to hold supplementary data about the usage session, which can be accessed or modified as needed.


---
### source_node 
- **Type**: `string`
- **Description**: The `source_node` variable is a relationship field in the `DocumentSource` class that links to a `Node` instance. It represents the source node associated with a document, allowing for the establishment of connections between documents and their originating nodes.
- **Use**: This variable is used to retrieve the `Node` instance that serves as the source for a document in the context of the `DocumentSource` relationship.


---
### source_node_id 
- **Type**: `UUID | None`
- **Description**: The `source_node_id` variable is a field in the `DocumentSource` class that represents the unique identifier of a source node in the database. It is defined as a UUID type and serves as a primary key, allowing for the identification of document sources linked to specific nodes.
- **Use**: This variable is used to establish a foreign key relationship with the `Node` table, ensuring that each document source is associated with a valid source node.


---
### status 
- **Type**: `UsageSessionStatus`
- **Description**: The `status` variable represents the current state of a usage session, which can be one of three values: 'running', 'completed', or 'failed'. It is defined as an instance of the `UsageSessionStatus` enum, providing a clear and constrained set of possible values for session management.
- **Use**: This variable is used to track and manage the lifecycle of a usage session within the application.


---
### text_embedding_3_small 
- **Type**: `list[float]`
- **Description**: The `text_embedding_3_small` variable is a field in the `ChunkAndEmbedding` class that stores a list of floating-point numbers representing a small-sized text embedding. This embedding is likely used for machine learning or natural language processing tasks, where textual data is converted into a numerical format for analysis.
- **Use**: It is used to hold the numerical representation of text data for further processing or analysis.


---
### timestamp 
- **Type**: `None | datetime`
- **Description**: The `timestamp` variable is a field in the `UsageEvent` class that records the date and time when a usage event occurs. It is defined as a nullable datetime field, which means it can either hold a datetime value or be set to None. The field is automatically populated with the current timestamp when a new event is created, using the server's current time.
- **Use**: This variable is used to track the exact time of each usage event for logging and analysis purposes.


---
### tokens_in 
- **Type**: `integer`
- **Description**: The `tokens_in` variable represents the number of tokens that have been input into a specific usage event. It is used to track the amount of data processed during the event, which can be important for billing or usage analytics.
- **Use**: This variable is utilized within the `UsageEvent` class to store and manage the count of tokens received during a usage session.


---
### tokens_out 
- **Type**: `int`
- **Description**: `tokens_out` is an integer variable that represents the number of tokens that have been outputted during a specific usage event. It is part of the `UsageEvent` class, which tracks various metrics related to usage sessions.
- **Use**: This variable is used to quantify the output tokens generated in a usage event, allowing for analysis of resource consumption.


---
### type 
- **Type**: `str`
- **Description**: The `type` variable represents the category or classification of a `Tag` instance within the application. It is defined as a string with a maximum length of 255 characters and is marked as non-nullable, indicating that every tag must have a type assigned to it.
- **Use**: This variable is used to categorize tags for better organization and retrieval within the application.


---
### updated_at 
- **Type**: `string`
- **Description**: The `updated_at` variable is a field in the `Subscription`, `GitProviderApp`, `GitProviderAppInstallation`, and other classes that tracks the last time the record was updated. It is defined as a nullable `datetime` type and is automatically set to the current timestamp when the record is created or updated.
- **Use**: This variable is used to maintain the timestamp of the last update for the respective database record.


---
### updated_by 
- **Type**: `string`
- **Description**: The `updated_by` variable is a string field that stores the identifier of the user or system that last updated the record in the database. It is part of the `Tag` class, which represents a tagging system within the application, and is essential for tracking changes and maintaining an audit trail.
- **Use**: This variable is used to record the user responsible for the most recent update to a `Tag` instance.


---
### usage_events 
- **Type**: `list[UsageEvent]`
- **Description**: `usage_events` is a list that holds instances of the `UsageEvent` class, which represent individual events recorded during a usage session. Each event contains details such as the type of event, associated session, and metadata related to the usage.
- **Use**: This variable is used to establish a relationship between a `UsageSession` and its corresponding `UsageEvent` instances, allowing for the tracking of multiple events within a single session.


---
### version 
- **Type**: `str`
- **Description**: The `version` variable represents a foreign key relationship to a `Version` entity, which is likely used to track the versioning of a particular record in the database. It is defined as a UUID type, ensuring that each version is uniquely identifiable. This variable is essential for maintaining the integrity of relationships between different entities in the system.
- **Use**: It is used to associate an `InspectorRun` with a specific version of the data.


---
### version_id 
- **Type**: `UUID | None`
- **Description**: The `version_id` variable is a field in the `InspectorRun` class that represents a unique identifier for a version, linking it to the `Version` table. It is defined as a foreign key, ensuring that each `InspectorRun` is associated with a specific version, which is crucial for maintaining data integrity and relationships between these entities.
- **Use**: This variable is used to establish a relationship between the `InspectorRun` and the `Version` entities, allowing for the tracking of which version is associated with each inspection run.


# Classes

---
### BillingFrequency 
- **Type**: `enum`
- **Members**:
    - `MONTHLY`: Represents a monthly billing frequency.
    - `ANNUAL`: Represents an annual billing frequency.
- **Description**: The `BillingFrequency` class is an enumeration that defines two possible billing frequencies: monthly and annual. It inherits from both `str` and `enum.Enum`, allowing it to be used as a string while also providing enumeration capabilities. This class is useful for categorizing or specifying the billing cycle in subscription or billing-related contexts.
- **Inherits From**:
    - str
    - enum.Enum


---
### ChunkAndEmbedding 
- **Type**: `dataclass`
- **Members**:
    - `id`: A unique identifier for the chunk and embedding, generated by default.
    - `content_id`: References the ID of the associated derived content.
    - `content`: A relationship to the DerivedContent object this chunk belongs to.
    - `text`: The text content of the chunk.
    - `text_embedding_3_small`: A list of floats representing the small text embedding vector.
    - `chunk_number`: The sequence number of the chunk within the content.
    - `created_at`: Timestamp indicating when the chunk was created.
    - `updated_at`: Timestamp indicating when the chunk was last updated.
    - `__ts_vector__`: A computed column for full-text search indexing of the text.
- **Description**: The `ChunkAndEmbedding` class represents a chunk of text and its associated embedding vector, which is part of a larger derived content. It includes metadata such as creation and update timestamps, and supports full-text search through a computed TSVector column. The class is designed to be used with a SQL database, leveraging SQLModel for ORM capabilities, and it maintains relationships with the `DerivedContent` class to which it belongs.
- **Inherits From**:
    - SQLModel


---
### DerivedContent 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the derived content, generated by default using UUID.
    - `content_kind`: Specifies the kind of content, which can be nullable and indexed.
    - `node_id`: References the ID of a node, allowing for nullable values and cascading deletes.
    - `relative_path`: Stores the relative path of the content as a non-nullable string.
    - `content`: Holds the actual content as a nullable string.
    - `content_name`: An optional name for the content, stored as a nullable string.
    - `misc_metadata`: A dictionary for storing miscellaneous metadata, which can be nullable.
    - `created_at`: Records the creation timestamp, defaulting to the current time and not nullable.
    - `updated_at`: Records the last update timestamp, defaulting to the current time and not nullable.
    - `order`: An optional integer indicating the order, with a default value of 0.
    - `chunks_and_embeds`: A relationship to a list of ChunkAndEmbedding objects, back-populating the content.
    - `node`: A relationship to a Node object, back-populating the contents.
- **Description**: The DerivedContent class represents a model for storing derived content in a database, utilizing SQLModel for ORM capabilities. It includes fields for unique identification, content type, node association, and metadata, along with timestamps for creation and updates. The class also defines relationships with other models, such as ChunkAndEmbedding and Node, to manage content chunks and node associations. The class is designed to be flexible, allowing for nullable fields and default values, and includes several TODO comments indicating potential future changes to its structure.
- **Inherits From**:
    - SQLModel


---
### DocumentSource 
- **Type**: `class`
- **Members**:
    - `source_node_id`: A UUID representing the source node, used as a primary key and foreign key.
    - `page_node_id`: A UUID representing the page node, used as a primary key and foreign key.
    - `source_node`: A relationship to the Node class, representing the source node.
    - `page_node`: A relationship to the Node class, representing the page node.
- **Description**: The DocumentSource class is a SQLModel-based table that serves as a link between documents and their sources. It uses two UUID fields, source_node_id and page_node_id, as primary keys and foreign keys to establish relationships with nodes in the database. The class also defines relationships to the Node class for both source_node and page_node, allowing for bidirectional navigation between documents and their associated nodes.
- **Inherits From**:
    - SQLModel


---
### Enum_Derived_Content_Status 
- **Type**: `enum.Enum`
- **Members**:
    - `generating`: Represents the status of content that is currently being generated.
    - `generation_complete`: Indicates that the content generation process has completed successfully.
    - `generation_error`: Denotes that an error occurred during the content generation process.
- **Description**: The `Enum_Derived_Content_Status` class is an enumeration that defines the possible statuses for derived content generation processes. It inherits from both `str` and `enum.Enum`, allowing the enumeration members to be used as strings. The statuses include `generating`, `generation_complete`, and `generation_error`, which represent the different stages or outcomes of the content generation process.
- **Inherits From**:
    - str
    - enum.Enum


---
### GitProviderApp 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the GitProviderApp instance.
    - `provider_kind`: Specifies the kind of Git provider, such as GitLab or GitHub.
    - `shared_provider`: Indicates whether the provider is shared across multiple organizations.
    - `owner_organization_id`: The ID of the organization that owns this Git provider app.
    - `name`: The name of the Git provider app.
    - `base_url`: The base URL for the Git provider app.
    - `client_id`: The client ID used for OAuth authentication.
    - `redirect_uri`: The redirect URI used in OAuth flows.
    - `scopes`: The OAuth scopes requested by the app.
    - `created_at`: The timestamp when the GitProviderApp was created.
    - `updated_at`: The timestamp when the GitProviderApp was last updated.
    - `app_installations`: A list of GitProviderAppInstallation instances associated with this app.
- **Description**: The GitProviderApp class represents a Git provider application, such as GitHub or GitLab, within a system that integrates with these services. It includes details necessary for OAuth authentication, such as client ID, redirect URI, and scopes, and tracks metadata like creation and update timestamps. The class also manages relationships with app installations, allowing for the association of multiple installations with a single Git provider app.
- **Inherits From**:
    - SQLModel


---
### GitProviderAppInstallation 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the installation, generated by default.
    - `git_provider_app_id`: References the associated GitProviderApp, enforcing a foreign key constraint.
    - `organization_id`: Stores the ID of the organization associated with the installation.
    - `user_id`: Optional field for storing the user ID, used for OAuth purposes.
    - `misc_metadata`: Holds additional metadata in a dictionary format, stored as JSONB in the database.
    - `created_at`: Timestamp indicating when the installation was created, with a default value of the current time.
    - `updated_at`: Timestamp indicating when the installation was last updated, automatically updated to the current time.
    - `git_provider_app`: Defines a relationship to the GitProviderApp, allowing access to the associated app.
- **Description**: The GitProviderAppInstallation class represents a database table for storing installations of Git provider applications within an organization. It includes fields for identifying the installation, associating it with a specific GitProviderApp and organization, and storing optional user information for OAuth purposes. The class also manages metadata and timestamps for creation and updates, and enforces a unique constraint on the combination of git_provider_app_id, organization_id, and user_id to ensure data integrity.
- **Inherits From**:
    - SQLModel


---
### GitProviderKind 
- **Type**: `enum.Enum`
- **Members**:
    - `GITLAB_ENTERPRISE_SELF_MANAGED`: Represents the GitLab Enterprise Self-Managed provider kind.
- **Description**: The `GitProviderKind` class is an enumeration that defines different types of Git provider kinds, specifically focusing on the GitLab Enterprise Self-Managed provider. It inherits from both `str` and `enum.Enum`, allowing it to be used as a string while also providing enumeration capabilities. The class includes a `__str__` method that returns the name of the enumeration member, facilitating a human-readable representation of the enum value.
- **Inherits From**:
    - str
    - enum.Enum

**Methods**

---
#### GitProviderKind.__str__
The `__str__` function returns the name of the enum member as a string.
- **Inputs**:
    - `self`: The instance of the enum member for which the string representation is being requested.
- **Control Flow**:
    - The function directly returns the `name` attribute of the enum member, which is a string representation of the enum's name.
- **Output**:
    - A string that represents the name of the enum member.



---
### GithubAppInstallation 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the GithubAppInstallation instance.
    - `organization_id`: The ID of the organization associated with the installation.
    - `github_app_installation_id`: The ID of the GitHub app installation.
    - `created_at`: The timestamp when the installation was created.
    - `updated_at`: The timestamp when the installation was last updated.
    - `__tablename__`: The name of the database table for this model, 'github_app_installations'.
    - `__table_args__`: Unique constraint ensuring the combination of github_app_installation_id and organization_id is unique.
- **Description**: The GithubAppInstallation class represents a database model for storing information about GitHub app installations within an organization. It includes fields for unique identification, organization association, and timestamps for creation and updates. The class also enforces a unique constraint on the combination of GitHub app installation ID and organization ID to ensure data integrity.
- **Inherits From**:
    - SQLModel


---
### InspectorRun 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the InspectorRun instance, generated by default.
    - `version_id`: A foreign key linking to the associated version, with cascade delete behavior.
    - `created_at`: The timestamp when the InspectorRun was created, with a default value of the current time.
    - `updated_at`: The timestamp when the InspectorRun was last updated, automatically updated to the current time.
    - `call_id`: An optional string identifier for the call associated with the InspectorRun.
    - `version`: A relationship to the Version class, allowing access to the associated version's inspector runs.
- **Description**: The InspectorRun class represents a database table for tracking individual runs of an inspector process, with fields for unique identification, version association, timestamps for creation and updates, and an optional call identifier. It includes a relationship to the Version class, enabling linkage and back-population of inspector runs related to a specific version.
- **Inherits From**:
    - SQLModel


---
### PlanType 
- **Type**: `enum.Enum`
- **Members**:
    - `CORE`: Represents the core plan type.
    - `ADVANCED`: Represents the advanced plan type.
    - `ENTERPRISE`: Represents the enterprise plan type.
- **Description**: The `PlanType` class is an enumeration that defines different types of subscription plans available in the system. It inherits from both `str` and `enum.Enum`, allowing each plan type to be represented as a string. The available plan types are 'core', 'advanced', and 'enterprise', which can be used to categorize and manage different levels of service offerings.
- **Inherits From**:
    - str
    - enum.Enum


---
### RuntimeLogAgentInstance 
- **Type**: `dataclass`
- **Members**:
    - `created_at`: Stores the timestamp when the instance was created.
    - `updated_at`: Stores the timestamp when the instance was last updated.
    - `id`: Unique identifier for the instance, generated by default.
    - `model`: Represents the model associated with the log agent instance.
    - `messages`: Holds a list of messages related to the log agent instance.
    - `organization_id`: Identifier for the organization associated with the instance.
- **Description**: The `RuntimeLogAgentInstance` class is a data model representing an instance of a runtime log agent, which includes metadata such as creation and update timestamps, a unique identifier, and associations with a model and organization. It also maintains a relationship with `RuntimeLogAgentMessage` instances, which are messages linked to this log agent instance. This class is designed to be used with SQLModel for database interactions, leveraging SQLAlchemy's ORM capabilities.
- **Inherits From**:
    - SQLModel


---
### RuntimeLogAgentMessage 
- **Type**: `class`
- **Members**:
    - `created_at`: Stores the timestamp when the message was created.
    - `id`: Unique identifier for the message, generated by default.
    - `message`: Holds the content of the message as a dictionary.
    - `order`: Represents the order of the message, with auto-incrementing integer values.
    - `agent_instance_id`: Foreign key linking to the associated RuntimeLogAgentInstance.
    - `agent_instance`: Relationship to the RuntimeLogAgentInstance, allowing access to the instance's messages.
- **Description**: The `RuntimeLogAgentMessage` class is a SQLModel-based ORM class that represents a log message associated with a runtime agent instance. It includes fields for storing the creation timestamp, a unique identifier, the message content, and the order of the message. Additionally, it maintains a foreign key relationship with the `RuntimeLogAgentInstance` class, enabling the association of messages with specific agent instances.
- **Inherits From**:
    - SQLModel


---
### Subscription 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the subscription, generated by default.
    - `organization_id`: The identifier for the organization associated with the subscription.
    - `plan_type`: The type of plan the subscription is associated with, which is required and indexed.
    - `status`: The current status of the subscription, defaulting to active.
    - `billing_frequency`: The frequency at which billing occurs, which is required.
    - `created_at`: The timestamp when the subscription was created, with a server default of the current time.
    - `updated_at`: The timestamp when the subscription was last updated, automatically updated to the current time.
- **Description**: The `Subscription` class represents a subscription model in a database, inheriting from SQLModel and designed to be a table. It includes fields for a unique identifier, organization ID, plan type, status, billing frequency, and timestamps for creation and updates. The class also defines a unique index to ensure that only one active subscription exists per organization.
- **Inherits From**:
    - SQLModel


---
### SubscriptionStatus 
- **Type**: `enum.Enum`
- **Members**:
    - `ACTIVE`: Represents an active subscription status.
    - `CANCELED`: Represents a canceled subscription status.
    - `SUSPENDED`: Represents a suspended subscription status.
- **Description**: The `SubscriptionStatus` class is an enumeration that defines the possible states of a subscription, which include 'active', 'canceled', and 'suspended'. It inherits from both `str` and `enum.Enum`, allowing the enumeration members to be used as strings while also providing enumeration capabilities.
- **Inherits From**:
    - str
    - enum.Enum


---
### Tag 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the tag, generated by the server.
    - `name`: The name of the tag, which must be unique within an organization.
    - `hex_color`: The hexadecimal color code associated with the tag.
    - `organization_id`: The identifier for the organization to which the tag belongs.
    - `type`: The type of the tag, used for categorization.
    - `created_at`: The timestamp when the tag was created.
    - `created_by`: The identifier of the user who created the tag.
    - `updated_at`: The timestamp when the tag was last updated.
    - `updated_by`: The identifier of the user who last updated the tag.
    - `primary_assets`: A list of primary assets associated with the tag.
- **Description**: The `Tag` class represents a tag entity in a database, designed to categorize and manage resources within an organization. It includes attributes for a unique identifier, name, color, organization association, and type, along with metadata for creation and modification timestamps and user identifiers. The class also establishes a relationship with primary assets, allowing tags to be linked to various resources.
- **Inherits From**:
    - SQLModel


---
### UsageEvent 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the usage event, automatically generated as a UUID.
    - `event_type`: Specifies the type of usage event, represented by the UsageEventType enum.
    - `session_id`: References the associated usage session by its UUID, with a foreign key constraint.
    - `organization_id`: Stores the identifier of the organization associated with the event.
    - `user_id`: Stores the identifier of the user associated with the event.
    - `event_source`: Indicates the source of the event as a string.
    - `bytes_in`: Records the number of bytes received during the event, defaulting to 0.
    - `bytes_out`: Records the number of bytes sent during the event, defaulting to 0.
    - `tokens_in`: Records the number of tokens received during the event, defaulting to 0.
    - `tokens_out`: Records the number of tokens sent during the event, defaulting to 0.
    - `timestamp`: The date and time when the event occurred, with a default of the current time.
    - `event_metadata`: Optional metadata associated with the event, stored as a JSONB object.
    - `session`: A relationship to the UsageSession class, linking usage events to their sessions.
- **Description**: The UsageEvent class represents an event that records usage data within a system, capturing details such as the type of event, associated session, organization, user, and data metrics like bytes and tokens transferred. It is designed to be part of a relational database model using SQLModel, with fields for storing event-specific metadata and timestamps. The class also establishes a relationship with the UsageSession class, allowing for the organization of events within sessions.
- **Inherits From**:
    - SQLModel


---
### UsageEventType 
- **Type**: `enum.IntEnum`
- **Members**:
    - `AGENT_PIPELINE_USAGE_DEBIT`: Represents a usage debit for agent pipeline activities.
    - `INSPECTOR_TECH_DOC_USAGE_DEBIT`: Represents a usage debit for inspector technical document activities.
    - `INSPECTOR_CODE_DIFF_USAGE_DEBIT`: Represents a usage debit for inspector code difference activities.
    - `ONBOARDING_USAGE_DEBIT`: Represents a usage debit for onboarding activities.
    - `SUMMARIZATION_USAGE_DEBIT`: Represents a usage debit for summarization activities.
    - `BASE_PLATFORM_USAGE_CREDIT`: Represents a usage credit for base platform activities.
    - `ADDITIONAL_PLATFORM_USAGE_CREDIT`: Represents a usage credit for additional platform activities.
    - `USER_SEAT_USAGE_DEBIT`: Represents a usage debit for user seat activities.
    - `USER_SEAT_USAGE_CREDIT`: Represents a usage credit for user seat activities.
- **Description**: The `UsageEventType` class is an enumeration that defines various types of usage events, each associated with a unique integer value. These events are categorized into debits and credits, representing different activities such as agent pipeline usage, inspector document usage, onboarding, and platform usage. The class also includes a method to convert the enum names into a more human-readable format by replacing underscores with spaces and capitalizing the words.
- **Inherits From**:
    - enum.IntEnum

**Methods**

---
#### UsageEventType.__str__
The `__str__` function returns a human-readable version of an enum name by replacing underscores with spaces and capitalizing each word.
- **Inputs**:
    - `self`: The instance of the enum class on which the method is called.
- **Control Flow**:
    - The method accesses the `name` attribute of the enum instance, which contains the enum's name as a string.
    - It replaces underscores ('_') in the name with spaces (' ').
    - It converts the modified string to title case, capitalizing the first letter of each word.
    - The resulting string is returned.
- **Output**:
    - A string that is a human-readable version of the enum name, with underscores replaced by spaces and each word capitalized.



---
### UsageSession 
- **Type**: `class`
- **Members**:
    - `id`: A unique identifier for the usage session, generated by default using UUID.
    - `status`: The current status of the usage session, defaulting to RUNNING.
    - `organization_id`: The identifier for the organization associated with the session.
    - `user_id`: The identifier for the user associated with the session.
    - `session_metadata`: Optional metadata associated with the session, stored as a dictionary.
    - `created_at`: The timestamp when the session was created, with a default value set to the current time.
    - `updated_at`: The timestamp when the session was last updated, automatically updated to the current time on changes.
    - `usage_events`: A list of usage events associated with the session, with a relationship that supports cascading deletes.
- **Description**: The `UsageSession` class represents a session of usage within an application, tracking its status, associated organization and user, and any metadata. It includes timestamps for creation and updates, and maintains a relationship with `UsageEvent` instances that occur during the session. This class is designed to be used with a SQL database, leveraging SQLModel for ORM capabilities, and supports automatic UUID generation for unique identification.
- **Inherits From**:
    - SQLModel


---
### UsageSessionStatus 
- **Type**: `enum.Enum`
- **Members**:
    - `RUNNING`: Represents a session that is currently running.
    - `COMPLETED`: Represents a session that has been completed.
    - `FAILED`: Represents a session that has failed.
- **Description**: The `UsageSessionStatus` class is an enumeration that defines the possible states of a usage session, which include 'running', 'completed', and 'failed'. This class is used to track and manage the status of a session within the application, providing a clear and standardized way to represent session states.
- **Inherits From**:
    - str
    - enum.Enum


# Functions

---
### update_primary_asset_content_timestamp 
The function `update_primary_asset_content_timestamp` updates the timestamp of the last related content update for a primary asset associated with a given derived content.
- **Inputs**:
    - `mapper`: An instance of `Mapper[Any]` from SQLAlchemy, which is not used in the function body.
    - `connection`: An instance of `Connection` from SQLAlchemy, used to execute the update statement.
    - `target`: An instance of `DerivedContent`, representing the derived content whose associated primary asset's timestamp needs updating.
- **Control Flow**:
    - Check if `target.node_id` is not set; if it is not set, the function returns immediately without making any updates.
    - Select the `PrimaryAsset.id` by joining the `PrimaryAsset`, `Version`, and `Node` tables where the `Node.id` matches `target.node_id`.
    - Construct an update statement for the `PrimaryAsset` table to set the `related_content_last_updated` field to the current timestamp for the selected primary assets.
    - Execute the update statement using the provided `connection`.
- **Output**:
    - The function does not return any value; it performs an update operation on the database.


