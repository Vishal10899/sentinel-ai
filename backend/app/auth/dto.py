from dataclasses import dataclass


@dataclass(slots=True)
class UserDTO:
    user_id: str
    name: str
    email: str
    salt: str
    password_hash: str

    def public(self) -> dict[str, str]:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
        }