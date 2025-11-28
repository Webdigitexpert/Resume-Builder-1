from pydantic import BaseModel

class PhoneSchema(BaseModel):
    phone: str

class OTPVerifySchema(BaseModel):
    phone: str
    otp: int

class UserResponse(BaseModel):
    id: str
    phone: str
