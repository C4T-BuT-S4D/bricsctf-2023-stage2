# Notify User Guide

Since our lovely service is in the beta testing stage, we haven't connected it to any external Mail Services yet, and instead use a local mail server setup for testing. In order to connect to it and read the notification emails, there are a few steps that need to be performed.

## Website

Begin by registering an account on the website, exposed on port 7777. You can then start creating notifications, but their status and content will only appear on the website itself.

## Mail client

To actually receive and read the notifications, connect a mail client of your choice (Apple Mail, Mozilla Thunderbird, etc) using `{username}@notify` as the email, and `{username}` as your account username, where the "{username}" stands for the username you have registered with on the website, specifying the host where Notify is launched as the inbound and outbound IMAP server address. If you encounter issues with logging in, check that authentication over plaintext is enabled, since there are no custom TLS certificates installed.
