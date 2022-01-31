import smtplib
#SERVER = "localhost"

FROM = 'monty@python.com'

TO = ["martin.bell@uts.edu.au"] # must be a list

SUBJECT = "Hello!"

TEXT = "This message was sent with Python's smtplib."

# Prepare actual message

message = """\
From: %s
To: %s
Subject: %s

%s
""" % (FROM, ", ".join(TO), SUBJECT, TEXT)

# Send the mail

server = smtplib.SMTP('myserver')
server.sendmail(FROM, TO, message)
server.quit()



	 

