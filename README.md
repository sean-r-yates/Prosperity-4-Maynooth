# Prosperity 4 Maynooth

This repo is our working record for IMC Prosperity 4.

It is not meant to read like a polished final paper, because we are still in the competition. It is a mixture of code, data, analysis, and the bits of work that actually mattered when the pressure started to rise.

## What This Repo Covers

This README only covers the rounds we have actually reached so far:

- `Round 1`
- `Round 2`
- `Round 3`

The folders in the repo are still split by round, but the writeup below focuses on the parts that are worth documenting right now.

## Repo Structure

- `Round 0 Tutorial` contains the tutorial material and early setup.
- `Round 1` contains the first round data capsule and the Round 1 trader.
- `Round 2` contains the second round data capsule and the trader file.
- `Round 3` contains the current round data and the report workflow for reading the voucher market.

<details>
<summary><h2>Round 1</h2></summary>

<h3>Files</h3>

- [Round 1 folder](./Round%201)
- [Round 1 trader](./Round%201/Trader_round_1.py)

<h3>Algo</h3>

Round 1 was the round where I just get something on the board. We were not as organized as we should have been, and I ended up cranking out the Python trader in one night so we had a working submission.

That trader is in [Round 1/Trader_round_1.py](./Round%201/Trader_round_1.py). It is not fancy, but it does what a first-round submission needed to do:

- build a fair price from the best bid and ask
- use order-book imbalance as a simple adjustment
- track a short rolling price history
- add a basic moving-average style directional signal
- take obvious value when it is there and otherwise make a market around fair value

It was a very practical file. The aim was not elegance. The aim was to get a trader live, functioning, and at least directionally sensible under time pressure.

<h3>Manual</h3>

The Round 1 manual was the welcome auction with `Dryland Flax` and `Ember Mushroom`. There was no continuous trading afterward, so the whole decision came down to one-shot auction pricing and sizing.

I bought both.

- For `Dryland Flax`, I bought `40k` volume at `28` and got `0` P&L.
- For `Ember Mushroom`, I bought `75k` volume at `16` and made about `+39k` P&L.

It was a simpler manual than what came later, but it still mattered.

</details>

<details>
<summary><h2>Round 2</h2></summary>

<h3>Files</h3>

- [Round 2 folder](./Round%202)
- [Round 2 trader](./Round%202/Trader_round_2.py)
- [Round 2 manual site repo](https://github.com/sean-r-yates/test)

<h3>Round Context</h3>

Round 2 was the second trading round and the final qualifier before the leaderboard reset for Phase 2. The products stayed the same, `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`, but the round added two extra layers:

- a one-time blind bid for extra market access on the algorithmic side
- a separate `Research / Scale / Speed` investment problem on the manual side

That made it a much more interesting round than Round 1. You were no longer just trying to trade well. You also had to think about access, field behaviour, and how much information the rest of the market had.

<h3>Algo</h3>

I did not work on the Round 2 algorithm, so I am leaving the implementation discussion open for the teammate who owned it.

The official Round 2 algo challenge, though, is worth summarizing because it shaped the round:

- the tradable products were still `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`
- the position limits were `80` for both products
- teams could add a `bid()` function to pay a one-time `Market Access Fee`
- the top `50%` of bidders got access to `25%` more order-book quotes
- accepted bids were subtracted from final Round 2 PnL

So the game was not just "build a better trader." It was also "how much should we bid for extra flow without overpaying?"

<h3>Manual</h3>

The Round 2 manual was the `Invest & Expand` challenge.

Each team had `50,000` XIRECs to allocate across three pillars:

- `Research`
- `Scale`
- `Speed`

The objective looked simple on paper:

`PnL = (Research x Scale x Speed) - Budget Used`

But the important twist was `Speed`, because speed was rank-based across the field. That meant the value of your own speed investment depended directly on what everyone else was doing. So the real problem was not just solving a formula. The real problem was estimating the market distribution of speed allocations well enough to make a smart submission.

That is where the website came in.

I built and pushed a small web tool that encouraged other participants to enter their own allocations. In return, the site showed them a polished market-style forecast and a live-looking snapshot of participant behaviour.

The public-facing snapshot was not a direct display of the real data we were collecting.

It was a deliberately mixed view built from:

- sampled real user submissions
- fake generated participants
- filtered back-end analytics

That was the point. If we had simply exposed the cleaned real dataset back to every user, we would have destroyed the advantage we were trying to build. Instead, the site gave people something believable and useful enough that they were happy to interact with it, while the actual high-quality signal stayed with us.

The honest version is this: I manipulated the crowd into thinking they were looking at a mostly real market estimate, while the visible output was actually a blend of real and fake data designed to preserve our edge.

That worked because the incentives lined up:

- people would not give away valuable allocation data for free
- they would share it if the site gave them something that felt helpful
- the site only needed to look credible, not literally mirror the true cleaned market state
- the real value came from filtering and cleaning the raw submissions behind the scenes

By the time we were done pushing it in Discord, the site had logged:

- `1,047` total attempts
- `138` real users
- a mixed market snapshot size of `207`

Some people did eventually realize what was going on and tried to distort the inputs. That was expected. On the back end, we filtered the data instead of trusting raw submissions blindly. Repeated identifiers, obviously distorted allocations, and low-quality noise could be screened out, which left us with a much stronger read on how real users were behaving.

That filtered data was the actual edge.

<h3>What We Submitted</h3>

This is the frustrating part.

Our team submitted:

- `30` research
- `30` scale
- `40` speed

That finished `227th`.

I also had an alliance with another team for information exchange, and they found the much better allocation:

- `17` research
- `41` scale
- `42` speed

That finished `20th`.

So the answer was there. After filtering and cleaning the data, the useful structure was already in what we had gathered. We just did not convert that edge into the submission we should have made ourselves.

<h3>Why Round 2 Matters</h3>

This was the first round where I felt like we did something more interesting than just work harder.

Anyone can use AI to build a slick site quickly. That is not the edge by itself. The edge came from recognizing that the actual scarce resource was information, then building a system that made people volunteer that information while feeling like they were mainly helping themselves.

That is the kind of edge I care about: relatively cheap to create, hard to copy cleanly, and based on understanding incentives rather than just grinding longer.

</details>

<details>
<summary><h2>Round 3</h2></summary>

<h3>Files</h3>

- [Round 3 folder](./Round%203)
- [Round 3 report source](./Round%203/round3_strategy_report.Rmd)
- [Round 3 report output](./Round%203/output/round3_strategy_report.html)

<h3>Notes</h3>

This round introduced:

- `HYDROGEL_PACK`
- `VELVETFRUIT_EXTRACT`
- the `VEV_*` voucher chain

For this round, the analysis is built around a single self-contained R Markdown report. The report focuses on four things:

- the price series for `HYDROGEL_PACK` and `VELVETFRUIT_EXTRACT`
- `VELVETFRUIT_EXTRACT` relative to the relevant voucher strikes
- voucher time value across the chain
- voucher liquidity through spread, trade count, and traded volume

When rendered, the HTML report and exported charts are written into `Round 3/output/`.

</details>

## Where The Repo Stands Now

This repo is intentionally honest about what is complete and what is not.

Round 1 has the trader I wrote under pressure and the opening auction outcome. Round 2 has the clearest example of us building an information edge on the manual side.

That is where we are right now: not at the end of the competition, but far enough in to know which parts were rushed, which parts were clever, and which parts are worth documenting properly.
