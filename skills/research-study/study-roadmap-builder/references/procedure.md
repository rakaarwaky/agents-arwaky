# Procedure — Study Roadmap Builder

1. **Ask (via `clarify`)** what the user is starting from, which domains,
   time budget, and goal. If already known, skip.
2. **Pick the 7 specific sub-fields** for the quarter in the user's
   priority order; design each to unlock a next-quarter field. Do NOT open a
   big CS/ML field in Q1 if the user wants science-first — lay the prereqs
   instead.
3. **Verify the hour budget honestly.** The rotation cap is the binding
   number: one field/day across ~7 fields = 1 session/field/week = ~12
   two-hour sessions (24 h) per field in a quarter, NOT the ~26 h
   theoretical max. Use ~12 sessions to decide how many section-subtopics a
   field can genuinely cover, and say so in the field doc.
4. **If the user points at a public roadmap** (e.g. roadmap.sh), FETCH ITS
   FULL TREE and expand each section into a FLAT file in the field folder.
   See `public-roadmap-api.md` for how to pull the content. Then TRIM the
   section list to the quarter's reachable scope (rotation cap) and name the
   rest as Q2 backlog — do not keep sections the user cannot finish.
5. **Scaffold the folder structure** (see `deliverable-structure.md`).
   Generate many files with a Python script written to a `.py` file and run
   via terminal — DO NOT inline large nested dicts in `execute_code`
   (paren-matching errors on big literals are likely). Keep the generator
   script out of the deliverable folder (delete it after).
6. **Update `README.md`** to point into the field folders + give the
   Mon–Sun rotation and the Q2 unlock map.
7. **Give the user a < 2 min "start now" action:** open the field-1 first
   section file and do the first checklist item.
