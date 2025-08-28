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
    METRICSLAMBDA_CW_ALARM:str
    BACKEND_ALLOWED_IPS:str
    ONBOARDING_LAMDBA_API_URL:str
    ONBOARDING_LAMDBA_AUTH0_URL:str
    ONBOARDING_LAMDBA_AUTH0_AUDIENCE:str
    POSTGRES_PASSWORD:str
    # add more as needed...

    def __init__(self, prefix: str = "") -> None:
        missing = []

        for name in self.__annotations__:
            env_key = f"{prefix}{name}" if prefix else name
            val = os.getenv(env_key)

            if val is None:
                missing.append(env_key)
            else:
                setattr(self, name, val)

        if missing:
            raise EnvironmentError(
                f"Missing required environment variable(s): {', '.join(missing)}"
            )
        print("Environment settings loaded " + self.DEPLOYMENT_ENVIRONMENT + " " + self.AWS_ACCOUNT + " " + self.AWS_REGION)

# One shared instance
settings = Settings(prefix="")  # or prefix="MYAPP_"