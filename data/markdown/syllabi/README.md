# Syllabi

Put one markdown file per syllabus here, named like `cs-439-<semester>-<professor>.md`.
Start each file with this header so ingestion can tag the chunks:

```markdown
---
course_code: CS 439
course_number: "39"
title: "Principles of Computer Systems"
doc_type: syllabus
semester: Fall 2025
professor: Jane Doe
source_url: https://...
---

# CS 439: Principles of Computer Systems

## Grading
...
```

`course_number` is the course number without its first (credit-hour) digit,
which matches how the catalog files are tagged.
