# Lab 05 — Conclusion

## 1. Which layer changed your results the most?

In my experiment, Layer 1 (Error Feedback) had the biggest impact on the results. Before adding this layer, the agent answered 16 out of 24 questions correctly, gave 4 wrong answers, and left 4 questions unanswered. After adding Layer 1, the results changed to 18 correct, 6 wrong, and 0 unanswered questions.

This happened because the agent could receive error messages from tools and try again instead of stopping immediately. However, I noticed that getting more answers did not always mean getting better answers. The number of wrong answers also increased from 4 to 6.

Layer 2 did not change the results. Layer 3 reduced wrong answers from 6 to 4, but the number of correct answers stayed the same.

Overall, I think Layer 1 mainly improved what the agent could do, while Layer 3 improved how it handled answers that were not supported by tool results.

## 2. One failure the full harness did not fix

One mistake that the full harness did not fix was question q17. The question asked how many percentage points the unemployment rate in Aktobe decreased between 2020 and 2023.

The agent correctly used the `get_series` tool and received the values 4.5% for 2020 and 4.1% for 2023. However, the mistake happened when it called the `calculate` tool. Instead of subtracting the two values, the model calculated a relative percentage change using `(4.5 - 4.1) / 4.5 * 100`. As a result, it answered 8.89 instead of the correct 0.4 percentage points.

Layer 3 did not reject this answer because 8.89 came from the calculator output.

To prevent similar mistakes, I would add a check that distinguishes percentage changes from percentage-point differences. This would not require extra model calls, but it would make the code more complex and could sometimes reject valid calculations.

## 3. Workflow or agent for the monthly ranking?

For Dala Insight's monthly ranking task, I would choose the fixed workflow because it was more accurate, faster, and less expensive in my experiment.

On the same 15 questions, the workflow answered 13 correctly, while the agent answered only 9. The workflow made no wrong answers and left 2 questions unanswered. The agent gave 2 wrong answers and left 4 unanswered.

The workflow also used fewer resources. It needed 15 model calls and 3,852 tokens, compared with 26 calls and 19,835 tokens for the agent. The workflow finished in 15.5 seconds, while the agent needed 51.7 seconds.

Since the company needs to repeat the same ranking task every month, I think a fixed workflow is more reliable and easier to control.

However, I would choose an agent for more complex questions that require several calculations, different tools, or flexible analysis.
