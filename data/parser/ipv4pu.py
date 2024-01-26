import re
import ipaddress

def is_public_ip(ip_addr):
    try:
        ip_obj = ipaddress.ip_address(ip_addr)
        return not ip_obj.is_private and not ip_obj.is_reserved and not ip_obj.is_loopback
    except ValueError:
        return False

def parse(text):
    ipv4_regex = r'\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    matches = []

    for match in re.finditer(ipv4_regex, text):
        ip_addr = match.group()
        if is_public_ip(ip_addr):
            start_pos, end_pos = match.span()
            matches.append((ip_addr, start_pos, end_pos))

    return matches
