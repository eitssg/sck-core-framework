"""ActionSpec Model Module for Core Automation Framework.

This module contains the ActionSpec class which provides a model for how Tasks or Actions are to
be provided to the core-execute library. The ActionSpec class defines actions that can be performed
by the Core Automation framework, including creating or deleting AWS resources, updating user
permissions, and other operations that wouldn't necessarily be done in a CloudFormation template.

Key Features:
    - **Action Definition**: Comprehensive specification for automation tasks
    - **Dependency Management**: Support for action dependencies and execution ordering
    - **Conditional Execution**: Python expressions for conditional action execution
    - **Output Management**: Organized output storage with namespace support
    - **Lifecycle Hooks**: Pre/post execution hooks for complex workflows
    - **Validation**: Comprehensive validation for action integrity and dependencies

Common Use Cases:
    - CloudFormation stack creation and management
    - IAM user and permission management
    - Event recording and status tracking
    - Resource tagging and metadata updates
    - Custom AWS service integrations

Classes:
    ActionParams: Base parameters model for action configuration.
    ActionSpec: Complete action specification with validation and execution metadata.

Examples:
    Creating a CloudFormation stack action:

    >>> action = ActionSpec(
    ...     name="create-vpc-stack",
    ...     kind="AWS::CreateStack",
    ...     params={
    ...         "account": "123456789012",
    ...         "region": "us-east-1",
    ...         "stack_name": "vpc-infrastructure",
    ...         "template": "templates/vpc.yaml"
    ...     }
    ... )

    Creating an action with dependencies:

    >>> database_action = ActionSpec(
    ...     name="create-database",
    ...     kind="AWS::CreateStack",
    ...     depends_on=["create-vpc-stack"],
    ...     params={
    ...         "stack_name": "database-stack",
    ...         "template": "templates/database.yaml"
    ...     }
    ... )

Note:
    Consider moving this to the core-execute library as it is used almost exclusively
    by the core-execute library for action execution and orchestration.
"""

from typing import Any
import warnings
from collections import OrderedDict
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    SerializationInfo,
    model_serializer,
    field_validator,
    model_validator,
)


class ActionParams(BaseModel):
    """Base parameters model for action configuration.

    Provides common parameters required by most actions, particularly AWS-related
    actions that need account and region specification. This model serves as a
    foundation for action-specific parameter validation.

    Attributes:
        account: AWS account ID where the action should be executed.
        region: AWS region where the action should be executed.

    Examples:
        >>> params = ActionParams(
        ...     account="123456789012",
        ...     region="us-east-1"
        ... )
        >>> print(params.account)
        '123456789012'

        >>> # Serialization uses aliases by default
        >>> data = params.model_dump()
        >>> print("Account" in data)
        True
    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    account: str = Field(
        ...,
        alias="Account",
        description="AWS account ID where this action should be executed",
    )
    region: str = Field(
        ...,
        alias="Region",
        description="AWS region where this action should be executed",
    )

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Serialize model with optimized defaults.

        Args:
            **kwargs: Keyword arguments for serialization options.

        Returns:
            Dictionary representation with None values excluded and aliases used.

        Examples:
            >>> params = ActionParams(account="123456789012", region="us-east-1")
            >>> data = params.model_dump()
            >>> print("Account" in data)
            True
        """
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        if "by_alias" not in kwargs:
            kwargs["by_alias"] = True
        return super().model_dump(**kwargs)


