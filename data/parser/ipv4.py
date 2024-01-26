import re
import ipaddress

def is_valid_ipv4_address(ip_addr):
    try:
        # This will return True for both public and private IPv4 addresses
        return isinstance(ipaddress.ip_address(ip_addr), ipaddress.IPv4Address)
    except ValueError:
        return False

def parse(text):
    ipv4_regex = r'(?<!\d)(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?!\d)'
    matches = []

    for match in re.finditer(ipv4_regex, text):
        ip_addr = match.group()
        if is_valid_ipv4_address(ip_addr):
            start_pos, end_pos = match.span()
            matches.append((ip_addr, start_pos, end_pos))

    return matches

