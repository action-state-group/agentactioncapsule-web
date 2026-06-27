#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate the agentactioncapsule.org docs layer as self-contained static HTML.

HashiCorp-style concept/docs pages in the neutral design family (ink/paper/indigo,
Inter + IBM Plex Mono). Each output file is single-file and self-contained — no
build step or framework is required to serve them; this generator only keeps the
shared chrome (tokens, nav, footer, sidebar) DRY at authoring time.

Run:  python3 tools/build_docs.py
Out:  docs/*.html  (one page per entry in PAGES, plus docs/index.html)

NEUTRALITY: these pages are neutral substrate only. No product, moat, Authority,
tiering, or monetization language. Standards status is stated honestly
(individual Internet-Draft; SCITT/COSE drafts are not yet RFCs).
"""
from __future__ import annotations

import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "docs"

DRAFT_URL = "https://datatracker.ietf.org/doc/draft-mih-scitt-agent-action-capsule/"
ORG_URL = "https://github.com/action-state-group"
ANCHOR_URL = "https://anchor.agentactioncapsule.org"
VERIFY_URL = "https://verify.actionstate.ai"

# Hybrid docs model: the site owns standard-level CONCEPTS; the canonical
# implementation/usage docs live in capsule-emit/docs (one fact, one home). Each
# concept page ends with a "Go deeper" link into the relevant canonical doc.
CE_DOCS = "https://github.com/action-state-group/capsule-emit/blob/main/docs"
GO_DEEPER = {
    "what-is-a-capsule": [("Concepts, in plain words", f"{CE_DOCS}/concepts.md"),
                          ("Anatomy of a capsule", f"{CE_DOCS}/anatomy.md")],
    "statement-vs-transparency-layer": [("Going deeper — the layers", f"{CE_DOCS}/going-deeper.md")],
    "what-is-a-transparency-service": [("The public log, explained", f"{CE_DOCS}/the-public-log-explained.md"),
                                       ("Why anchoring makes it trustworthy", f"{CE_DOCS}/why-anchoring.md")],
    "verifiable-data-structures": [("Going deeper", f"{CE_DOCS}/going-deeper.md")],
    "how-verification-works": [("Why anchoring makes it trustworthy", f"{CE_DOCS}/why-anchoring.md"),
                               ("The public log, explained", f"{CE_DOCS}/the-public-log-explained.md")],
    "quickstart": [("Tutorial: your first capsule", f"{CE_DOCS}/tutorials/01-your-first-capsule.md"),
                   ("Confirming &amp; chaining", f"{CE_DOCS}/tutorials/02-confirming-and-chaining.md")],
    "verify-a-capsule": [("Tutorial: reading your ledger", f"{CE_DOCS}/tutorials/03-reading-your-ledger.md")],
    "glossary": [("Concepts, in plain words", f"{CE_DOCS}/concepts.md")],
}


def go_deeper_html(slug: str) -> str:
    items = GO_DEEPER.get(slug)
    if not items:
        return ""
    links = " &middot; ".join(f'<a class="ln" href="{u}">{label} &#x2197;</a>' for label, u in items)
    return ('<div class="callout deeper"><strong>Go deeper</strong> &mdash; '
            f'implementation &amp; usage docs in <code>capsule-emit</code>: {links}</div>')

# Honest standards-status line, reused wherever status is relevant.
STATUS_NOTE = (
    "<strong>Status.</strong> The Agent Action Capsule profile is an individual "
    "IETF Internet-Draft (<code>draft-mih-scitt-agent-action-capsule</code>) — "
    "submitted for discussion, <em>not</em> adopted by a working group, and not a "
    "standard. It builds on the IETF SCITT and COSE drafts, which are themselves "
    "still in progress and not yet published as RFCs. RFC&nbsp;9162 (Certificate "
    "Transparency 2.0) is a published RFC."
)

# ---------------------------------------------------------------------------
# Shared chrome
# ---------------------------------------------------------------------------
CSS = """
  :root{
    --ink:#0B0E14; --ink-2:#161B25; --paper:#FCFCFA; --paper-2:#F4F4F0;
    --line:#E3E3DC; --line-2:#2A313F;
    --muted:#5C6573; --muted-2:#9AA3B2;
    --accent:#3A5BD9; --accent-soft:#EAEEFC;
    --verify:#127A52; --verify-soft:#E6F2EC;
    --mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
  }
  *{margin:0;padding:0;box-sizing:border-box}
  html{scroll-behavior:smooth}
  body{font-family:'Inter',system-ui,sans-serif;background:var(--paper);color:var(--ink);line-height:1.65;-webkit-font-smoothing:antialiased}
  a{color:inherit}
  .wrap{max-width:1140px;margin:0 auto;padding:0 32px}
  .mono{font-family:var(--mono)}

  /* NAV — canonical cross-site chrome */
  nav{position:sticky;top:0;z-index:50;background:rgba(252,252,250,0.9);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
  .nav-in{max-width:1140px;margin:0 auto;padding:14px 32px;display:flex;align-items:center;justify-content:space-between;gap:18px}
  .brand{display:flex;align-items:center;gap:10px;font-weight:600;font-size:15px;letter-spacing:-0.2px;text-decoration:none;color:var(--ink)}
  .brand .glyph{width:22px;height:22px;border:1.5px solid var(--ink);border-radius:5px;position:relative;flex-shrink:0}
  .brand .glyph::after{content:'';position:absolute;inset:4px;border-left:1.5px solid var(--accent);border-bottom:1.5px solid var(--accent);transform:rotate(-45deg) translate(1px,-1px)}
  .brand .svc{font-family:var(--mono);font-size:11px;font-weight:500;letter-spacing:1px;text-transform:uppercase;color:var(--muted);border-left:1px solid var(--line);padding-left:10px;margin-left:2px}
  .nav-links{display:flex;gap:22px;align-items:center}
  .nav-links a{font-size:13.5px;color:var(--muted);text-decoration:none;transition:color .15s;white-space:nowrap}
  .nav-links a:hover{color:var(--ink)}
  .nav-links a.active{color:var(--ink);font-weight:600}
  .nav-ghost{font-family:var(--mono);font-size:13px;border:1px solid var(--line);padding:7px 14px;border-radius:7px;color:var(--ink)!important}
  .nav-ghost:hover{border-color:var(--ink)}

  /* DOCS SHELL */
  .docs{display:grid;grid-template-columns:236px 1fr;gap:52px;padding:40px 0 64px}
  .side{position:sticky;top:78px;align-self:start;max-height:calc(100vh - 96px);overflow-y:auto}
  .side h5{font-family:var(--mono);font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted-2);margin:20px 0 10px}
  .side h5:first-child{margin-top:0}
  .side a{display:block;font-size:14px;color:var(--muted);text-decoration:none;padding:5px 0 5px 12px;border-left:2px solid var(--line);transition:all .12s}
  .side a:hover{color:var(--ink);border-left-color:var(--muted-2)}
  .side a.active{color:var(--accent);border-left-color:var(--accent);font-weight:600}

  /* ARTICLE */
  article{min-width:0;max-width:760px}
  .crumb{font-family:var(--mono);font-size:12px;letter-spacing:.5px;text-transform:uppercase;color:var(--accent);margin-bottom:12px}
  article h1{font-size:clamp(28px,4vw,40px);letter-spacing:-1px;line-height:1.1;font-weight:700;margin-bottom:14px}
  article .lede{font-size:18px;color:var(--muted);margin-bottom:30px;line-height:1.6}
  article h2{font-size:23px;letter-spacing:-0.4px;font-weight:700;margin:38px 0 12px;padding-top:8px}
  article h3{font-size:17px;font-weight:600;margin:24px 0 8px}
  article p{margin-bottom:14px}
  article ul,article ol{margin:0 0 16px 22px}
  article li{margin-bottom:7px}
  article a.ln{color:var(--accent);text-decoration:none}
  article a.ln:hover{text-decoration:underline}
  code{font-family:var(--mono);font-size:.88em;background:var(--paper-2);border:1px solid var(--line);border-radius:5px;padding:1px 6px}
  pre.code{background:var(--ink);color:#E8ECF4;border-radius:12px;padding:20px;overflow-x:auto;font-family:var(--mono);font-size:13px;line-height:1.7;border:1px solid var(--line-2);margin:6px 0 18px}
  pre.code code{background:none;border:none;padding:0;font-size:inherit;color:inherit}
  pre.code .c{color:#7E8AA0} pre.code .s{color:#9DE2B8} pre.code .k{color:#C58AF9}
  pre.code .fn{color:#7FB4FF} pre.code .ok{color:#54D08A;font-weight:600}
  table.t{border-collapse:collapse;width:100%;font-size:13.5px;border:1px solid var(--line);border-radius:10px;overflow:hidden;margin:6px 0 20px}
  table.t th,table.t td{padding:11px 14px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
  table.t thead th{font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);background:var(--paper-2)}
  table.t tbody th{font-weight:600;white-space:nowrap}
  table.t tbody td{color:var(--muted)}
  table.t tr:last-child th,table.t tr:last-child td{border-bottom:none}
  .callout{background:var(--paper-2);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;padding:14px 18px;font-size:14px;margin:6px 0 20px}
  .callout.warn{border-left-color:var(--verify)}
  .callout.deeper{border-left-color:var(--verify);background:var(--verify-soft)}
  .next{display:flex;justify-content:space-between;gap:16px;margin-top:48px;padding-top:24px;border-top:1px solid var(--line);flex-wrap:wrap}
  .next a{flex:1;min-width:200px;border:1px solid var(--line);border-radius:12px;padding:16px 18px;text-decoration:none;transition:border-color .15s}
  .next a:hover{border-color:var(--ink)}
  .next .dir{font-family:var(--mono);font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted-2);margin-bottom:5px}
  .next .ttl{font-size:15px;font-weight:600;color:var(--ink)}
  .next a.n{text-align:right}

  /* DOCS INDEX CARDS */
  .idx-group{margin-bottom:34px}
  .idx-group h2{font-size:15px;font-family:var(--mono);letter-spacing:1px;text-transform:uppercase;color:var(--muted-2);margin-bottom:14px;font-weight:500}
  .cards{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
  .dcard{border:1px solid var(--line);border-radius:12px;padding:20px 22px;background:#fff;text-decoration:none;transition:border-color .15s,transform .15s;display:block}
  .dcard:hover{border-color:var(--ink);transform:translateY(-2px)}
  .dcard .n{font-size:16px;font-weight:600;letter-spacing:-0.2px;margin-bottom:6px}
  .dcard .d{font-size:13.5px;color:var(--muted)}

  /* FOOTER — canonical */
  footer{padding:48px 0 56px;border-top:1px solid var(--line)}
  .foot-in{display:flex;justify-content:space-between;gap:24px;flex-wrap:wrap;align-items:flex-start}
  .foot-brand{max-width:38ch}
  .foot-brand p{font-size:13px;color:var(--muted);margin-top:12px}
  .foot-cols{display:flex;gap:48px;flex-wrap:wrap}
  .foot-col h5{font-family:var(--mono);font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted-2);margin-bottom:14px}
  .foot-col a{display:block;font-size:13.5px;color:var(--muted);text-decoration:none;margin-bottom:9px}
  .foot-col a:hover{color:var(--ink)}
  .foot-note{margin-top:40px;padding-top:24px;border-top:1px solid var(--line);font-size:12.5px;color:var(--muted-2);font-family:var(--mono)}

  @media(max-width:900px){
    .docs{grid-template-columns:1fr;gap:24px}
    .side{position:static;max-height:none;border-bottom:1px solid var(--line);padding-bottom:16px;display:flex;flex-wrap:wrap;gap:6px 16px}
    .side h5{width:100%;margin:8px 0 2px}
    .side a{border-left:none;padding:3px 0}
    .cards{grid-template-columns:1fr}
    .nav-in{gap:12px}
    .nav-links{gap:16px;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none}
    .nav-links::-webkit-scrollbar{display:none}
  }
"""

NAV = """<nav>
  <div class="nav-in">
    <a class="brand" href="/"><span class="glyph"></span> Agent Action Capsule</a>
    <div class="nav-links">
      <a href="/">Standard</a>
      <a href="{anchor}">Transparency Log</a>
      <a href="{verify}">Verifier</a>
      <a class="active" href="/docs/">Docs</a>
      <a class="nav-ghost" href="{org}">Source &#x2197;</a>
      <a href="{draft}">Draft (IETF) &#x2197;</a>
    </div>
  </div>
</nav>""".format(anchor=ANCHOR_URL, verify=VERIFY_URL, org=ORG_URL, draft=DRAFT_URL)

FOOTER = """<footer>
  <div class="wrap">
    <div class="foot-in">
      <div class="foot-brand">
        <a class="brand" href="/"><span class="glyph"></span> Agent Action Capsule</a>
        <p>An open profile on IETF SCITT for verifiable records of agent actions. Neutral substrate for the agent ecosystem, stewarded by Action State Group.</p>
      </div>
      <div class="foot-cols">
        <div class="foot-col">
          <h5>Standard</h5>
          <a href="/">Overview</a>
          <a href="/docs/">Docs</a>
          <a href="{draft}">Internet-Draft &#x2197;</a>
        </div>
        <div class="foot-col">
          <h5>Services</h5>
          <a href="{anchor}">Transparency Log</a>
          <a href="{verify}">Verifier</a>
        </div>
        <div class="foot-col">
          <h5>Source</h5>
          <a href="{org}">GitHub &#x2197;</a>
          <a href="https://github.com/ietf-wg-scitt/examples">Test vectors &#x2197;</a>
        </div>
      </div>
    </div>
    <div class="foot-note">Apache-2.0 &middot; neutral substrate &middot; agentactioncapsule.org</div>
  </div>
</footer>""".format(anchor=ANCHOR_URL, verify=VERIFY_URL, org=ORG_URL, draft=DRAFT_URL)

# Sidebar groups: (group label, [(slug, short-title)])
SIDEBAR = [
    ("Concepts", [
        ("what-is-a-capsule", "What is a Capsule?"),
        ("statement-vs-transparency-layer", "Statement vs transparency layer"),
        ("what-is-a-transparency-service", "What is a Transparency Service?"),
        ("verifiable-data-structures", "Verifiable Data Structures"),
        ("how-verification-works", "How verification works"),
    ]),
    ("Guides", [
        ("quickstart", "Quickstart"),
        ("verify-a-capsule", "Verify a capsule"),
    ]),
    ("Reference", [
        ("glossary", "Glossary"),
    ]),
]

# Linear order for prev/next.
ORDER = [s for _, items in SIDEBAR for s, _ in items]


def sidebar_html(active_slug: str) -> str:
    out = ['<nav class="side" aria-label="Docs">']
    out.append('<h5>Documentation</h5>')
    ov_cls = ' class="active"' if active_slug == "index" else ""
    out.append(f'<a href="/docs/"{ov_cls}>Overview</a>')
    for label, items in SIDEBAR:
        out.append(f"<h5>{label}</h5>")
        for slug, title in items:
            cls = ' class="active"' if slug == active_slug else ""
            out.append(f'<a href="/docs/{slug}.html"{cls}>{title}</a>')
    out.append("</nav>")
    return "\n".join(out)


def next_block(slug: str) -> str:
    if slug not in ORDER:
        return ""
    i = ORDER.index(slug)
    titles = {s: t for _, items in SIDEBAR for s, t in items}
    prev_a = nxt_a = ""
    if i > 0:
        ps = ORDER[i - 1]
        prev_a = (f'<a class="p" href="/docs/{ps}.html"><div class="dir">&#8592; Previous</div>'
                  f'<div class="ttl">{titles[ps]}</div></a>')
    else:
        prev_a = ('<a class="p" href="/docs/"><div class="dir">&#8592; Previous</div>'
                  '<div class="ttl">Overview</div></a>')
    if i < len(ORDER) - 1:
        ns = ORDER[i + 1]
        nxt_a = (f'<a class="n" href="/docs/{ns}.html"><div class="dir">Next &#8594;</div>'
                 f'<div class="ttl">{titles[ns]}</div></a>')
    return f'<div class="next">{prev_a}{nxt_a}</div>'


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} &mdash; Agent Action Capsule docs</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
{nav}
<main class="wrap">
  <div class="docs">
    {sidebar}
    <article>
      <div class="crumb">{crumb}</div>
      {body}
      {nxt}
    </article>
  </div>
</main>
{footer}
</body>
</html>
"""


def render(slug, title, desc, crumb, body, *, is_index=False):
    return PAGE.format(
        title=title, desc=desc, css=CSS, nav=NAV, footer=FOOTER,
        sidebar=sidebar_html("index" if is_index else slug),
        crumb=crumb, body=body,
        nxt="" if is_index else next_block(slug),
    )


# ---------------------------------------------------------------------------
# Page content
# ---------------------------------------------------------------------------
PAGES = {}

PAGES["what-is-a-capsule"] = dict(
    title="What is an Agent Action Capsule?",
    desc="An Agent Action Capsule is a signed, tamper-evident record of a consequential action an AI agent took, verifiable by any third party without trusting the operator.",
    crumb="Concepts",
    body=f"""
<h1>What is an Agent Action Capsule?</h1>
<p class="lede">An Agent Action Capsule is a signed, tamper-evident record of a consequential action an AI agent took &mdash; sealed at the moment it acted, so any third party can verify later what happened, without trusting the operator who ran the agent.</p>

<p>Agents increasingly take real actions: they place orders, move files, send messages, change records. Today, the only evidence that an action happened as described is the operator's own word. The Agent Action Capsule closes that gap by borrowing the shape that software supply-chain security already uses for build artifacts &mdash; a signed statement registered to a transparency log &mdash; and applying it to <em>agent actions</em>.</p>

<h2>The three properties</h2>
<table class="t">
  <thead><tr><th>Property</th><th>What it means</th></tr></thead>
  <tbody>
    <tr><th>Signed</th><td>The capsule is a COSE-signed statement committing to the action, its inputs and outputs (by digest), and the model/runtime that produced it. Change any byte and the signature fails.</td></tr>
    <tr><th>Transparent</th><td>The statement is registered to a transparency service, which returns a receipt proving the record was included in an append-only log that cannot quietly drop or rewrite history.</td></tr>
    <tr><th>Third-party verifiable</th><td>An auditor, third party, or regulator checks the signature and the inclusion proof from the bytes alone &mdash; no access to the operator's systems, no trust required.</td></tr>
  </tbody>
</table>

<h2>What a capsule commits to</h2>
<p>A capsule is a <code>COSE_Sign1</code> envelope over the media type <code>application/agent-action-capsule+json</code>. The payload commits to:</p>
<ul>
  <li>the <strong>action</strong> performed (an effect type and its identifying fields);</li>
  <li><strong>input and output digests</strong> &mdash; SHA-256 of what went in and what came out, so raw values stay local while the proof travels;</li>
  <li>the <strong>producing context</strong> &mdash; the model and runtime that generated the action.</li>
</ul>
<p>Because inputs and outputs are committed <em>by digest</em>, a capsule proves integrity without disclosing sensitive payloads.</p>

<h2>What gets sealed &mdash; the fields</h2>
<p>The seal is the <code>capsule_id</code>: the SHA-256 of the canonical capsule. Recompute it and it must match byte-for-byte &mdash; that hash <em>is</em> the seal. Around it, a capsule commits the parts an agent action needs to be accountable:</p>
<table class="t">
  <thead><tr><th>Field</th><th>What it commits</th></tr></thead>
  <tbody>
    <tr><th>capsule_id</th><td>SHA-256 of the canonical capsule &mdash; the seal / content address.</td></tr>
    <tr><th>action / operator / developer / timestamp</th><td>what was done, the accountable tenant, the agent identity@version, and when.</td></tr>
    <tr><th>disposition</th><td>the <strong>may/did</strong> verdict &mdash; <code>executed</code>, <code>confirmed</code>, <code>denied</code>, or <code>blocked</code>.</td></tr>
    <tr><th>effect</th><td>what was committed, plus the <strong>confirmed-effect binding</strong> so the claim and the outcome can't drift apart.</td></tr>
    <tr><th>model_attestation</th><td>which model decided, with the action's <strong>input and output committed as digests</strong> (raw values are never stored) and best-effort compute.</td></tr>
    <tr><th>assurance</th><td>how far to trust it: attestation / effect / ledger modes.</td></tr>
    <tr><th>chain</th><td>links to other capsules (<code>confirms</code> / <code>supersedes</code> / <code>escalates</code>) &mdash; present only when this capsule relates to another.</td></tr>
  </tbody>
</table>

<h2>Content-private by construction</h2>
<p>Each evidence layer is <strong>hashed, and only the digest is committed</strong> &mdash; the raw prompt, vendor, or amount is never inside the capsule. You can hand someone a capsule and they learn <em>what happened</em> and can verify the seal, without seeing your inputs or outputs. Reveal a raw value later only when you choose, and anyone can re-hash it against the committed digest.</p>

<h2>Chains: approved &rarr; executed &rarr; confirmed</h2>
<p>A confirmation is itself a capsule that points at its parent by digest. That turns a decision and its follow-through into one verifiable trail &mdash; the basis for human-in-the-loop confirmation and for selective disclosure (show a chain that proves authorization without exposing the underlying data).</p>

<h2>Levels of assurance</h2>
<p>Tamper-evidence is always present (the <code>capsule_id</code> hash). An <em>existence proof</em> comes from anchoring &mdash; the receipt held beside the capsule. A producer <em>signature</em> binding to a key is the SCITT Signed-Statement level, a step up from the default. You adopt as much as your use case needs.</p>

<h2>Where it sits</h2>
<p>The capsule is a <em>statement-layer</em> profile. It says nothing about which verifiable data structure a log uses &mdash; that separation is what lets the same capsule verify against different transparency services. See <a class="ln" href="/docs/statement-vs-transparency-layer.html">the statement layer vs the transparency layer</a>.</p>
<p>It is one <strong>SCITT profile</strong> among others &mdash; specialized for agent actions, built on the general SCITT/COSE substrate, and interoperable with any SCITT transparency service. Adopting it means joining the standard, not forking it.</p>

<div class="callout">{STATUS_NOTE}</div>
""",
)

PAGES["statement-vs-transparency-layer"] = dict(
    title="The statement layer vs the transparency layer",
    desc="The Agent Action Capsule separates the signed statement (what happened) from the transparency layer (where it is recorded). The statement is verifiable-data-structure agnostic.",
    crumb="Concepts",
    body="""
<h1>The statement layer vs the transparency layer</h1>
<p class="lede">Two concerns, deliberately kept apart: <strong>what happened</strong> (a signed statement) and <strong>where it is recorded</strong> (a transparency log). The statement never depends on which log technology you choose.</p>

<h2>Two layers</h2>
<table class="t">
  <thead><tr><th>Layer</th><th>Answers</th><th>Form</th></tr></thead>
  <tbody>
    <tr><th>Statement</th><td>What action happened, signed by whom?</td><td>A <code>COSE_Sign1</code> Signed Statement (the Agent Action Capsule profile).</td></tr>
    <tr><th>Transparency</th><td>Was this statement recorded in an append-only log, and can that be proven?</td><td>A transparency service that registers the statement and returns a receipt.</td></tr>
  </tbody>
</table>

<h2>Why the separation matters</h2>
<p>Keeping the statement independent of the log means a single capsule can be anchored to more than one transparency service, and verified the same way regardless of how each log structures its proofs. The action layer never changes when the log changes &mdash; this is what we mean by <a class="ln" href="/docs/verifiable-data-structures.html">verifiable-data-structure agnostic</a>.</p>

<h2>The stack</h2>
<p>Each layer is a separate, open-source library so the boundaries stay honest:</p>
<table class="t">
  <thead><tr><th>Component</th><th>Role</th></tr></thead>
  <tbody>
    <tr><th>agent-action-capsule</th><td>The profile &mdash; the Signed Statement format and the reference verifier.</td></tr>
    <tr><th>capsule-emit</th><td>The producer &mdash; seal an action in one call, or wrap an existing tool with one decorator.</td></tr>
    <tr><th>scitt-cose</th><td>The verifier &mdash; checks SCITT receipts across verifiable data structures.</td></tr>
    <tr><th>capsule-anchor</th><td>The log &mdash; a neutral transparency service implementation.</td></tr>
  </tbody>
</table>
<div class="callout">Read next: <a class="ln" href="/docs/what-is-a-transparency-service.html">what a transparency service is</a>, and how it differs from a verifier.</div>
""",
)

PAGES["what-is-a-transparency-service"] = dict(
    title="What is a Transparency Service?",
    desc="A SCITT Transparency Service registers signed statements, issues receipts, and anchors them to an append-only log. It is high-trust infrastructure — and it is not a verifier.",
    crumb="Concepts",
    body="""
<h1>What is a Transparency Service?</h1>
<p class="lede">A Transparency Service (TS) registers signed statements, issues a receipt proving inclusion, and anchors them to an append-only log &mdash; so a record can be shown to exist and to never have been quietly dropped or rewritten.</p>

<h2>What it does</h2>
<ol>
  <li><strong>Register.</strong> Accepts a <code>COSE_Sign1</code> signed statement and appends its digest as a leaf in the log.</li>
  <li><strong>Receipt.</strong> Returns a signed inclusion proof you can verify offline against the log's public key.</li>
  <li><strong>Anchor.</strong> Publishes a signed tree head and the proofs that keep the log append-only over time.</li>
</ol>

<h2>What it is &mdash; and is NOT</h2>
<p>A <em>verifier</em> checks evidence and holds nothing. A <em>transparency service</em> holds state and carries operational trust. Conflating the two is the most common mistake, so the boundary is worth stating plainly:</p>
<table class="t">
  <thead><tr><th></th><th>Verifier</th><th>Transparency Service</th></tr></thead>
  <tbody>
    <tr><th>Operation</th><td>verify only</td><td>register statements, issue receipts, anchor</td></tr>
    <tr><th>State</th><td>none (stateless)</td><td>a durable, append-only log</td></tr>
    <tr><th>Trust commitment</th><td>none &mdash; verify it yourself</td><td>uptime, integrity, non-equivocation</td></tr>
    <tr><th>Risk class</th><td>low (read-only utility)</td><td>high (operational trust infrastructure)</td></tr>
    <tr><th>Who must trust whom</th><td>nobody trusts the operator</td><td>the ecosystem trusts the log operator</td></tr>
  </tbody>
</table>
<p>A verifier that begins storing submissions, issuing receipts, or anchoring has silently become a transparency service with all of its obligations.</p>

<h2>The trust model</h2>
<p>What you verify yourself: each signature, each inclusion proof, and consistency between any two tree heads &mdash; all from the bytes, offline. What the log commits to operationally: durable append-only storage, non-equivocation (one consistent view for everyone), and a stable, published signing key.</p>
<div class="callout">A live, neutral implementation runs at <a class="ln" href="https://anchor.agentactioncapsule.org">anchor.agentactioncapsule.org</a>. To check a receipt without running anything, use the <a class="ln" href="https://verify.actionstate.ai">hosted verifier</a>.</div>
""",
)

PAGES["verifiable-data-structures"] = dict(
    title="Verifiable Data Structures: RFC 9162 vs CCF",
    desc="A verifiable data structure (VDS) is how a transparency log proves inclusion and consistency. SCITT receipts identify the VDS: vds=1 is RFC9162_SHA256, vds=2 is CCF (ccf.v1).",
    crumb="Concepts",
    body="""
<h1>Verifiable Data Structures: RFC 9162 vs CCF</h1>
<p class="lede">A verifiable data structure (VDS) is the mechanism a transparency log uses to prove that an entry is included and that the log has only ever grown. A SCITT receipt records which VDS it speaks &mdash; and the same signed statement can be carried by more than one.</p>

<h2>The VDS field</h2>
<p>SCITT receipts carry a <code>vds</code> identifier so a verifier knows how to interpret the proof. Two are implemented here:</p>
<table class="t">
  <thead><tr><th></th><th>vds=1 &mdash; RFC9162_SHA256</th><th>vds=2 &mdash; CCF (ccf.v1)</th></tr></thead>
  <tbody>
    <tr><th>Basis</th><td>RFC&nbsp;9162 (Certificate Transparency 2.0) Merkle trees, SHA-256</td><td>Microsoft CCF (Confidential Consortium Framework) ledger receipts</td></tr>
    <tr><th>Proof shape</th><td>Merkle inclusion path + signed tree head</td><td>CCF ledger inclusion proof signed by the service identity</td></tr>
    <tr><th>Verify with</th><td>the log's public key + the leaf digest</td><td>the CCF service certificate / identity</td></tr>
    <tr><th>Published status</th><td>RFC&nbsp;9162 is a published RFC</td><td>CCF is an open-source framework; the SCITT mapping is a draft</td></tr>
  </tbody>
</table>

<h2>Why two?</h2>
<p>Different operators run different ledger technologies. By implementing both <code>vds=1</code> and <code>vds=2</code>, the verifier proves the statement layer really is structure-independent: one Agent Action Capsule was registered to an RFC&nbsp;9162 log <em>and</em> a real CCF node, and both receipts verify under a single verifier.</p>

<h2>What stays constant</h2>
<p>The signed statement &mdash; the capsule itself &mdash; does not change between <code>vds=1</code> and <code>vds=2</code>. Only the receipt differs. That is the whole point of separating <a class="ln" href="/docs/statement-vs-transparency-layer.html">the statement layer from the transparency layer</a>.</p>
<div class="callout">Cross-implementation test vectors for <code>RFC9162_SHA256</code> are published in the SCITT working group's examples repository: <a class="ln" href="https://github.com/ietf-wg-scitt/examples">ietf-wg-scitt/examples</a>.</div>
""",
)

PAGES["how-verification-works"] = dict(
    title="How verification works: signature + inclusion proof",
    desc="Verifying a capsule is two independent checks: the COSE signature proves who sealed it, and the receipt's inclusion proof shows the log recorded it. Both check from the bytes, offline.",
    crumb="Concepts",
    body="""
<h1>How verification works</h1>
<p class="lede">Verifying a capsule is two independent checks. The signature proves <strong>who sealed it</strong>. The receipt proves <strong>the log included it</strong>. Neither check requires trusting the operator &mdash; both run from the bytes, offline.</p>

<h2>Check 1 &mdash; the signature</h2>
<p>The capsule is a <code>COSE_Sign1</code> structure. Given the issuer's public key, the verifier confirms the signature covers the protected header and payload. If any field changed after signing, the check fails. This establishes <em>who</em> made the statement and that it is intact.</p>

<h2>Check 2 &mdash; the inclusion proof</h2>
<p>The transparency service returns a receipt: a signed proof that the statement's leaf digest sits in the log's Merkle tree at a given size. Given the log's public key and the leaf digest, the verifier recomputes the path to the signed tree head. This establishes that the record was <em>recorded</em> and is discoverable &mdash; not held privately by the operator.</p>

<pre class="code"><code><span class="c"># verify a receipt's inclusion proof, offline</span>
<span class="k">from</span> scitt_cose <span class="k">import</span> verify_receipt

r = verify_receipt(receipt, leaf_entry_hex=leaf,
                   log_public_key_pem=log_key)
<span class="k">print</span>(r.ok)   <span class="c"># -> </span><span class="ok">True</span></code></pre>

<h2>Staying append-only over time</h2>
<p>Beyond a single inclusion proof, a verifier can request a <strong>consistency proof</strong> between two signed tree heads to confirm the log only ever appended &mdash; it never rewrote or removed earlier entries. Inclusion answers &ldquo;is my record in the log?&rdquo;; consistency answers &ldquo;has the log stayed honest between then and now?&rdquo;</p>

<h2>What you do not have to trust</h2>
<ul>
  <li>You do not trust the operator &mdash; every claim is checkable from the bytes.</li>
  <li>You do not need the raw inputs or outputs &mdash; verification uses digests.</li>
  <li>You do not need network access to the operator &mdash; you need the public key and the proof.</li>
</ul>
<div class="callout">Try it without installing anything at the <a class="ln" href="https://verify.actionstate.ai">hosted verifier</a>, or run the same library yourself &mdash; see <a class="ln" href="/docs/verify-a-capsule.html">Verify a capsule</a>.</div>
""",
)

PAGES["quickstart"] = dict(
    title="Quickstart: seal your first capsule",
    desc="Seal an agent action as a verifiable capsule with one decorator using capsule-emit, anchor it to a transparency log, and verify the result.",
    crumb="Guides",
    body="""
<h1>Quickstart: seal your first capsule</h1>
<p class="lede">Turn an agent action into a verifiable, anchored record with one decorator. This walks from install to a verified receipt in a few minutes.</p>

<h2>1. Install the producer</h2>
<pre class="code"><code>pip install capsule-emit</code></pre>

<h2>2. Wrap a tool</h2>
<p>Add one decorator over the function (or MCP tool) whose actions you want sealed. The signature is preserved, so your tool's interface does not change.</p>
<pre class="code"><code><span class="k">from</span> capsule_emit <span class="k">import</span> emitter

<span class="fn">@emitter.tool</span>(effect_type=<span class="s">"write_order"</span>)
<span class="k">def</span> <span class="fn">submit_order</span>(vendor, amount, po_number):
    <span class="c"># your real tool logic</span>
    <span class="k">return</span> place(vendor, amount, po_number)

<span class="c"># call it normally — each call seals input + output</span>
<span class="c"># digests and registers the statement to the log</span>
submit_order(<span class="s">"Frobozz"</span>, 4210.00, <span class="s">"PO-0047"</span>)</code></pre>

<h2>3. Where it anchors</h2>
<p>By default the producer registers statements to a transparency service and keeps the returned receipt alongside the sealed statement. You can point it at any compatible service, including the neutral public log at <a class="ln" href="https://anchor.agentactioncapsule.org">anchor.agentactioncapsule.org</a>.</p>

<h2>4. Verify what you sealed</h2>
<pre class="code"><code>pip install agent-action-capsule

<span class="c"># verify a ledger of sealed actions, offline</span>
agent-action-capsule verify --store ledger.jsonl

  <span class="s">capsule_id</span>  9f2a...c14  <span class="ok">ok</span>
  substrate.receipt_verified: <span class="ok">True</span></code></pre>
<div class="callout">Next: <a class="ln" href="/docs/verify-a-capsule.html">verify a capsule</a> in detail, including the hosted verifier and what each check proves.</div>
""",
)

PAGES["verify-a-capsule"] = dict(
    title="Verify a capsule",
    desc="Verify an Agent Action Capsule three ways: in the browser with the hosted verifier, on the command line, or as a library — all running the same open-source checks.",
    crumb="Guides",
    body="""
<h1>Verify a capsule</h1>
<p class="lede">Anyone holding a capsule or receipt can verify it &mdash; in the browser, on the command line, or as a library. Every path runs the same open-source verifier and checks the same two things: the signature and the inclusion proof.</p>

<h2>In the browser</h2>
<p>The fastest way to check a single receipt or signed statement is the hosted verifier. Paste a receipt or statement (and a key, if you want the signature checked) and read the verdict and reasons. It is stateless &mdash; nothing you submit is stored.</p>
<div class="callout">Open <a class="ln" href="https://verify.actionstate.ai">verify.actionstate.ai</a>. The page runs the identical library you can install locally; for maximal privacy, verify locally instead.</div>

<h2>On the command line</h2>
<pre class="code"><code>pip install agent-action-capsule
agent-action-capsule verify --store ledger.jsonl</code></pre>

<h2>As a library</h2>
<pre class="code"><code><span class="k">from</span> scitt_cose <span class="k">import</span> verify_receipt

r = verify_receipt(receipt, leaf_entry_hex=leaf,
                   log_public_key_pem=log_key)
<span class="k">print</span>(r.ok)   <span class="c"># -> </span><span class="ok">True</span></code></pre>

<h2>What a pass means</h2>
<ul>
  <li>The signature is intact and made by the stated issuer key.</li>
  <li>The leaf digest is provably included in the log at the proven tree size.</li>
  <li>Optionally, the log has stayed append-only between two tree heads (consistency).</li>
</ul>
<p>For the mechanics of each check, see <a class="ln" href="/docs/how-verification-works.html">how verification works</a>.</p>
""",
)

PAGES["glossary"] = dict(
    title="Glossary",
    desc="Definitions of the core terms: SCITT, COSE_Sign1, Signed Statement, Receipt, VDS, STH, inclusion proof, consistency proof.",
    crumb="Reference",
    body="""
<h1>Glossary</h1>
<p class="lede">The core vocabulary of the Agent Action Capsule and the transparency layer it builds on.</p>
<table class="t">
  <thead><tr><th>Term</th><th>Definition</th></tr></thead>
  <tbody>
    <tr><th>SCITT</th><td>Supply Chain Integrity, Transparency, and Trust &mdash; the IETF working group and architecture for registering signed statements in transparency services. Its specifications are drafts, not yet RFCs.</td></tr>
    <tr><th>SCITT profile</th><td>A specialization of the general SCITT signed-statement format for a domain. The Agent Action Capsule is the profile for <em>agent actions</em> &mdash; it builds on SCITT/COSE and interoperates with any SCITT transparency service, rather than being a separate standard.</td></tr>
    <tr><th>COSE</th><td>CBOR Object Signing and Encryption &mdash; the signature format used for statements and receipts.</td></tr>
    <tr><th>COSE_Sign1</th><td>A single-signer COSE structure: one signature over a protected header and payload. The envelope an Agent Action Capsule uses.</td></tr>
    <tr><th>Signed Statement</th><td>A COSE_Sign1 claim about something &mdash; here, an agent action. The capsule is a profiled Signed Statement.</td></tr>
    <tr><th>Agent Action Capsule</th><td>The profile in this project: a Signed Statement over <code>application/agent-action-capsule+json</code> committing to an action and its input/output digests.</td></tr>
    <tr><th>Transparency Service</th><td>A service that registers Signed Statements into an append-only log, issues receipts, and publishes tree heads and proofs.</td></tr>
    <tr><th>Transparency log</th><td>The public, append-only log a Transparency Service maintains. It is publicly readable &mdash; anyone can fetch its entries and verify any one of them; nothing is taken on trust.</td></tr>
    <tr><th>Ledger</th><td>Your <em>local</em> append-only trail of capsules (e.g. <code>ledger.jsonl</code>) &mdash; distinct from the public transparency log. The ledger is yours; the transparency log is the shared, anchored record.</td></tr>
    <tr><th>Receipt</th><td>A signed proof, returned by a transparency service, that a statement was included in its log. Verifiable offline against the log key.</td></tr>
    <tr><th>VDS</th><td>Verifiable Data Structure &mdash; how a log proves inclusion and consistency. <code>vds=1</code> is RFC9162_SHA256; <code>vds=2</code> is CCF (ccf.v1).</td></tr>
    <tr><th>Inclusion proof</th><td>Evidence that a specific leaf is part of the log at a given size &mdash; answers &ldquo;is my record in the log?&rdquo;</td></tr>
    <tr><th>Consistency proof</th><td>Evidence that one tree head is an append-only extension of an earlier one &mdash; answers &ldquo;did the log stay honest?&rdquo;</td></tr>
    <tr><th>STH</th><td>Signed Tree Head &mdash; the log's current Merkle root and size, signed, so verifiers and witnesses can pin its state.</td></tr>
    <tr><th>Merkle tree</th><td>A hash tree whose root commits to every leaf; the structure behind RFC&nbsp;9162 inclusion and consistency proofs.</td></tr>
    <tr><th>RFC 9162</th><td>Certificate Transparency 2.0 &mdash; the published RFC whose SHA-256 Merkle proofs back <code>vds=1</code>.</td></tr>
    <tr><th>CCF</th><td>Confidential Consortium Framework &mdash; Microsoft's open-source ledger framework whose receipts back <code>vds=2</code>.</td></tr>
  </tbody>
</table>
""",
)

# Docs index (overview)
INDEX_BODY = f"""
<h1>Documentation</h1>
<p class="lede">Concepts and short guides for the Agent Action Capsule &mdash; the open profile for verifiable records of what an AI agent did, and the transparency layer it builds on.</p>

<div class="idx-group">
  <h2>Concepts</h2>
  <div class="cards">
    <a class="dcard" href="/docs/what-is-a-capsule.html"><div class="n">What is an Agent Action Capsule?</div><div class="d">A signed, tamper-evident record of an agent action &mdash; and the three properties that make it verifiable.</div></a>
    <a class="dcard" href="/docs/statement-vs-transparency-layer.html"><div class="n">Statement vs transparency layer</div><div class="d">What happened vs where it is recorded &mdash; and why the statement is structure-independent.</div></a>
    <a class="dcard" href="/docs/what-is-a-transparency-service.html"><div class="n">What is a Transparency Service?</div><div class="d">Register, receipt, anchor &mdash; and the boundary between a transparency service and a verifier.</div></a>
    <a class="dcard" href="/docs/verifiable-data-structures.html"><div class="n">Verifiable Data Structures</div><div class="d">RFC9162_SHA256 (vds=1) vs CCF ccf.v1 (vds=2), and what stays constant across them.</div></a>
    <a class="dcard" href="/docs/how-verification-works.html"><div class="n">How verification works</div><div class="d">Two independent checks: signature, then inclusion proof &mdash; both from the bytes, offline.</div></a>
  </div>
</div>

<div class="idx-group">
  <h2>Guides</h2>
  <div class="cards">
    <a class="dcard" href="/docs/quickstart.html"><div class="n">Quickstart</div><div class="d">Seal your first capsule with one decorator, anchor it, and verify the result.</div></a>
    <a class="dcard" href="/docs/verify-a-capsule.html"><div class="n">Verify a capsule</div><div class="d">Verify in the browser, on the command line, or as a library &mdash; same checks everywhere.</div></a>
  </div>
</div>

<div class="idx-group">
  <h2>Reference</h2>
  <div class="cards">
    <a class="dcard" href="/docs/glossary.html"><div class="n">Glossary</div><div class="d">SCITT, COSE_Sign1, Signed Statement, Receipt, VDS, STH, inclusion &amp; consistency proofs.</div></a>
  </div>
</div>

<div class="callout deeper"><strong>Building on it?</strong> Implementation, tutorials, and adapter guides live in the canonical <code>capsule-emit</code> docs: <a class="ln" href="{CE_DOCS}">capsule-emit/docs &#x2197;</a>. These pages cover the standard-level concepts; the repo docs cover hands-on usage.</div>

<div class="callout">{STATUS_NOTE}</div>
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # index
    (OUT / "index.html").write_text(
        render("index", "Documentation", "Concepts and guides for the Agent Action Capsule, the open profile for verifiable records of agent actions.",
               "Docs", INDEX_BODY, is_index=True), encoding="utf-8")
    n = 1
    for slug in ORDER:
        p = PAGES[slug]
        body = p["body"] + go_deeper_html(slug)
        (OUT / f"{slug}.html").write_text(
            render(slug, p["title"], p["desc"], p["crumb"], body), encoding="utf-8")
        n += 1
    print(f"wrote {n} files to {OUT}")


if __name__ == "__main__":
    main()
