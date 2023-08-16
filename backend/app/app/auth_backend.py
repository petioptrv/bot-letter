from starlette.authentication import AuthenticationBackend, AuthCredentials, SimpleUser


class BasicAuthBackend(AuthenticationBackend):
    async def authenticate(self, conn):
        return AuthCredentials(["authenticated"]), SimpleUser("test")
