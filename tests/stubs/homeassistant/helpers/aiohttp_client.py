def async_get_clientsession(hass, verify_ssl=True):
    hass.session.verify_ssl = verify_ssl  # the fake TrueNAS refuses a verified connection when it's self-signed
    return hass.session
