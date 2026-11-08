# Jev Guardrail Evaluation

This repository explores TypeSafe AI's Jev as a fast evaluation layer for prompt-injection defense and other safety checks. The focus is whether a decision model can make useful, bounded judgments quickly enough to sit inline in an application request path, with a target of **under 200 ms**.

Jev is a decision model from TypeSafe AI. Instead of generating free-form text, it evaluates a supplied state against typed questions and returns structured answers, such as a yes/no probability, a choice, or a score. An application can use those answers to allow, block, review, route, or escalate a request. This makes Jev a natural candidate for checks that are well-defined and do not require multi-step investigation or a written explanation.

## Why Low-Latency Guardrails Matter

Safety checks are most useful when they run where a decision is made: before untrusted input reaches a model, before an agent acts on retrieved content, or before a tool call is executed. But every synchronous check adds time to the user-visible request. A guardrail that is too slow may be bypassed, run only on a fraction of traffic, or make an otherwise responsive product feel sluggish.

The challenge is not simply to find a fast classifier. A useful inline guardrail must balance:

- **Latency:** fit within the application's end-to-end budget, including network and service overhead.
- **Detection:** catch attacks and policy violations without letting too many through.
- **False positives:** avoid blocking legitimate requests, including benign text that discusses security or instructions.
- **Robustness:** hold up across direct and indirect prompt injection, different content types, languages, and obfuscations.
- **Operational behavior:** return predictable, usable decisions and provide a safe path for uncertain cases.

Generative-model judges can be flexible, but generating an explanation or a long response is unnecessary for many binary or categorical checks. Jev's bounded, structured decision interface and TypeSafe's reported speed make it a promising candidate for these narrow evaluations. It may also be useful for other safety evaluations, such as content-policy classification, tool-action review, or routing uncertain cases to a slower second check. Those use cases need their own questions, data, and validation; prompt-injection results do not establish performance on them.

## The Sub-200 ms Hypothesis

The working hypothesis is that Jev can provide a useful first-tier evaluation for prompt injection and related safety checks within a sub-200 ms latency budget for most requests. An independent evaluation of Jev as a prompt-injection guardrail reported **122 ms median latency and 223 ms p95** across 6,991 calls. The median is below this repository's target, while the p95 is above it; meeting the target consistently, including at the tail, remains an evaluation goal rather than an established result.

These are encouraging measurements, not a latency guarantee. The same study recorded a slowest call of 1.3 seconds. Latency depends on the model build, service, network, input size, and runtime conditions. This repository's focus is to evaluate the full tradeoff rather than treat speed as a substitute for security quality.

The same independent study illustrates why quality must be measured alongside speed:

- On the deepset prompt-injection benchmark, Jev achieved an AUC of 0.986, but its default 0.5 cutoff caught 58.6% of attacks while blocking none of the 399 safe prompts in that test.
- A cutoff selected on one half of that benchmark caught 81.7% of attacks on the held-out half with no false blocks. That cutoff did not transfer to other input types, where false blocks could rise substantially.
- The study reported especially strong resistance to over-blocking safe prompts containing trigger words, alongside weaker results for some embedded attacks, obfuscations, and non-European languages.

In other words, Jev looks like a strong candidate for **fast, bounded evaluation**, but a model score is not a universal security verdict. Question wording, context, threshold, model version, and content type all matter. A production design should use representative labelled data, a separate review band for uncertain cases, and layered controls such as least-privilege tool access and confirmation for sensitive actions.

## Evaluation Focus

This project is intended to assess Jev as a low-latency evaluator across:

- Direct prompt injection and jailbreak attempts.
- Indirect prompt injection in retrieved documents and other untrusted content.
- Other safety checks where a bounded decision is appropriate.
- Latency distributions, including median, p95, p99, and end-to-end overhead.
- Detection quality, false-block rates, threshold behavior, repeatability, and performance across input types.

Results should record the model build and evaluation configuration, and distinguish measurements on a benchmark from claims about production traffic. The goal is to identify where Jev is useful, where it is not, and when a slower or human review path is warranted.

## References

- [Introducing System One Models & Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev) — TypeSafe AI's introduction to Jev and its decision-model approach.
- [What is Jev and when to use it](https://mastra.ai/articles/jev) — examples of Jev for classifiers, workflow branching, tool approval, and content guardrails, including limitations.
- [Jev Guardrail Evaluation repository](https://github.com/Ruchith1018/jev-guardrail-evaluation) — independent prompt-injection evaluation code, data, results, and figures.
- [Evaluating Jev as a Prompt-Injection Guardrail](https://www.ruchith.space/Blog/testing-jev-as-a-guardrail/index.html) — the corresponding independent evaluation and discussion of findings, latency, thresholds, and deployment considerations.