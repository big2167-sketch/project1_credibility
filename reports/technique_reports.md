# Project 1 - Credibility Scoring Technique Report (Deliverable 2)

## Overview
This project implements a draft credibility scoring function for a reference URL. The goal is to produce a lightweight, explainable score that can run in real time inside an application UI.

The scoring output is a JSON object:
```json
{ "score": 0.0, "explanation": "..." }

## Methodology

This is a heuristic-based prototype intended for Deliverable 1 and early feasibility demonstration.

### Signals Used

#### Domain Suffix Prior
- `.gov` and `.edu` are treated as more reliable starting points.
- `.org` is treated as moderately reliable (depends on organization).
- `.com` is treated as variable credibility.

#### Accessibility and Transport
- URLs that fail to load or return non-2xx status are penalized.
- HTTPS adds a small positive signal.

#### Content Indicators
The function fetches the page and extracts:
- Page title presence
- Approximate text length (substantial vs thin content)
- Hints for authorship ("By ...", "author", "written by")
- Hints for date ("published", "updated", year patterns)
- Hints for references ("references", "doi", "PMID", "bibliography")

### Score Construction
The final score is a sum of:
- a base score,
- domain prior adjustments,
- additive bonuses/penalties from the indicators above.

The score is clamped to the range **[0, 1]**.

### Why This Approach Is Appropriate (Draft Phase)
- **Fast**: simple parsing and a small number of regex checks.
- **Explainable**: each score component contributes to a human-readable explanation.
- **Robust**: graceful handling of invalid URLs, timeouts, and non-HTML content.

### Error Handling
- Invalid inputs return `score = 0.0` with a clear explanation.
- Network failures or bad status codes return a reduced score with reason included.
- Non-HTML content returns a valid output with limited analysis.

### Complexity and Scalability Considerations
- Each call performs one HTTP request and a parsing step.
- At scale, performance could be improved via:
  - caching repeated URLs,
  - limiting fetch size,
  - async/concurrent requests,
  - domain reputation databases,
  - ML models trained on labeled credibility datasets.

### Benchmark Results

- Serial:
- Concurrent:

## Future Improvements

- Add structured signals such as author metadata tags and publisher verification.
- Incorporate ML-based scoring trained on labeled credibility datasets.
- Introduce whitelist/blacklist or reputation services.
- Add source-type classification (academic paper vs blog vs government site).
