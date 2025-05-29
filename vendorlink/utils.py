import os

from django.core.mail import EmailMessage


class Util:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data["subject"],
            body=data["body"],
            from_email=os.environ.get("EMAIL_FROM"),
            to=[data["to_email"]],
        )
        email.send()

    def send_verification_email(user):
        subject = "Vendor Account Verified"
        message = (
            f"Dear {user.first_name},\n\n"
            "We are pleased to inform you that your vendor account has been verified and is now active.\n\n"
            "Before logging into your vendor dashboard, please complete your vendor profile here:\n"
            f"http://127.0.0.1:3000/vendor/profile/{user.user_id}/\n\n"
            "Once your profile is set up, you can log in and start managing your vendor activities.\n\n"
            "Thank you for joining us!\n\n"
            "Best regards,\n"
            "Vendora"
        )
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=os.environ.get("EMAIL_FROM"),
            to=[user.email],
        )
        email.send()


from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class Util:
    @staticmethod
    def send_email1(subject, to_email, template_name, context):
        # Render the HTML email content
        html_content = render_to_string(template_name, context)

        # Generate plain-text fallback from context if needed (optional)
        text_content = context.get("plain_text", "Please view this email in HTML.")

        # Compose email
        email = EmailMultiAlternatives(subject, text_content, to=[to_email])
        email.attach_alternative(html_content, "text/html")

        email.send()
