# Email sending utilities can be placed here
from app.utils.helpers import OTP_EXPIRY_MINUTES

def send_otp_mail(email: str, otp: str):
    print(
        f"OTP:{otp} has been sended to {email} "
        f"that will expire in {OTP_EXPIRY_MINUTES} minutes"
    )
