import pcre2
import logging
import json
from services.settings import settings_service
from services.rag import rag_service
from utils.formatters import clean_response
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RegexEngineService:
    def __init__(self):
        """Initialize regex engine service."""
        self.service_name = "regex_engine"

    def _normalize_regex_output(self, response: str) -> str:
        """Normalize LLM output into a usable regex string.

        Handles JSON-wrapped strings/objects and safely unescapes backslashes.
        """
        cleaned = clean_response(response)

        parsed = None
        try:
            parsed = json.loads(cleaned)
        except Exception:
            parsed = None

        if isinstance(parsed, dict):
            cleaned = parsed.get("regex") or parsed.get("pattern") or cleaned
        elif isinstance(parsed, list) and parsed:
            first = parsed[0]
            cleaned = first if isinstance(first, str) else cleaned
        elif isinstance(parsed, str):
            cleaned = parsed

        if isinstance(cleaned, str):
            cleaned = cleaned.strip()
            cleaned = cleaned.replace("\\\\", "\\")

        return cleaned
        

    def run_regex_match(self, log: str, pattern: str):
        """
        Returns one standard dictionary for all regex use cases.

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
            logger.warning(
                "Expected regex to be a string, got %s. Converting to string.",
                type(regex),
            )
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
    
    def generate_regex_v1(self, log: str) -> Dict[str, Any]:
        logger.info("Generating regex (v1)...")

        system_prompt = settings_service.get_prompts_settings("generate_regex")
        active_siem = settings_service.get_active_siem()
        result = rag_service.query_rag(
            user_prompt=log, 
            system_prompt=system_prompt,
            filter_category=f"{active_siem}_fields"
        )

        if not result["success"]:
            return {
                "success": False,
                "regex": None,
                "error": result["error"],
                "latency": result["latency"]
            }

        # Clean + normalize
        regex = self._normalize_regex_output(result["content"])
        if not regex.endswith("$"):
            regex += "$"

        return {
            "success": True,
            "regex": regex,
            "error": None,
            "latency": result["latency"]
        }
    
    
    def generate_regex_v2(self, log: str, fix_count: int) -> Dict[str, Any]:
        logger.info("Generating regex (v2)...")

        system_prompt = settings_service.get_prompts_settings("generate_regex")
        active_siem = settings_service.get_active_siem()
        remaining = log
        final_regex = ""
        total_latency = 0.0
        failure_count = 0
        
        for i in range(fix_count):
            remaining_stripped = remaining.strip()
            if not remaining_stripped:
                logger.info("Remaining log empty, stopping.")
                break

            logger.info("Generating regex round %s...", i + 1)
            result = rag_service.query_rag(
                user_prompt=remaining, 
                system_prompt=system_prompt,
                filter_category=f"{active_siem}_fields"
            )
            total_latency += result.get("latency", 0)

            if not result["success"]:
                return {
                    "success": False,
                    "regex": final_regex or None,
                    "error": result["error"],
                    "latency": total_latency
                }

            raw = self._normalize_regex_output(result["content"])
            if not raw.endswith("$"):
                raw += "$"

            # reduce to longest valid partial match
            reduced = regex_engine_service.run_reduce_regex(remaining, raw)["regex"]
            logger.info(f"Reduced regex: {reduced}")

            # match it
            match_info = regex_engine_service.run_regex_match(remaining, reduced)
            matched_value = match_info["full"]["value"]
            end = match_info["full"]["end"]

            # check if regex failed to advance
            if match_info["status"] == "Unmatched" or end == 0:
                failure_count += 1
                logger.warning(f"Regex failed to match or advance. Failure count: {failure_count}")
                if failure_count >= 3:
                    final_regex += r"\s?.*"
                    logger.warning("Too many failures, appending wildcard and stopping.")
                    break
                continue  # try next round without updating remaining

            failure_count = 0  # reset on success

            # append to final regex
            if final_regex:
                if reduced:
                    final_regex += r"\s?" + reduced
                else:
                    final_regex += reduced
            else:
                final_regex = reduced

            # move forward
            remaining = remaining[end:]
            logger.info(f"Remaining log for next round: {remaining}")

        # post-process result
        final_regex = self.resolve_duplicate_capture_groups(final_regex)

        return {
            "success": True,
            "regex": final_regex,
            "error": None,
            "latency": total_latency
        }


    def fix_regex(self, log: str, regex: str) -> Dict[str, Any]:
        
        # shrink to longest matching core
        longest = regex_engine_service.run_reduce_regex(log, regex)
        longest_end = longest["end"]
        remaining_text = log[longest_end:] if longest_end is not None else ""
        result = self.generate_regex_v2(remaining_text, fix_count=3)

        if not result["success"]:
            return {
                "success": False,
                "regex": None,
                "error": result["error"],
                "latency": result["latency"]
            }

        # Assemble without re-normalizing the assembled regex
        prefix = longest.get("regex", "") or ""
        suffix = result.get("regex", "") or ""
        fixed = f"{prefix}{suffix}"
        fixed = self.resolve_duplicate_capture_groups(fixed)
        if not fixed.endswith("$"):
            fixed += "$"

        # Validate compilation
        try:
            pcre2.compile(fixed)
        except Exception as e:
            return {
                "success": False,
                "regex": None,
                "error": f"CompileError: {e}",
                "latency": result["latency"]
            }

        # Validate match quality; try a spacer if needed
        match_info = regex_engine_service.run_regex_match(log, fixed)
        if match_info["status"] == "Unmatched" and prefix and suffix:
            fixed_spaced = f"{prefix}\\s?{suffix}"
            fixed_spaced = self.resolve_duplicate_capture_groups(fixed_spaced)
            if not fixed_spaced.endswith("$"):
                fixed_spaced += "$"
            try:
                pcre2.compile(fixed_spaced)
                match_info = regex_engine_service.run_regex_match(log, fixed_spaced)
                if match_info["status"] != "Unmatched":
                    fixed = fixed_spaced
            except Exception:
                pass

        if match_info["status"] == "Unmatched":
            return {
                "success": True,
                "regex": fixed,
                "warning": "Fixed regex did not match input log",
                "match_status": match_info["status"],
                "error": None,
                "latency": result["latency"]
            }

        return {
            "success": True,
            "regex": fixed,
            "warning": None,
            "match_status": match_info["status"],
            "error": None,
            "latency": result["latency"]
        }
    
    def resolve_duplicate_capture_groups(self, regex: str) -> str:
        """Resolve duplicate named capture groups by appending incremental numbers.
        
        Args:
            regex: The regex pattern to process
            
        Returns:
            Processed regex with unique capture group names
        """
        # Pattern to match named capture groups like (?P<name> or (?<name>
        pattern = pcre2.compile(r'(\(\?(?:P?<|<))(\w+)(>)')
        seen = {}
        offset = 0

        # Iterate over matches
        for match in list(pattern.finditer(regex)):
            group_name = match.group(2)
            if group_name in seen:
                # Increment counter for duplicate names
                seen[group_name] += 1
                new_name = f"{group_name}_{seen[group_name]}"
                
                # Replace the duplicate name
                start, end = match.span(2)
                regex = regex[:start + offset] + new_name + regex[end + offset:]
                offset += len(new_name) - len(group_name)
            else:
                seen[group_name] = 0
        
        logger.info(f"Resolved duplicate capture groups: {seen}")
        return regex


regex_engine_service = RegexEngineService()