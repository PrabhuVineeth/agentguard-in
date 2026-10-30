# Human Review Checklist for Indic-Language Tasks (data/review_checklist.md)

Machine-translated or synthetically generated Indic prompt injection tasks must be rigorously reviewed prior to final publication benchmarks.

Reviewers should evaluate each task against the following criteria:

## 1. Domain Terminology Accuracy
- [ ] **UPI Payments**: Are VPA handles, amounts, and notes preserved without translation garbling? (e.g. `user@okhdfcbank` must not be translated into Hindi/Kannada script).
- [ ] **IRCTC Ticketing**: Are train numbers (5-digit IDs), station abbreviations (e.g., SBC, NDLS), and passenger names phonetically authentic?
- [ ] **Government Welfare Forms**: Are official scheme names (e.g., *Post-Matric Scholarship*, *Jeevan Pramaan*, *Nadakacheri*) represented using authentic local administrative terms?
- [ ] **Email Assistant**: Are subject lines, formal salutations (e.g., *Namaste*, *Aadarniya*), and email addresses uncorrupted?

## 2. Injection Attack Naturalness
- [ ] **Attack Intent**: Does the translated attack text convey the same imperative authority or deceptive intent as the English template?
- [ ] **No Syntactic Leakage**: Ensure markers like `<system>` or markdown syntax are intentionally placed, not corrupted by translation tools.
- [ ] **Grammar and Fluency**: Is the Indic phrasing natural rather than literal word-for-word translation?

## 3. Reviewer Sign-off Protocol
When a task passes human review:
1. Set `human_reviewed = True` in the task JSON specification.
2. Record `review_notes` with reviewer initials, date, and any minor corrections made.
3. Update `CHANGELOG.md` with batch review status.
