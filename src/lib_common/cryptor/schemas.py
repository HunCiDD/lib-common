from typing import Dict

from pydantic import BaseModel, Field, SecretStr

# 根秘钥
class CryptorRootConfigsM(BaseModel):
    material: SecretStr
    salt: str
    secret: SecretStr


# 工作秘钥
class CryptorWorkConfigsM(BaseModel):
    secret: SecretStr
    xform: str = "aes/gcm/pkcs7"


class CryptorConfigsM(BaseModel):
    root: CryptorRootConfigsM = Field(default_factory=CryptorRootConfigsM, description="根秘钥")
    work: Dict[str, CryptorWorkConfigsM] = Field(default_factory=dict, description="工作秘钥")
