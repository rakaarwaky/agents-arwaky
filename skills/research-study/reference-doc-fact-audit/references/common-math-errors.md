# Common Math Errors in LLM-Written Reference Docs

These are the specific failure modes found when auditing a vector / linear-algebra
reference document. For each, the left form is wrong and the right form is verified.

## Orthogonality claims

A "show these are orthogonal" exercise that the doc asserts with a specific pair is the
most common error. Always recompute the dot product before accepting it.

- Wrong: `(2,−1,3)·(1,2,1) = 0` (orthogonal).
  Correct: `2(1)+(−1)(2)+3(1) = 3 ≠ 0`. Not orthogonal.

The fix is to replace the pair with one that actually is orthogonal, or to reword the
exercise as "find an orthogonal pair" and give the answer the user must verify.

## Dual basis values

The dual basis of a basis B′ = {v₁, v₂} is defined by eᵢ*(vⱼ) = δᵢⱼ. The components
of eᵢ* in the standard basis are **not** the components of vᵢ.

- Wrong: B′ = {(1,1),(1,−1)} has dual basis e₁* = (1,1), e₂* = (1,−1).
  Correct: solve x+y = 1, x−y = 0 → x = y = 1/2, so e₁* = (1/2, 1/2).
  Similarly e₂* = (1/2, −1/2).
  Values on the standard basis: e₁*(1,0) = e₁*(0,1) = 1/2; e₂*(1,0) = 1/2, e₂*(0,1) = −1/2.

## Axiom counts

The standard list of vector-space axioms is ten, not eight. The two most commonly
omitted are:

- 1·u = u (identity scalar).
- 0·u = 0 (zero scalar).

If the prose says "eight axioms" but the list has only eight, the two are missing.
Add them and update the count to ten.

## Axiom completeness check

When auditing any axiom list, verify the count in the prose matches the number of items
listed AND that the list is complete. A list of eight labelled "ten" is the same defect
as the wrong count. The full ten-axiom set is:

1. Closure under addition.
2. Commutativity.
3. Associativity of addition.
4. Additive identity.
5. Additive inverse.
6. Closure under scalar multiplication.
7. Distributivity.
8. Scalar associativity.
9. 1·u = u.
10. 0·u = 0.

## Subspace / span sign errors

`span{(2,−1)}` and `span{(−2,1)}` are the same subspace. A sign flip in a basis vector
is not an error. Do not report it.

## Broken link vs plain-text mention

A backticked filename in prose (`` `s01-reference.md` ``) is a mention, not a link.
It only needs fixing if the file does not exist AND the doc promises the reader will
find it there. A real markdown link (`[text](path)`) that points to a missing file is
a broken link and must be fixed.
