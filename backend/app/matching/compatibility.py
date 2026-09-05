from typing import List, Tuple

# Mapping of Donor Full Blood Group (e.g. "O+") -> Recipient Full Blood Groups that can accept it
COMPATIBILITY_MAP = {
    "O-": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
    "O+": ["O+", "A+", "B+", "AB+"],
    "A-": ["A-", "A+", "AB-", "AB+"],
    "A+": ["A+", "AB+"],
    "B-": ["B-", "B+", "AB-", "AB+"],
    "B+": ["B+", "AB+"],
    "AB-": ["AB-", "AB+"],
    "AB+": ["AB+"]
}

def is_blood_compatible(donor_blood_group: str, donor_rh: str, recipient_blood_group: str, recipient_rh: str) -> bool:
    """
    Deterministic ABO and Rh compatibility check.
    Returns True if donor blood can be given to recipient.
    """
    donor_full = f"{donor_blood_group.upper()}{donor_rh}"
    recipient_full = f"{recipient_blood_group.upper()}{recipient_rh}"
    
    compatible_recipients = COMPATIBILITY_MAP.get(donor_full, [])
    return recipient_full in compatible_recipients

def get_compatible_donor_types(recipient_blood_group: str, recipient_rh: str) -> List[Tuple[str, str]]:
    """
    Returns list of (blood_group, rh_factor) donor types compatible for a recipient.
    """
    recipient_full = f"{recipient_blood_group.upper()}{recipient_rh}"
    compatible_types = []
    
    for donor_type, allowed_recipients in COMPATIBILITY_MAP.items():
        if recipient_full in allowed_recipients:
            bg = donor_type[:-1]
            rh = donor_type[-1]
            compatible_types.append((bg, rh))
            
    return compatible_types
