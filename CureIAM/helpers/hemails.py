import email
import smtplib
from CureIAM.helpers import hlogging

_log = hlogging.get_logger(__name__)

def send(from_addr, to_addrs, subject, content,
               host='', port=0, ssl_mode='ssl',
               username='', password='', debug=0):
    """Send email message.

    When ``ssl_mode` is ``'ssl'`` and ``host`` is uspecified or
    specified as ``''`` (the default), the local host is used. When
    ``ssl_mode`` is ``'ssl'`` and ``port`` is unspecified or specified
    as ``0``, the standard SMTP-over-SSL port, i.e., port 465, is used.
    See :class:`smtplib.SMTP_SSL` documentation for more details on
    this.

    When ``ssl_mode`` is ``'ssl'` and if ``host`` or ``port`` are
    unspecified, i.e., if host or port are ``''`` and/or ``0``,
    respectively, the OS default behavior is used. See
    :class:`smtplib.SMTP` documentation for more details on this.

    We recommend these parameter values:

    - Leave ``ssl_mode`` unspecified (thus ``'ssl'`` by default) if
      your SMTP server supports SSL.

    - Set ``ssl_mode`` to ``'starttls'`` explicitly if your SMTP server
      does not support SSL but it supports STARTTLS.

    - Set ``ssl_mode`` to ``'disable'`` explicitly if your SMTP server
      supports neither SSL nor STARTTLS.

    - Set ``host`` to the SMTP hostname or address explicitly.

    - Leave ``port`` unspecified (thus ``0`` by default), so that the
      appropriate port is chosen automatically.

    With these recommendations, this function should do the right thing
    automatically, i.e., connect to port 465 if ``use_ssl`` is
    unspecified or ``False`` and port 25 if ``use_ssl`` is ``True``.

    Note that in case of SMTP, there are two different encryption
    protocols in use:

    - SSL/TLS (or implicit SSL/TLS): SSL/TLS is used from the beginning
      of the connection. This occurs typically on port 465. This is
      enabled by default (``ssl_mode`` as ``'ssl'``).

    - STARTTLS (or explicit SSL/TLS): The SMTP session begins as a
      plaintext session. Then the client (this function in this case)
      makes an explicit request to switch to SSL/TLS by sending the
      ``STARTTLS`` command to the server. This occurs typically on port
      25 or port 587. Set ``ssl_mode`` to ``'starttls'`` to enable this
      behaviour

    If ``username`` is unspecified or specified as an empty string, no
    SMTP authentication is done. If ``username`` is specified as a
    non-empty string, then SMTP authentication is done.

    Arguments:
        from_addr (str): Sender's email address.
        to_addrs (list): A list of :obj:`str` objects where each
            :obj:`str` object is a recipient's email address.
        subject (str): Email subject.
        content (str): Email content.
        host (str): SMTP host.
        port (int): SMTP port.
        ssl_mode (str): SSL mode to use: ``'ssl'`` for SSL/TLS
            connection (the default), ``'starttls'`` for STARTTLS, and
            ``'disable'`` to disable SSL.
        username (str): SMTP username.
        password (str): SMTP password.
        debug (int or bool): Debug level to pass to
            :meth:`SMTP.set_debuglevel` to debug an SMTP session. Set to
            ``0`` (the default) or ``False`` to disable debugging. Set
            to ``1`` or ``True`` to see SMTP messages. Set to ``2`` to
            see timestamped SMTP messages.

    """
    log_data = ('from_addr: {}; to_addrs: {}; subject: {}; host: {}; '
                'port: {}; ssl_mode: {}'
                .format(from_addr, to_addrs, subject, host, port, ssl_mode))
    try:
        if ssl_mode == 'ssl':
            smtp = smtplib.SMTP_SSL(host, port)
            smtp.set_debuglevel(debug)
        elif ssl_mode == 'starttls':
            smtp = smtplib.SMTP(host, port)
            smtp.set_debuglevel(debug)
            smtp.starttls()
        elif ssl_mode == 'disable':
            smtp = smtplib.SMTP(host, port)
            smtp.set_debuglevel(debug)
        else:
            _log.error('Cannot send email; %s; error: %s: %s', log_data,
                       'invalid ssl_mode', ssl_mode)
            return

        if username:
            smtp.login(username, password)

        msg = email.message.EmailMessage()
        msg['From'] = from_addr
        msg['To'] = ', '.join(to_addrs)
        msg['Subject'] = subject
        msg.set_content(content)

        smtp.send_message(msg)
        smtp.quit()

        _log.info('Sent email successfully; %s', log_data)

    except Exception as e:
        _log.error('Failed to send email; %s; error: %s: %s', log_data,
                   type(e).__name__, e)