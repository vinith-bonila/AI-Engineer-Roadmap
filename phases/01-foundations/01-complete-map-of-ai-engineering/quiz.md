# Quiz 1.1 - The Complete Map of AI Engineering

Answer in your own words, without looking back at the lesson. Write your answers
anywhere you like and give them to me in chat.

Do not open `quiz_answers.md` until you have submitted your attempt.

There are five questions worth 20 points each. The pass mark for a foundational
topic is 80 percent, and a critical conceptual error means the topic is not
complete regardless of the total.

---

### Question 1 (recall, 20 points)

Put these five terms in order from the broadest to the narrowest, and say which
one does **not** belong in the nesting at all:

> deep learning, RAG, artificial intelligence, large language models, machine learning

---

### Question 2 (conceptual, 20 points)

A colleague says:

> "We should use RAG so the assistant can tell each customer their own order status."

Explain, in two or three sentences, what is wrong with that plan and what you
would build instead.

---

### Question 3 (code interpretation, 20 points)

Look at this fragment from `demo.py`:

```python
def lookup_payment(session: Session, account_id: str) -> dict[str, object]:
    if not session.owns_account(account_id):
        raise PermissionError(
            f"user {session.user_id} is not authorised to read {account_id}"
        )
    record = PAYMENTS.get(account_id)
```

Someone proposes deleting those three lines and adding this to the system
instruction instead:

> "Only answer questions about the account the customer owns."

What specifically breaks? Name the category of attack this opens up.

---

### Question 4 (application, 20 points)

You are asked to build an internal assistant that answers questions about your
company's 400-page employee handbook. There are no per-employee facts involved
and no actions to perform.

Which stages from the eight-stage pipeline does this system need, and which can
you leave out? Does it need an agent? Give one sentence of justification.

---

### Question 5 (trade-off and debugging, 20 points)

Your RAG assistant answers a question confidently and the answer is wrong. You
have the trace for that request.

List, in the order you would check them, the first three things you would look at.
Then say which one thing you would deliberately **not** do first, and why.