class ActionSpec(BaseModel):
    """Complete specification for Core Automation actions with validation and execution metadata.

    The ActionSpec class defines an "action" or "task" that Core Automation will perform when
    deploying infrastructure to your Cloud. Tasks could include adding tags to resources,
    adjusting DNS entries, creating CloudFormation stacks, etc. Tasks are executed by
    core-execute and are defined in the core-execute.actionlib library.

    The class provides comprehensive validation for action integrity, dependency management,
    and output organization to ensure reliable automation workflows.

    Attributes:
        apiVersion: API version of the actions API (defaults to "v1").
        name: Unique identifier for the action with namespace support.
        kind: Action type that determines which action class will be instantiated.
        metadata: Arbitrary metadata about the action.
        depends_on: List of action names that must complete successfully before this action.
        params: Parameters dictionary containing action-specific configuration.
        scope: Organizational scope (portfolio, app, branch, build).
        condition: Python expression for conditional execution.
        before: List of actions that should execute after this action completes.
        after: List of actions that should execute before this action starts.
        save_outputs: Whether to save action outputs to the state system.
        lifecycle_hooks: List of ActionSpec objects for lifecycle event handling.

    Properties:
        action_name: Extracts the final component after the last '/' in the name.
        output_namespace: Calculated namespace for organizing action outputs.
        state_namespace: Namespace used for state variable storage.
        action: Backward compatibility property returning the kind value.
        label: DEPRECATED - Use 'name' instead.
        type: DEPRECATED - Use 'kind' instead.

    Examples:
        >>> # Basic CloudFormation stack creation
        >>> action = ActionSpec(
        ...     name="create-s3-bucket",
        ...     kind="AWS::CreateStack",
        ...     params={
        ...         "account": "123456789012",
        ...         "region": "us-east-1",
        ...         "stack_name": "my-s3-bucket",
        ...         "template": "templates/s3-bucket.yaml"
        ...     }
        ... )

        >>> # Action with dependencies and namespace
        >>> action = ActionSpec(
        ...     name="myapp:action/deploy-lambda",
        ...     kind="AWS::CreateStack",
        ...     depends_on=["create-s3-bucket"],
        ...     params={
        ...         "stack_name": "lambda-function",
        ...         "template": "templates/lambda.yaml"
        ...     }
        ... )
        >>> print(action.action_name)
        'deploy-lambda'
        >>> print(action.output_namespace)
        'myapp:output'

        >>> # Conditional action with lifecycle hooks
        >>> action = ActionSpec(
        ...     name="conditional-cleanup",
        ...     kind="AWS::DeleteStack",
        ...     condition="deployment.environment != 'production'",
        ...     lifecycle_hooks=[
        ...         ActionSpec(
        ...             name="backup-data",
        ...             kind="AWS::BackupResources",
        ...             params={"resources": ["database", "files"]}
        ...         )
        ...     ]
        ... )

        >>> # Action ordering with before/after
        >>> setup_action = ActionSpec(
        ...     name="setup-logging",
        ...     kind="AWS::EnableLogging",
        ...     before=["deploy-app", "deploy-database"]
        ... )

    Output Management:
        Actions can save outputs for use by other actions:

        >>> # Action that saves outputs
        >>> vpc_action = ActionSpec(
        ...     name="infra:action/create-vpc",
        ...     kind="AWS::CreateStack",
        ...     save_outputs=True,  # Enables output saving
        ...     params={"stack_name": "vpc-stack"}
        ... )

        >>> # Later action using the outputs
        >>> app_action = ActionSpec(
        ...     name="app:action/deploy",
        ...     kind="AWS::CreateStack",
        ...     depends_on=["infra:action/create-vpc"],
        ...     params={
        ...         "vpc_id": "{{ actions['infra:action/create-vpc'].outputs.vpc_id }}"
        ...     }
        ... )

    Validation Rules:
        - **Name Format**: Must be alphanumeric with hyphens, underscores, colons, slashes
        - **No Self-Dependencies**: Actions cannot depend on themselves
        - **Scope Validation**: Must be one of portfolio, app, branch, build
        - **Dependency Integrity**: All dependency references must be valid action names
        - **Namespace Consistency**: Output namespaces follow consistent transformation rules

    Note on save_outputs:
        When save_outputs is True, action outputs are organized by namespace:
        - Action calls set_output("variable_name", value)
        - Stored as "{namespace}/variable_name": value in state
        - Namespace calculated from action name (e.g., "myapp:action" → "myapp:output")
    """

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    apiVersion: str = Field(
        alias="ApiVersion",
        description="The API version of the actions API",
        default="v1",
    )

    name: str = Field(
        ...,
        alias="Name",
        description="""The name of the action. A unique identifier that serves multiple purposes:

    **Primary Functions:**
    
    1. **Unique Identification**: Primary identifier for the action within a deployment spec
    2. **Dependency Resolution**: Referenced by other actions in depends_on, before, and after fields  
    3. **Action Name Derivation**: The action_name property extracts the final component after the last '/'
    4. **Output Namespace**: The output_namespace property uses the first component before '/' for grouping outputs
    
    **Name Structure Examples:**
    
    - ``"deploy-stack"`` → action_name="deploy-stack", output_namespace="deploy-stack"  
    - ``"myapp:action/deploy"`` → action_name="deploy", output_namespace="myapp:output"
    - ``"portfolio/app/branch/task"`` → action_name="task", output_namespace="portfolio"
    
    **Format Rules:**
    
    - Alphanumeric characters, hyphens, underscores, colons, and forward slashes allowed
    - Cannot start or end with hyphens
    - Maximum length of 63 characters (AWS resource compatibility)
    - Forward slashes (/) create hierarchical namespaces
    - Colons (:) used for namespace type designation (e.g., :action becomes :output)""",
        min_length=1,
    )

    kind: str = Field(
        ...,
        alias="Kind",
        description="""The action kind that determines which action class will be instantiated.

    **Purpose:**
    
    The kind field specifies which action implementation from core_execute.actionlib 
    will be used to execute this action. It maps directly to action class names using
    the AWS service namespace convention.
    
    **Naming Convention:**
    
    - The format is "AWS::ActionName", "RDS::ActionName", "KMS::ActionName", etc.
    - Maps to snake_case class names in the actionlib module
    
    **Common Examples:**

    - ``"AWS::CreateStack"`` - Creates AWS CloudFormation stacks
    - ``"AWS::DeleteStack"`` - Deletes AWS CloudFormation stacks
    - ``"AWS::PutEvent"`` - Records events in the database
    - ``"AWS::GetStackReferences"`` - Checks stack export dependencies
    - ``"AWS::PutUser"`` - Creates IAM users

    **Action Discovery:**
    
    The core-execute framework uses this value to dynamically load and instantiate
    the appropriate action class at runtime. Invalid kinds will result in action
    execution failures.""",
        min_length=1,
    )

    metadata: dict[str, Any] | None = Field(
        alias="Metadata",
        description="Arbitrary metadata about this action for documentation and tooling",
        default=None,
    )

    depends_on: list[str] = Field(
        default=[],
        alias="DependsOn",
        description="""List of action names that must complete successfully before this action can execute.

    **Dependency Resolution:**
    
    - Actions wait for all dependencies to reach 'completed' state before starting
    - If any dependency fails, this action will be skipped with 'dependencies_failed' status
    - Circular dependencies are detected and will cause validation errors
    - Dependencies are resolved within the scope of a single deployspec.yaml file
    
    **Dependency Types:**
    
    - **Resource Dependencies**: Action needs outputs or resources from another action
    - **Ordering Dependencies**: Action must run after another for logical reasons
    - **Conditional Dependencies**: Action depends on validation or checks from another
    
    **Examples:**
    
    .. code-block:: yaml
    
        # Single dependency
        depends_on: ["create-s3-bucket"]
        
        # Multiple dependencies  
        depends_on: ["create-vpc", "create-subnets", "create-security-groups"]
        
        # Complex dependency chain
        depends_on: ["validate-template", "check-permissions"]
    
    **Best Practices:**
    
    - Keep dependency chains as short as possible for better parallelization
    - Use explicit dependencies rather than relying on execution order
    - Consider using ``before``/``after`` for simple ordering without failure propagation""",
    )

    params: dict[str, Any] = Field(
        ...,
        alias="Params",
        description="""Parameters dictionary containing action-specific configuration and inputs.

    **Parameter Structure:**
    
    The params dictionary contains all configuration needed for action execution.
    Each action kind defines its own parameter schema through Pydantic models.
    
    **Common Parameter Patterns:**
    
    - **AWS Resources**: Account, Region, StackName, Template paths
    - **User Management**: Username, Permissions, Groups, Policies  
    - **Event Recording**: Type, Status, Message, Identity
    - **File Operations**: Source, Destination, Permissions
    
    **Variable Substitution:**
    
    Parameter values support template variable substitution using Jinja2 syntax:
    
    .. code-block:: yaml
    
        params:
          account: "{{ deployment.account }}"
          region: "{{ deployment.region }}"  
          stack_name: "{{ app.name }}-{{ branch.name }}-stack"
          template: "templates/{{ stack_type }}.yaml"
    
    **Parameter Validation:**
    
    - Action-specific Pydantic models validate parameter types and constraints
    - Required parameters will cause validation errors if missing
    - Unknown parameters are typically ignored but may generate warnings
    
    **Examples by Action Type:**
    
    .. code-block:: yaml
    
        # CloudFormation stack creation
        params:
          account: "123456789012"
          region: "us-east-1"
          stack_name: "my-application-stack"
          template: "infrastructure/app-stack.yaml"
          
        # Event recording
        params:
          type: "STATUS"
          status: "DEPLOY_SUCCESS"
          message: "Application deployed successfully"
          identity: "{{ deployment.identity }}"
    
    **Dynamic Parameters:**
    
    Parameters can reference outputs from other actions using the template system,
    enabling dynamic workflows where later actions use results from earlier ones.""",
    )

    scope: str = Field(
        alias="Scope",
        description="""The organizational scope that determines which level of the deployment hierarchy this action operates on.

        **Scope Hierarchy:**
        
        Actions are scoped to operate at specific levels of the deployment organization:
        
        1. **portfolio** - Business Application level (cross-app operations)
        2. **app** - Application deployment level (specific app within portfolio)  
        3. **branch** - Application branch level (branch-specific operations)
        4. **build** - Build/version level (specific build or version operations)
        
        **Scope Characteristics:**
        
        **Portfolio Scope:**
        - Operations that affect the entire business application (portfolio)
        - Cross-application shared resources and configurations
        - Portfolio-wide policies, networking, and infrastructure
        - Examples: Shared VPCs, cross-app IAM roles, portfolio-level monitoring
        
        **App Scope:**  
        - Operations specific to a single application deployment within the portfolio
        - Application-specific infrastructure and configuration
        - Resources that serve one specific app but may span multiple branches
        - Examples: App-specific databases, load balancers, ECR repositories
        
        **Branch Scope:**
        - Operations specific to an application branch (e.g., feature, development, staging)
        - Branch-specific environments and testing resources
        - Resources tied to specific git branches or development workflows
        - Examples: Feature branch environments, branch-specific test databases
        
        **Build Scope:**
        - Operations specific to a particular build number or version of the application
        - Build artifacts, deployment packages, and version-specific resources
        - Resources created for specific deployments or releases
        - Examples: Deployment packages, build artifacts, version-specific configurations
        
        **Action Targeting:**
        
        The scope determines where the action operates in the deployment hierarchy:
        - Portfolio actions affect shared resources across all apps in the portfolio
        - App actions affect resources specific to one application deployment
        - Branch actions affect resources specific to a development branch
        - Build actions affect resources specific to a build/version number
        
        **Resource Lifecycle:**
        
        Scope affects resource lifecycle and cleanup behavior:
        - Portfolio resources persist across all deployments and branches
        - App resources persist across branches but are app-specific
        - Branch resources are created/destroyed with branch lifecycle
        - Build resources are created/destroyed with individual builds
        
        **Default Behavior:**
        
        Most actions default to 'build' scope as they typically operate on specific
        build artifacts or version-specific configurations during deployment.""",
        default="build",
    )

    condition: str | None = Field(
        alias="Condition",
        description="""Python expression that determines whether this action should execute.

        **Conditional Execution:**
        
        The condition field allows actions to be executed conditionally based on 
        deployment context, previous action results, or environment variables.
        
        **Expression Syntax:**
        
        - Standard Python expressions that evaluate to boolean
        - Access to deployment context through template variables
        - Can reference outputs from previously executed actions
        - Defaults to ``True`` (always execute) if not specified
        
        **Available Context:**
        
        Conditions have access to the same template context as parameters:
        
        - ``deployment.*`` - Deployment details (account, region, environment)
        - ``app.*`` - Application information (name, version, configuration)
        - ``branch.*`` - Branch details (name, type, commit information)  
        - ``env.*`` - Environment variables
        - Action outputs from dependencies (if action has completed)
        
        **Common Condition Patterns:**
        
        .. code-block:: yaml
        
            # Environment-based conditions
            condition: "deployment.environment == 'production'"
            condition: "branch.name != 'main'"
            
            # Feature flag conditions  
            condition: "env.ENABLE_MONITORING == 'true'"
            condition: "app.features.database_encryption"
            
            # Dependency-based conditions
            condition: "actions['check-prerequisites'].outputs.passed == true"
            condition: "len(actions['validate-template'].outputs.errors) == 0"
            
            # Complex logical conditions
            condition: "deployment.environment in ['staging', 'production'] and branch.type == 'release'"
        
        **Evaluation Timing:**
        
        - Conditions are evaluated just before action execution
        - All dependencies must complete before condition evaluation
        - Failed condition evaluation skips the action with 'condition_not_met' status
        
        **Best Practices:**
        
        - Keep conditions simple and readable
        - Use explicit comparisons rather than truthy/falsy evaluation
        - Document complex conditions in action comments
        - Test conditions thoroughly across different deployment scenarios""",
        default=None,
    )

    before: list[str] | None = Field(
        alias="Before",
        description="""List of action names that should execute after this action completes.

        **Execution Ordering:**
        
        The before field creates soft dependencies where this action will attempt to
        complete before the listed actions start, but failure doesn't prevent the
        other actions from executing.
        
        **Difference from depends_on:**
        
        - ``depends_on``: Hard dependency - listed actions must complete successfully first
        - ``before``: Soft ordering - this action runs first but failure doesn't block others
        - ``before`` is the inverse relationship of ``depends_on``
        
        **Use Cases:**
        
        **Resource Preparation:**
        
        .. code-block:: yaml
        
            # Prepare logging before other actions start
            - name: setup-logging
            before: ["create-app-stack", "deploy-database"]
        
        **Cleanup Ordering:**
        
        .. code-block:: yaml
        
            # Backup before destructive operations
            - name: backup-database  
            before: ["delete-old-data", "migrate-schema"]
        
        **Performance Optimization:**
        
        .. code-block:: yaml
        
            # Start long-running processes early
            - name: warm-up-cache
            before: ["deploy-application"]
        
        **Best Practices:**
        
        - Use ``before`` for optimization and preparation, not critical dependencies
        - Use ``depends_on`` when failure of one action should prevent others
        - Avoid creating complex before/after chains that are hard to understand
        - Consider using explicit ``depends_on`` for clearer dependency relationships""",
        default=None,
    )

    after: list[str] | None = Field(
        alias="After",
        description="""List of action names that should execute before this action starts.

        **Execution Ordering:**
        
        The after field creates soft dependencies where this action will wait for
        the listed actions to complete, but their failure doesn't prevent this
        action from executing.
        
        **Relationship to other fields:**
        
        - ``after``: This action runs after listed actions (soft dependency)
        - ``depends_on``: This action requires listed actions to succeed (hard dependency)  
        - ``after`` is the inverse relationship of ``before``
        
        **Use Cases:**
        
        **Cleanup and Finalization:**
        
        .. code-block:: yaml
        
            # Clean up after main deployment actions
            - name: cleanup-temp-files
            after: ["deploy-app", "run-tests", "generate-reports"]
        
        **Monitoring and Notification:**
        
        .. code-block:: yaml
        
            # Send notifications after deployment completes
            - name: notify-team
            after: ["deploy-production", "run-smoke-tests"]
        
        **Resource Optimization:**
        
        .. code-block:: yaml
        
            # Scale down resources after batch processing
            - name: scale-down-workers
            after: ["process-data", "generate-reports"]
        
        **Conditional Cleanup:**
        
        .. code-block:: yaml
        
            # Clean up regardless of whether main actions succeeded
            - name: remove-temp-resources
            after: ["deploy-app"]
            condition: "True"  # Always run cleanup
        
        **Best Practices:**
        
        - Use ``after`` for cleanup, notification, and optimization actions
        - Use ``depends_on`` when this action actually needs results from others
        - Combine with conditions for robust cleanup that runs regardless of failures
        - Keep after lists focused - too many can create execution bottlenecks""",
        default=None,
    )

    save_outputs: bool | None = Field(
        alias="SaveOutputs",
        description="""Controls whether action outputs are saved to the state system with namespace organization.

        **Output Organization:**
        
        When ``save_outputs`` is ``True`` (default), action outputs are automatically
        organized using the ``output_namespace`` property derived from the action name:
        
        - Action calls ``set_output("key", value)``
        - Actual state key becomes ``{namespace}/key`` 
        - Enables organized access to outputs from other actions
        
        **Namespace Calculation:**
        
        The output namespace is derived from the action name:
        
        .. code-block:: python
        
            # Simple names use the full name as namespace
            "deploy-stack" → namespace: "deploy-stack"
            
            # Hierarchical names use first component  
            "myapp:action/deploy" → namespace: "myapp:output"
            "portfolio/app/deploy" → namespace: "portfolio"
        
        **Output Access Patterns:**
        
        **Direct Access:**
        
        .. code-block:: yaml
        
            # Reference specific action outputs in parameters
            params:
            vpc_id: "{{ actions['create-vpc'].outputs.vpc_id }}"
            subnet_ids: "{{ actions['create-subnets'].outputs.subnet_ids }}"
        
        **Namespace Access:**
        
        .. code-block:: yaml
        
            # Access outputs by namespace (multiple actions)
            params:  
            app_outputs: "{{ state['myapp:output'] }}"
            infra_config: "{{ state['infrastructure'] }}"
        
        **Performance Considerations:**
        
        - **Enable (True)**: Outputs available for other actions, organized by namespace
        - **Disable (False)**: Saves memory/storage, action outputs not accessible to others
        
        **When to disable:**
        
        - Actions that don't produce useful outputs for other actions
        - High-frequency actions that generate large amounts of temporary data  
        - Actions in performance-critical deployment paths
        - Temporary/utility actions whose outputs aren't needed downstream
        
        **State Structure Example:**
        
        .. code-block:: json
        
            {
            "state": {
                "myapp:output/vpc_id": "vpc-12345",
                "myapp:output/database_endpoint": "db.example.com",
                "infrastructure/load_balancer_arn": "arn:aws:elasticloadbalancing:...",
                "cleanup-temp/files_removed": 42
            }
            }""",
        default=None,
    )

    lifecycle_hooks: list["ActionSpec"] | None = Field(
        alias="LifecycleHooks",
        description="""List of ActionSpec objects that define hooks to execute at specific points in this action's lifecycle.

        **Lifecycle Hook System:**
        
        Lifecycle hooks allow you to define additional actions that run at specific
        points during the main action's execution, enabling complex workflows with
        setup, monitoring, and cleanup phases.
        
        **Hook Execution Points:**
        
        Hooks are executed at these lifecycle events:
        
        - **pre_execute**: Before the main action starts
        - **post_execute**: After the main action completes successfully  
        - **on_failure**: If the main action fails
        - **on_complete**: After the main action finishes (success or failure)
        
        **Hook Configuration:**
        
        Each hook is a full ActionSpec with its own kind, params, and conditions:
        
        .. code-block:: yaml
        
            lifecycle_hooks:
            - name: "pre-deploy-validation"
                kind: "AWS::ValidateTemplate"
                scope: "build"
                params:
                template: "{{ params.template }}"
                
            - name: "post-deploy-notification"  
                kind: "AWS::PutEvent"
                scope: "build"
                params:
                type: "STATUS"
                status: "DEPLOY_SUCCESS"
                message: "Stack {{ params.stack_name }} deployed successfully"
        
        **Common Hook Patterns:**
        
        **Validation Hooks:**
        
        .. code-block:: yaml
        
            lifecycle_hooks:
            - name: "validate-prerequisites"
                kind: "AWS::CheckDependencies"
                params:
                required_stacks: ["vpc-stack", "security-stack"]
        
        **Monitoring Hooks:**
        
        .. code-block:: yaml
        
            lifecycle_hooks:
            - name: "start-monitoring"
                kind: "AWS::EnableMonitoring"
                params:
                resource_arn: "{{ outputs.stack_arn }}"
                
            - name: "create-dashboard"
                kind: "AWS::CreateDashboard"  
                params:
                stack_name: "{{ params.stack_name }}"
        
        **Cleanup Hooks:**
        
        .. code-block:: yaml
        
            lifecycle_hooks:
            - name: "cleanup-temp-files"
                kind: "AWS::RemoveFiles"
                condition: "True"  # Always run cleanup
                params:
                path: "/tmp/deployment-{{ deployment.id }}"
        
        **Hook Execution Model:**
        
        - Hooks inherit the same execution context as the main action
        - Hook failures don't prevent the main action from executing
        - Hooks can access main action outputs through template variables
        - Hooks can have their own dependencies and conditions
        
        **Best Practices:**
        
        - Keep hooks focused and lightweight
        - Use conditions to control when hooks execute
        - Design hooks to be idempotent (safe to run multiple times)
        - Consider hook execution time impact on overall deployment
        - Use appropriate scopes for hook actions""",
        default=None,
    )

    @property
    def action_name(self) -> str:
        """Get the action name for this ActionSpec.

        Extracts the final component of the action name after the last '/' separator.
        This is used to identify the action in logs and other outputs, removing any
        namespace prefixes.

        Returns:
            The action name without namespace prefix. Returns empty string if name is empty.

        Examples:
            >>> action = ActionSpec(name="deploy-stack", kind="AWS::CreateStack", params={})
            >>> action.action_name
            'deploy-stack'

            >>> action = ActionSpec(name="myapp:action/deploy", kind="AWS::CreateStack", params={})
            >>> action.action_name
            'deploy'

            >>> action = ActionSpec(name="portfolio/app/branch/action-name", kind="AWS::CreateStack", params={})
            >>> action.action_name
            'action-name'

        Notes:
            This property extracts the meaningful action identifier from potentially
            complex namespaced names. The namespace portion is used for organization
            while the action name is used for identification and logging.
        """
        return self.name.split("/")[-1] if self.name else ""

    @property
    def output_namespace(self) -> str | None:
        """Calculate the output namespace for action results.

        The output namespace is used to group action outputs in the state system
        when `save_outputs` is enabled. It transforms the action name into a
        namespace suitable for organizing output data.

        The namespace is derived from the action name by:
        1. Taking the first part before any '/' separator
        2. Replacing ':action' suffix with ':output' if present
        3. Returning None if save_outputs is False or name is empty

        Returns:
            The calculated output namespace string, or None if outputs should
            not be saved or if the name is invalid.

        Examples:
            >>> action = ActionSpec(name="deploy-stack", kind="AWS::CreateStack", params={})
            >>> action.output_namespace
            'deploy-stack'

            >>> action = ActionSpec(name="myapp:action/deploy", kind="AWS::CreateStack", params={})
            >>> action.output_namespace
            'myapp:output'

            >>> action = ActionSpec(name="deploy-stack", kind="AWS::CreateStack",
            ...                    params={}, save_outputs=False)
            >>> action.output_namespace is None
            True

        Notes:
            The output namespace is used by the action execution system to organize
            outputs in the state. When an action calls `set_output("key", value)`,
            the actual state key becomes `{namespace}/key` if a namespace exists.
        """
        # Early return if outputs should not be saved or name is invalid
        if self.save_outputs is False or not self.name:
            return None

        # Split on '/' and take the first part for namespace
        namespace_part = self.name.split("/")[0]

        # Return None if the first part is empty (shouldn't happen with validation)
        if not namespace_part:
            return None

        # Replace ':action' suffix with ':output' if present
        return namespace_part.replace(":action", ":output")

    @property
    def state_namespace(self) -> str | None:
        """Get the state namespace for this ActionSpec.

        The state namespace is used to organize action outputs in the state system.
        It transforms the action name by replacing ':action/' with ':var/' to create
        a consistent namespace for variable storage.

        Returns:
            The state namespace string, or None if the name is empty.

        Examples:
            >>> action = ActionSpec(name="namespace:action/action-name", kind="AWS::CreateStack", params={})
            >>> action.state_namespace
            'namespace:var/action-name'

            >>> action = ActionSpec(name="simple-name", kind="AWS::CreateStack", params={})
            >>> action.state_namespace
            'simple-name'

        Notes:
            This property transforms action namespaces into variable namespaces for
            consistent state organization. The ':action/' pattern becomes ':var/'
            to distinguish between action definitions and variable storage.
        """
        namespace_part = self.name

        # Return None if the first part is empty (shouldn't happen with validation)
        if not namespace_part:
            return None

        # Replace ':action/' suffix with ':var/' if present
        return namespace_part.replace(":action/", ":var/")

    @model_validator(mode="before")
    @classmethod
    def handle_deprecations(cls, values: Any) -> Any:
        """Handle the deprecation of 'label' and 'type' fields in favor of 'name' and 'kind'.

        This validator provides backward compatibility by mapping deprecated field names
        to their new equivalents and issuing appropriate warnings.

        Args:
            values: The input values for model creation. Expected to be a dict for processing,
                   but other types are passed through unchanged.

        Returns:
            The validated and potentially modified values with deprecated fields
            mapped to their new equivalents.

        Raises:
            ValueError: If conflicting values are provided for both old and new field names.

        Examples:
            >>> # Handles legacy field names automatically
            >>> legacy_data = {"label": "my-action", "type": "AWS::CreateStack"}
            >>> values = ActionSpec.handle_deprecations(legacy_data)
            >>> print(values["name"])
            'my-action'

        Warnings:
            Issues DeprecationWarning when deprecated fields are used.
        """
        if isinstance(values, dict):
            # Handle label -> name deprecation
            label_value = values.pop("label", None) or values.pop("Label", None)
            name_value = values.pop("name", None) or values.pop("Name", None)

            if label_value and not name_value:
                warnings.warn(
                    "The 'label' field is deprecated and will be removed in a future version. "
                    "Please use 'name' instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                name_value = label_value
            elif label_value and name_value:
                if label_value != name_value:
                    raise ValueError(
                        f"Conflicting values: label='{label_value}' and name='{name_value}'. "
                        "Please use only 'name' as 'label' is deprecated."
                    )
                warnings.warn(
                    "The 'label' field is deprecated. Please use only 'name'.",
                    DeprecationWarning,
                    stacklevel=2,
                )

            values["name"] = name_value

            # Handle type -> kind deprecation
            type_value = values.pop("type", None) or values.pop("Type", None)
            kind_value = values.pop("kind", None) or values.pop("Kind", None)

            if type_value and not kind_value:
                warnings.warn(
                    "The 'type' field is deprecated and will be removed in a future version. "
                    "Please use 'kind' instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                kind_value = type_value
            elif type_value and kind_value:
                if type_value != kind_value:
                    raise ValueError(
                        f"Conflicting values: type='{type_value}' and kind='{kind_value}'. "
                        "Please use only 'kind' as 'type' is deprecated."
                    )
                warnings.warn(
                    "The 'type' field is deprecated. Please use only 'kind'.",
                    DeprecationWarning,
                    stacklevel=2,
                )

            values["kind"] = kind_value

        return values

    @field_validator("depends_on", mode="before")
    @classmethod
    def validate_depends_on(cls, value) -> list[str]:
        """Validate and normalize depends_on field values.

        Args:
            value: The depends_on value to validate. Can be a string, list of strings, or None.

        Returns:
            A list of dependency names. Empty list if None was provided.

        Raises:
            ValueError: If value is not a string, list of strings, or None.
                       If any item in a list is not a string.

        Examples:
            >>> ActionSpec.validate_depends_on(None)
            []
            >>> ActionSpec.validate_depends_on("single-dep")
            ['single-dep']
            >>> ActionSpec.validate_depends_on(["dep1", "dep2"])
            ['dep1', 'dep2']
        """
        if value is None:
            return []
        if value == "null":
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            # Validate all items are strings
            for item in value:
                if not isinstance(item, str):
                    raise ValueError(
                        f"All items in depends_on must be strings, got {type(item)}"
                    )
            return value
        raise ValueError(
            f"Invalid depends_on value: {value}. Must be a string or a list of strings"
        )

    @field_validator("kind", mode="before")
    @classmethod
    def validate_action_kind(cls, value) -> str:
        """Validate and normalize action kind values.

        Removes 'aws.' prefix from kind values for backward compatibility.

        Args:
            value: The kind value to validate and normalize.

        Returns:
            The normalized kind value with 'aws.' prefix removed if present.

        Examples:
            >>> ActionSpec.validate_action_kind("AWS::CreateStack")
            'AWS::CreateStack'
            >>> ActionSpec.validate_action_kind("aws.create_stack")
            'create_stack'
        """
        if value and isinstance(value, str):
            if value.startswith("aws."):
                value = value.lstrip("aws.")
        return value

    @field_validator("scope", mode="before")
    @classmethod
    def validate_scope(cls, value) -> str:
        """Validate that scope is one of the allowed values.

        Args:
            value: The scope value to validate.

        Returns:
            The validated scope value.

        Raises:
            ValueError: If scope is not one of the allowed values.

        Examples:
            >>> ActionSpec.validate_scope("build")
            'build'
            >>> ActionSpec.validate_scope("invalid")
            ValueError: Invalid scope: invalid. Must be one of: ['build', 'branch', 'app', 'portfolio']
        """
        scope_list = cls.get_scope_list()
        if value not in scope_list:
            raise ValueError(f"Invalid scope: {value}. Must be one of: {scope_list}")
        return value

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, value: str) -> str:
        """Validate that name follows the format required for action_name and output_namespace properties.

        The name field supports hierarchical namespaces and action identification:
        - Used by action_name property (extracts part after last '/')
        - Used by output_namespace property (extracts part before first '/' and transforms :action to :output)

        Args:
            value: The name value to validate.

        Returns:
            The validated name value.

        Raises:
            ValueError: If name is empty, contains invalid characters, starts/ends with hyphen,
                       has invalid structure, or exceeds maximum length.

        Examples:
            >>> ActionSpec.validate_name_format("deploy-stack")
            'deploy-stack'
            >>> ActionSpec.validate_name_format("myapp:action/deploy")
            'myapp:action/deploy'
            >>> ActionSpec.validate_name_format("invalid name")
            ValueError: Name 'invalid name' must contain only alphanumeric characters...
        """
        import re

        if not value or not value.strip():
            raise ValueError("Name cannot be empty or whitespace")

        # Allow alphanumeric, hyphens, underscores, colons, and forward slashes
        if not re.match(r"^[a-zA-Z0-9_:/-]+$", value):
            raise ValueError(
                f"Name '{value}' must contain only alphanumeric characters, hyphens, underscores, "
                f"colons, and forward slashes. No spaces or other special characters allowed."
            )

        # Cannot start or end with hyphen or forward slash
        if value.startswith(("-", "/")) or value.endswith(("-", "/")):
            raise ValueError(
                f"Name '{value}' cannot start or end with a hyphen or forward slash"
            )

        # Check for consecutive separators or invalid separator combinations
        if "//" in value or ":/" in value or "/:" in value:
            raise ValueError(
                f"Name '{value}' cannot contain consecutive separators or invalid separator combinations"
            )

        # Validate individual path components
        parts = value.split("/")
        for i, part in enumerate(parts):
            if not part:  # Empty part indicates consecutive slashes
                raise ValueError(f"Name '{value}' cannot contain empty path components")

            # First part can contain colons (for namespace designation like "myapp:action")
            # Subsequent parts should not contain colons (action names)
            if i > 0 and ":" in part:
                raise ValueError(
                    f"Name '{value}' cannot contain colons in action name part '{part}'. "
                    f"Colons are only allowed in the namespace portion (before first '/')"
                )

            # Each part cannot start or end with hyphen
            if part.startswith("-") or part.endswith("-"):
                raise ValueError(
                    f"Name '{value}' part '{part}' cannot start or end with a hyphen"
                )

            # Each part must contain only valid characters
            valid_chars = r"^[a-zA-Z0-9_:-]+$" if i == 0 else r"^[a-zA-Z0-9_-]+$"
            if not re.match(valid_chars, part):
                char_desc = (
                    "alphanumeric characters, hyphens, underscores, and colons"
                    if i == 0
                    else "alphanumeric characters, hyphens, and underscores"
                )
                raise ValueError(
                    f"Name '{value}' part '{part}' must contain only {char_desc}"
                )

        # AWS resource name compatibility
        if len(value) > 63:
            raise ValueError(
                f"Name '{value}' is too long. Maximum length is 63 characters."
            )

        # Validate that if colons are used, they follow the expected pattern
        if ":" in value:
            namespace_part = parts[0]
            if namespace_part.count(":") > 1:
                raise ValueError(
                    f"Name '{value}' namespace part '{namespace_part}' can contain at most one colon"
                )

            # If colon exists, validate the format (should be like "namespace:type")
            if ":" in namespace_part:
                ns_parts = namespace_part.split(":")
                if len(ns_parts) != 2 or not ns_parts[0] or not ns_parts[1]:
                    raise ValueError(
                        f"Name '{value}' namespace part '{namespace_part}' must follow format 'namespace:type'"
                    )

        return value

    @field_validator("before", "after", mode="before")
    @classmethod
    def validate_action_lists(cls, value) -> list[str] | None:
        """Validate before/after action lists.

        Args:
            value: The before/after value to validate. Can be a string, list of strings, or None.

        Returns:
            A list of action names or None if input was None.

        Raises:
            ValueError: If value is not a string, list of strings, or None.
                       If any item in a list is not a string.

        Examples:
            >>> ActionSpec.validate_action_lists(None)
            None
            >>> ActionSpec.validate_action_lists("single-action")
            ['single-action']
            >>> ActionSpec.validate_action_lists(["action1", "action2"])
            ['action1', 'action2']
        """
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            # Validate all items are strings
            for item in value:
                if not isinstance(item, str):
                    raise ValueError(
                        f"All items in list must be strings, got {type(item)}"
                    )
            return value
        raise ValueError("Must be a string or a list of strings")

    @model_validator(mode="after")
    def validate_no_self_dependency(self) -> "ActionSpec":
        """Validate that action doesn't depend on itself.

        Returns:
            The validated instance.

        Raises:
            ValueError: If the action depends on itself through depends_on, before, or after fields.

        Examples:
            >>> action = ActionSpec(name="test", kind="AWS::CreateStack", params={}, depends_on=["test"])
            ValueError: Action 'test' cannot depend on itself
        """
        if self.name in self.depends_on:
            raise ValueError(f"Action '{self.name}' cannot depend on itself")
        if self.before and self.name in self.before:
            raise ValueError(f"Action '{self.name}' cannot be before itself")
        if self.after and self.name in self.after:
            raise ValueError(f"Action '{self.name}' cannot be after itself")
        return self

    @classmethod
    def get_scope_list(cls) -> list[str]:
        """Get the list of valid scopes.

        Returns:
            List of valid scope values ordered from most specific to least specific.

        Examples:
            >>> ActionSpec.get_scope_list()
            ['build', 'branch', 'app', 'portfolio']
        """
        return ["build", "branch", "app", "portfolio"]

    def has_dependencies(self) -> bool:
        """Check if this action has any dependencies.

        Returns:
            True if the action has dependencies, False otherwise.

        Examples:
            >>> action = ActionSpec(name="test", kind="AWS::CreateStack", params={})
            >>> action.has_dependencies()
            False
            >>> action.depends_on = ["other-action"]
            >>> action.has_dependencies()
            True
        """
        return bool(self.depends_on)

    def is_conditional(self) -> bool:
        """Check if this action has a condition.

        Returns:
            True if the action has a condition, False otherwise.

        Examples:
            >>> action = ActionSpec(name="test", kind="AWS::CreateStack", params={})
            >>> action.is_conditional()
            False
            >>> action.condition = "deployment.environment == 'production'"
            >>> action.is_conditional()
            True
        """
        return self.condition is not None

    def get_execution_order_dependencies(self) -> list[str]:
        """Get all dependencies that affect execution order.

        Returns:
            List of dependency names including depends_on and before dependencies.

        Examples:
            >>> action = ActionSpec(
            ...     name="test",
            ...     kind="AWS::CreateStack",
            ...     params={},
            ...     depends_on=["dep1", "dep2"],
            ...     before=["after1"]
            ... )
            >>> deps = action.get_execution_order_dependencies()
            >>> print(sorted(deps))
            ['after1', 'dep1', 'dep2']
        """
        dependencies = self.depends_on.copy()
        if self.before:
            dependencies.extend(self.before)
        return dependencies

    # Backward compatibility properties
    @property
    def label(self) -> str:
        """DEPRECATED: Use 'name' instead. Returns the name value for backward compatibility.

        Returns:
            The name value.

        Warnings:
            Issues DeprecationWarning when this property is accessed.

        Examples:
            >>> action = ActionSpec(name="test-action", kind="AWS::CreateStack", params={})
            >>> label = action.label  # Triggers deprecation warning
            >>> print(label)
            'test-action'
        """
        warnings.warn(
            "The 'label' property is deprecated. Use 'name' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.name

    @property
    def type(self) -> str:
        """DEPRECATED: Use 'kind' instead. Returns the kind value for backward compatibility.

        Returns:
            The kind value.

        Warnings:
            Issues DeprecationWarning when this property is accessed.

        Examples:
            >>> action = ActionSpec(name="test", kind="AWS::CreateStack", params={})
            >>> action_type = action.type  # Triggers deprecation warning
            >>> print(action_type)
            'AWS::CreateStack'
        """
        warnings.warn(
            "The 'type' property is deprecated. Use 'kind' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.kind

    @property
    def action(self) -> str:
        """The action to perform as defined by the execute.actionlib module.

        This property returns the value of the 'kind' field for backward compatibility
        and action library integration.

        Returns:
            The action kind value.

        Examples:
            >>> action = ActionSpec(name="test", kind="AWS::CreateStack", params={})
            >>> print(action.action)
            'AWS::CreateStack'
        """
        return self.kind

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Override to exclude None values and use aliases by default.

        Args:
            **kwargs: Keyword arguments passed to the parent model_dump method.
                     All standard Pydantic model_dump parameters are supported.

        Returns:
            Dictionary representation of the model with None values excluded by default
            and field aliases used.

        Examples:
            >>> action = ActionSpec(name="test", kind="AWS::CreateStack", params={})
            >>> data = action.model_dump()
            >>> print("Name" in data)  # Uses alias
            True
            >>> print(None in data.values())  # None values excluded
            False
        """
        if "exclude_none" not in kwargs:
            kwargs["exclude_none"] = True
        if "by_alias" not in kwargs:
            kwargs["by_alias"] = True
        return super().model_dump(**kwargs)

    @model_serializer
    def ser_model(self, info: SerializationInfo) -> OrderedDict:
        """Serialize the model to an OrderedDict in a specific field order.

        Respects exclude_none and by_alias parameters, and uses Field aliases
        for consistent serialization output.

        Args:
            info: Serialization information containing exclude_none and by_alias settings.

        Returns:
            Serialized model data in the specified field order.

        Examples:
            >>> action = ActionSpec(name="test", kind="AWS::CreateStack", params={})
            >>> from pydantic import SerializationInfo
            >>> info = SerializationInfo(exclude_none=True, by_alias=True)
            >>> data = action.ser_model(info)
            >>> list(data.keys())[0]  # First field in order
            'Name'
        """
        exclude_none = info.exclude_none
        by_alias = info.by_alias

        # Define field order for consistent serialization
        field_order = [
            "name",
            "kind",
            "depends_on",
            "params",
            "scope",
            "condition",
            "before",
            "after",
            "save_outputs",
            "lifecycle_hooks",
        ]

        out = OrderedDict()
        for field in field_order:
            value = getattr(self, field)
            if exclude_none and value is None:
                continue
            if exclude_none and isinstance(value, list) and len(value) == 0:
                continue

            # Get the alias from the Field definition if by_alias is True
            if by_alias:
                field_info = ActionSpec.model_fields.get(field)
                if field_info and field_info.alias:
                    key = field_info.alias
                else:
                    key = field
            else:
                key = field

            # For nested models, call their model_dump if needed
            if hasattr(value, "model_dump"):
                value = value.model_dump(exclude_none=exclude_none, by_alias=by_alias)
            elif isinstance(value, list) and value and hasattr(value[0], "model_dump"):
                value = [
                    item.model_dump(exclude_none=exclude_none, by_alias=by_alias)
                    for item in value
                ]

            out[key] = value
        return out

    def __str__(self) -> str:
        """Return a human-readable string representation.

        Returns:
            String showing key attributes for identification.

        Examples:
            >>> action = ActionSpec(name="deploy-stack", kind="AWS::CreateStack", params={})
            >>> str(action)
            "ActionSpec(name='deploy-stack', kind='AWS::CreateStack', scope='build')"
        """
        return (
            f"ActionSpec(name='{self.name}', kind='{self.kind}', scope='{self.scope}')"
        )

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging.

        Returns:
            Detailed representation showing name and kind for debugging.

        Examples:
            >>> action = ActionSpec(name="deploy-stack", kind="AWS::CreateStack", params={})
            >>> repr(action)
            "ActionSpec(Kind='AWS::CreateStack',Name='deploy-stack')"
        """
        return f"ActionSpec(Kind='{self.kind}',Name='{self.name}')"
