import re
import ipaddress

def is_private_ip(ip_addr):
    try:
        return ipaddress.ip_address(ip_addr).is_private
    except ValueError:
        return False

def parse(text):
    ipv4_regex = r'\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    matches = []

    for match in re.finditer(ipv4_regex, text):
        ip_addr = match.group()
        if is_private_ip(ip_addr):
            start_pos, end_pos = match.span()
            matches.append((ip_addr, start_pos, end_pos))

    return matches


