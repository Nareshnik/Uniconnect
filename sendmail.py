
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from datetime import datetime


def send_mail(mail_mail, subject, msg):

    print("Sending Mail", mail_mail, subject, msg)


    # Email configuration
    sender_email = "studentdesknnrg@gmail.com"
    receiver_email = mail_mail
    receiver_email = receiver_email.split(",")


    # Create MIME object
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ', '.join(receiver_email)
    message["Subject"] = subject


    # HTML content with inline CSS for a fancy look
    html_content = f"""
    <html>
    <head>
        <style>
        body {{
            font-family: 'Arial', sans-serif;
            background-color: #f4f4f4;
            text-align: center;
        }}
        .container {{
            padding: 23px;
            border-radius: 10px;
            background-color: #f1f1f1e3;
            max-width: 600px;
            margin: 20px auto;
            border: 2px solid #976363;
        }}
        h1 {{
            color: #3498db;
        }}
        
        .inner_div {{
            color: #7a2992; 
            font-weight: bold;  
            text-align: start;
            font-size: 14px;
        }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Hello,</h1>

            <div class='inner_div'> <b style='color:blue'>{msg} </b>.</div>  
            <br>


            <br>
            <br>

            <div class='inner_div'>
            Kindly open Student Desk Website and do the Needful.
            <br>
            Best regards,
            <br>
            </div>
            
        </div>
    </body>
    </html>
    """



# input_sendmail_list =[username,useremail, idflight,flightn,msg,mail_source,mail_destination,mail_time,mail_price]


    # Attach HTML content to the MIME object
    message.attach(MIMEText(html_content, "html"))

    # Connect to the SMTP server (e.g., Gmail)
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "studentdesknnrg@gmail.com"
    smtp_password = "wimfgetsagziwlse"

    # Start TLS connection
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()

    # Login to the email account
    server.login(smtp_username, smtp_password)

    # Send the email
    server.sendmail(sender_email, receiver_email, message.as_string())

    # Quit the server
    server.quit()

        
    return "Mail Sent Successfully"


#if __name__ == "__main__":
    #send_mail("santosh.excellent123gmail.com, santosh.awesome@oulook.com,", "Test Mail 5", "This is Message")

