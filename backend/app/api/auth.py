from fastapi_auth0 import Auth0, Auth0User

auth = Auth0(domain="driverai.us.auth0.com", api_audience="http://localhost")

Auth0User = Auth0User
