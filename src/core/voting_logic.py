def rtl_voting_logic(threat_pred, type_pred, jammer_pred):
    """
    RTL Deterministic Voting Logic (Hardware Boolean Gate)
    
    Inputs:
        threat_pred: Boolean (True if Threat detected)
        type_pred:   Integer (0: WiFi, 1: DJI, 2: Jammer)
        jammer_pred: Boolean (True if Jamming signal detected)
        
    Returns:
        action_code: 0: STANDBY, 1: ALERT_THREAT, 2: ALERT_JAMMING
        status: String message
    """
    
    # Rule 1: If Jammer=1 -> OVERRIDE Type. Alert: JAMMING!
    if jammer_pred:
        return 2, "ALERT: JAMMING DETECTED! (High Entropy / Wiener Noise)"
        
    # Rule 2: If Threat=0 -> RESET. Status: BENIGN / STANDBY
    if not threat_pred:
        return 0, "SYSTEM STATUS: BENIGN / STANDBY"
        
    # Rule 3: If Threat=1 AND Jammer=0 -> Trust Type head classification
    if threat_pred and not jammer_pred:
        if type_pred == 1:
            return 1, "ALERT: DJI DRONE DETECTED! (Pulse Edge Analysis)"
        elif type_pred == 0:
            return 0, "STATUS: WiFi DETECTED (Benign DSSS)"
        elif type_pred == 2:
            # Type head says Jammer, but Jammer head says Clear.
            # Usually, we trust the dedicated Jammer head or flag for review.
            return 2, "ALERT: POTENTIAL JAMMING DETECTED! (Type Head Flag)"
            
    return 0, "STATUS: UNDETERMINED"
