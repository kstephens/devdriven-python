from typing import List
from dataclasses import dataclass
import smtplib
import html

@dataclass
class Email:
  subject: str
  recipients: List[str]
  body: str
  sender: str
  server: str

  def message(self) -> str:
        return f'''From: {self.sender}
To: {', '.join(self.recipients)}
Subject: {self.subject}
MIME-Version: 1.0
Content-Type: text/html; charset=utf-8
Content-Disposition: inline

<html><body><pre style="font: monospace">
{html.escape(self.body)}
</pre></body></html>
'''

  def send(self) -> dict:
    success, error = False, None
    smtp = smtplib.SMTP(self.server)
    recipients = ', '.join(self.recipients)
    try:
      # smtp.set_debuglevel(1)
      smtp.sendmail(self.sender, recipients, self.message())
      success = True
    # pylint: disable-next=broad-except
    except Exception as exc:
      error = exc
    finally:
      smtp.quit()
    return {
      'subject': self.subject,
      'recipients': recipients,
      'success': success,
      'error': error,
    }
