# stiss_pattern = rf"""({stiss_exception_pattern})|([.!?]+(?:\.\.\.)?)\s+(?=["\'(\[{{‚„'"]?\s*[A-Z\u00C0-\u00DC])|([.!?]+)$"""

# stiss_pattern = rf"""
# (                           # Group 1: Exception patterns - matched first, no split occurs
#     {stiss_exception_pattern}  # Inline the pre-built exception pattern (e.g. abbreviations, Mr., etc.)
# )
# |                           # OR
# (                           # Group 2: Mid-sentence ending punctuation
#     [.!?]+                  # One or more sentence-ending punctuation marks (handles ?! or ... etc.)
# )
# \s+                         # One or more whitespace characters after the punctuation
# (?=                         # Positive lookahead - next part must be present but isn't consumed:
#     ["'(\[{{‚„]?            #   Optional opening quote, bracket, or fancy quote character
#     \s*                     #   Optional whitespace (e.g. "( Hello" style spacing)
#     [A-Z\u00C0-\u00DC]      #   Must be followed by uppercase letter (Latin or extended Latin/accented)
# )
# |                           # OR
# (                           # Group 3: Sentence ending at end of string
#     [.!?]+                  # One or more sentence-ending punctuation marks
# )
# $                           # Must be at the very end of the string
# """


# |
#     (  # 3. stop at end of text  FIXME not needed as we don't need to split at the very end
#         {STOP_WESTERN}+
#         {CLOSING_MODIFIERS}*
#         \s+  # require spacing
#         |
#         {STOP_CJK}+
#     )$

		# Sentence end at end of string
		if match.group(3):
			return match.group(3)
