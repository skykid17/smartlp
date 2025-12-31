import pcre2


class RegexEngineService:
    def __init__(self):
        """Initialize regex engine service."""
        self.service_name = "regex_engine"
        

    def run_regex_match(self, log: str, pattern: str):
        """
        Unified regex engine returning one standard dictionary for all regex use cases.

        Returns:
            {
                "status": "Matched" | "Partially Matched" | "Unmatched",
                "error": str or None,
                "full": { "value": str, "start": int, "end": int } or None,
                "groups": [
                    { "name": "field_name", "value": ..., "start": ..., "end": ... },
                    ...
                ]
            }
        """

        result = {
            "status": "Unmatched",
            "error": None,
            "full": None,
            "groups": [],
        }

        # Compile
        try:
            prog = pcre2.compile(pattern)
        except Exception as e:
            result["status"] = "Unmatched"
            result["error"] = f"CompileError: {e}"
            return result

        # Search (partial match)
        m = prog.search(log)
        if not m:
            return result    # Unmatched

        # Full match span
        try:
            full_val  = m.group(0)
            full_start = m.start()
            full_end = m.end()
        except Exception:
            full_val = m.group(0)
            full_start = 0
            full_end = len(log)

        result["full"] = {
            "value": full_val,
            "start": full_start,
            "end": full_end
        }

        # Check full match
        is_full = False
        try:
            is_full = bool(prog.fullmatch(log))
        except Exception:
            pass

        result["status"] = "Matched" if is_full else "Partially Matched"

        # Extract groups
        groupindex = getattr(prog, "groupindex", {})

        # Named groups
        for name, idx in groupindex.items():
            try:
                val = m.group(idx)
                if val is not None:
                    result["groups"].append({
                        "name": name,
                        "value": val,
                        "start": m.start(idx),
                        "end": m.end(idx)
                    })
            except Exception:
                continue

        # Numbered groups
        named_indices = set(groupindex.values())
        total = m.lastindex or 0

        for i in range(1, total + 1):
            if i in named_indices:
                continue
            try:
                val = m.group(i)
                if val is None:
                    continue
                result["groups"].append({
                    "name": f"group{i}",
                    "value": val,
                    "start": m.start(i),
                    "end": m.end(i)
                })
            except Exception:
                continue

        return result

    def run_reduce_regex(self, log: str, regex: str) -> dict:
        """
        Reduce the regex by shortening it until it produces
        the longest valid partial match using run_regex_match().
        
        Returns dict:
        {
            "regex": reduced_regex,
            "matched_text": <substring>,
            "start": <int>,
            "end": <int>,
        }
        """
        if not isinstance(regex, str):
            self.log_warning(f"Expected regex to be a string, got {type(regex)}. Converting to string.")
            regex = str(regex)
        
        best = {
            "regex": "",
            "matched_text": "",
            "start": None,
            "end": None,
            "length": 0
        }

        # Try progressively reducing the regex from right-to-left
        for cut in range(len(regex), 0, -1):
            candidate = regex[:cut]

            # Try compiling
            try:
                pcre2.compile(candidate)
            except Exception:
                continue  # skip invalid patterns

            # Run unified matcher
            match = self.run_regex_match(log, candidate)

            # Skip invalid or fully invalid
            if match["status"] == "Unmatched":
                continue
            
            # A partial or full match exists
            full = match["full"]
            if not full:
                continue

            match_text = full["value"]
            match_len = len(match_text)

            # Keep the candidate that yields the longest match
            if match_len > best["length"]:
                best = {
                    "regex": candidate,
                    "matched_text": match_text,
                    "start": full["start"],
                    "end": full["end"],
                    "length": match_len
                }

            # If it's a full match of the entire log, stop early
            if match_text == log:
                break
        
        # Return final results without "length"
        return {
            "regex": best["regex"],
            "matched_text": best["matched_text"],
            "start": best["start"],
            "end": best["end"],
        }

regex_engine_service = RegexEngineService()