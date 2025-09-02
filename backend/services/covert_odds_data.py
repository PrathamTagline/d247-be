from typing import Dict, Any


def get_market_type_key(mname: str, gtype: str = None) -> str:
    """
    Determine market type key based on mname and gtype.
    Returns a normalized key for grouping similar markets.
    """
    mname_lower = mname.lower() if mname else ""
    gtype_lower = gtype.lower() if gtype else ""

    if "bookmaker" in mname_lower:
        return "bookmaker"
    elif "fancy" in mname_lower or "fancy" in gtype_lower:
        return "fancy"
    elif "match" in mname_lower or "odds" in mname_lower:
        return "odds"
    elif "session" in mname_lower:
        return "session"
    elif "toss" in mname_lower:
        return "toss"
    else:
        return mname_lower.replace(" ", "_") if mname_lower else "unknown"


def get_market_type_name(mname: str, gtype: str = None) -> str:
    """
    Get the standardized market type name for the markettype field.
    """
    market_key = get_market_type_key(mname, gtype)

    type_mapping = {
        "bookmaker": "BOOKMAKER",
        "fancy": "FANCY",
        "odds": "ODDS",
        "session": "SESSION",
        "toss": "TOSS"
    }

    return type_mapping.get(market_key, market_key.upper()) 


def convert_odds_format(source_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert odds data from source format to target format with mname separation.
    """
    try:
        data_section = None

        if "odds" in source_data and "data" in source_data["odds"]:
            data_section = source_data["odds"]["data"]
        elif "highlight" in source_data and "data" in source_data["highlight"]:
            highlight_data = source_data["highlight"]["data"]
            if isinstance(highlight_data, dict):
                data_section = []
                for key in ["t1", "t2"]:
                    if key in highlight_data and isinstance(highlight_data[key], list):
                        data_section.extend(highlight_data[key])
            elif isinstance(highlight_data, list):
                data_section = highlight_data
        elif "data" in source_data:
            data_section = source_data["data"]
        elif isinstance(source_data, list):
            data_section = source_data

        if not data_section or not isinstance(data_section, list):
            print("No valid data structure found in source data")
            return {}

        if not data_section:
            return {}

        first_event = data_section[0]

        result = {
            "eventid": str(first_event.get("gmid", "")),
            "eventName": first_event.get("ename", ""),
            "updateTime": None,
            "status": "ACTIVE",
            "inplay": first_event.get("iplay", False),
            "sport": {"name": None},
            "isLiveStream": None,
            "markets": {}
        }

        for event in data_section:
            if not isinstance(event, dict):
                continue

            if not event.get("section") or not isinstance(event["section"], list):
                continue

            mname = event.get("mname", "")
            gtype = event.get("gtype", "")
            market_type = get_market_type_name(mname, gtype)

            market = {
                "marketId": str(event.get("mid", "")),
                "market": mname,
                "status": event.get("status", ""),
                "inplay": event.get("iplay", False),
                "totalMatched": None,
                "active": None,
                "markettype": market_type,
                "min": str(event.get("min", "")),
                "max": str(event.get("max", "")),
                "runners": []
            }

            for section in event["section"]:
                if not section or not isinstance(section, dict):
                    continue

                runner = {
                    "runnerName": section.get("nat", "").strip(),
                    "selectionId": section.get("sid", 0),
                    "status": section.get("gstatus", ""),
                    "back": [],
                    "lay": [],
                    "runner": section.get("nat", "").strip()
                }

                if section.get("odds") and isinstance(section["odds"], list):
                    back_odds = [
                        odd for odd in section["odds"]
                        if odd.get("otype") == "back" and odd.get("odds", 0) > 0
                    ]
                    for level, odd in enumerate(back_odds):
                        runner["back"].append({
                            "rate": str(odd.get("odds", 0)),
                            "size": odd.get("size", 0),
                            "price": None,
                            "level": level
                        })

                    lay_odds = [
                        odd for odd in section["odds"]
                        if odd.get("otype") == "lay" and odd.get("odds", 0) > 0
                    ]
                    for level, odd in enumerate(lay_odds):
                        runner["lay"].append({
                            "rate": str(odd.get("odds", 0)),
                            "size": odd.get("size", 0),
                            "price": None,
                            "level": level
                        })

                market["runners"].append(runner)

            if market["runners"]:
                mname_key = mname.strip() if mname else "unknown"
                if mname_key not in result["markets"]:
                    result["markets"][mname_key] = []
                result["markets"][mname_key].append(market)

        all_statuses = []
        for markets in result["markets"].values():
            for market in markets:
                all_statuses.append(market["status"])

        if all_statuses:
            if "SUSPENDED" in all_statuses:
                result["status"] = "SUSPENDED"
            elif "OPEN" in all_statuses:
                result["status"] = "OPEN"
            elif "CLOSED" in all_statuses:
                result["status"] = "CLOSED"
            else:
                result["status"] = all_statuses[0]

    except (KeyError, TypeError, AttributeError) as e:
        print(f"Error converting odds data: {e}")
        return {}

    return result