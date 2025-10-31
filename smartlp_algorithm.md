### Algorithm Pseudocode for Regex Generation v1

1. Initialize:
   - Requrest a regex from LLM for log

2. Loop for count in fixCount:
   a. If regex fully matches log
      - terminate loop

   b. Reduce the generated regex to longest matching pattern.

   c. Request a fixed regex from LLM for log

3. Return regex


### Algorithm Pseudocode for Regex Generation v2

1. Initialize:
   - regex ← ""
   - remaining_log ← log
   - processed_segments ← empty set
   - count ← 0

2. Loop while remaining_log is not empty and count <= fixCount:
   a. Request a regex from LLM for remaining_log.
      - If request fails, terminate loop.

   b. Reduce the generated regex to longest matching pattern.

   c. Compile and search for the reduced regex in remaining_log.
      - If no match, terminate loop.

   d. Identify matched_part as the first matched segment.

   e. Determine index of matched_part in remaining_log.

   f. If matched_part is not at the start of remaining_log:
      - Prepend ".+?" to reduced_regex.

   g. Slice remaining_log to exclude matched_part and preceding content.

   h. If matched_part is already in processed_segments:
      - Terminate loop to prevent infinite processing.

   i. Add matched_part to processed_segments.

   j. Update regex:
      - If regex is not empty, append reduced_regex.
      - Otherwise, set regex to reduced_regex.

   k. Increment count and continue.

3. Resolve duplicate named groups in the regex

4. Return regex.
