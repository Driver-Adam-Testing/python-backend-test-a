import os

# config/settings.py
import os

class Settings:
    # Declare all settings (no defaults, since they must exist in env)
    DEPLOYMENT_ENVIRONMENT: str
    AWS_REGION: str
    AWS_ACCOUNT: str
    BASE_URL: str
    CORS_ORIGINS: str
    # METRICSLAMBDA_CW_ALARM:str
    BACKEND_ALLOWED_IPS:str
    ONBOARDING_LAMDBA_API_URL:str
    ONBOARDING_LAMDBA_AUTH0_URL:str
    ONBOARDING_LAMDBA_AUTH0_AUDIENCE:str
    ONBOARDING_LAMDBA_CLIENT_ID:str

    BACKEND_ENABLE_ROLLBACK:str
    #NONE CDK STUFF TODO Remove in setEnh.sh container load world
    POSTGRES_SERVER:str
    POSTGRES_PORT:str
    POSTGRES_DB:str
    POSTGRES_USER:str
    #POSTGRES_PASSWORD:str
    SECRECTS_NAME:str
    #ASYNC_DATABASE_URL:str
    AUTH0_DOMAIN:str
    AUTH0_MGMT_API_DOMAIN:str
    AUTH0_CLIENT_ID:str
    AUTH0_AUDIENCE:str
    AUTH0_MGMT_API_CLIENT_ID:str
    # AUTH0_MGMT_API_CLIENT_SECRET:str
    AUTH0_MGMT_API_AUDIENCE:str
    # MODAL_TOKEN_ID:str
    # MODAL_TOKEN_SECRET:str
    # MODAL_ENVIRONMENT:str
    # S3ADMIN_AWS_ACCESS_KEY_ID:str
    # S3ADMIN_AWS_SECRET_ACCESS_KEY:str
    GH_CLIENT_ID:str
    # GH_CLIENT_SECRET:str
    GH_REDIRECT_URI:str
    # GH_WEBHOOK_SECRET:str
    # GH_CLIENT_PEM_SECRET:str
    # OPENAI_API_KEY:str
    # SENTRY_DSN:str
    SECRECTS_KEYS:str
    # add more as needed...
    IS_PRIVATE_DEPLOY:bool
    ALLOWED_AWS_ACCOUNT:str

    def __init__(self, prefix: str = "") -> None:
        missing = []

        for name in self.__annotations__:
            env_key = f"{prefix}{name}" if prefix else name
            val = os.getenv(env_key)

            if val is None:
                if hasattr(self.__class__, name):
                    setattr(self, name, getattr(self.__class__, name))
                else:
                    missing.append(env_key)
            else:
                setattr(self, name, val)

        if missing:
            raise EnvironmentError(
                f"Missing required environment variable(s): {', '.join(missing)}"
            )
        print("Environment settings loaded " + self.DEPLOYMENT_ENVIRONMENT + " " + self.AWS_ACCOUNT + " " + self.AWS_REGION)

    def to_dict(self) -> dict[str, str]:
        """Return settings as a dict of {name: value}."""
        return {name: getattr(self, name) for name in self.__annotations__}

    def to_json(self, **kwargs) -> str:
        """Return settings as a JSON string."""
        return json.dumps(self.to_dict(), **kwargs)

# One shared instance
settings = Settings(prefix="")  # or prefix="MYAPP_"