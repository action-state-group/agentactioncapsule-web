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
    "Transparency 2.0) is a published RFC. <strong>Tracking the standard:</strong> "
    "this profile is built to track SCITT and COSE as they finalize — as those "
    "drafts advance and are published as RFCs, the profile and its reference "
    "implementations will be updated to conform to the final versions, and any "
    "breaking changes will be versioned and documented."
)

# ---------------------------------------------------------------------------
# Shared chrome
# ---------------------------------------------------------------------------
CSS = """
  :root{
    --ink:#0B0E14; --ink-2:#161B25; --paper:#FCFCFA; --paper-2:#F4F4F0;
    --line:#E3E3DC; --line-2:#2A313F;
    --muted:#5C6573; --muted-2:#6B7280;
    --accent:#3A5BD9; --accent-soft:#EAEEFC;
    --verify:#127A52; --verify-soft:#E6F2EC;
    --mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
  }
  *{margin:0;padding:0;box-sizing:border-box}
  html{scroll-behavior:smooth}
  body{font-family:'Inter',system-ui,sans-serif;background:var(--paper);color:var(--ink);line-height:1.65;-webkit-font-smoothing:antialiased}
  a{color:inherit}
  .sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0}
  .skip{position:absolute;left:8px;top:-48px;z-index:100;background:var(--ink);color:var(--paper);padding:9px 16px;border-radius:8px;text-decoration:none;transition:top .15s}
  .skip:focus{top:8px}
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
        <p>An open, individual profile built on the SCITT protocol (an IETF Internet-Draft; not WG-adopted), for verifiable records of agent actions. Stewarded today by Action State Group, built to be donated to a neutral home.</p>
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
    <div class="foot-note">Open source &middot; built to be donated &middot; agentactioncapsule.org</div>
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
        ("whats-consequential", "What's consequential"),
        ("how-it-composes", "How it composes"),
        ("anchor-anywhere", "Anchor anywhere"),
    ]),
    ("Guides", [
        ("quickstart", "Quickstart"),
        ("verify-a-capsule", "Verify a capsule"),
    ]),
    ("Live", [
        ("explore", "Explore a capsule"),
        ("log", "The public log, live"),
    ]),
    ("Reference", [
        ("glossary", "Glossary"),
    ]),
    ("Project", [
        ("governance", "Governance"),
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
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Agent Action Capsule">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://agentactioncapsule.org/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="https://agentactioncapsule.org/og-image.png">
<meta name="theme-color" content="#0B0E14">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{nav}
<main class="wrap" id="main">
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
    url = "https://agentactioncapsule.org/docs/" if is_index else f"https://agentactioncapsule.org/docs/{slug}.html"
    return PAGE.format(
        title=title, desc=desc, css=CSS, nav=NAV, footer=FOOTER, url=url,
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
    <tr><th>Signed</th><td>The capsule is a statement committing to the action, its inputs and outputs (by digest), and the model/runtime that produced it &mdash; content-addressed by default, and COSE-signed at the Signed-Statement tier. Change any byte and verification fails.</td></tr>
    <tr><th>Transparent</th><td>The statement is registered to a transparency service, which returns a receipt proving the record was included in an append-only log that cannot quietly drop or rewrite history.</td></tr>
    <tr><th>Third-party verifiable</th><td>An auditor, third party, or regulator checks the signature and the inclusion proof from the bytes alone &mdash; no access to the operator's systems. You trust the log's key, not the operator.</td></tr>
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
    <tr><th>model_attestation</th><td>which model decided, with the <strong>full input</strong> it saw (system prompt, context, tool definitions, and the action's arguments) and the <strong>output</strong> each <strong>committed as a digest</strong> (fixed-size; raw values, however large or sensitive, are never stored) plus best-effort compute.</td></tr>
    <tr><th>assurance</th><td>how far to trust it: attestation / effect / ledger modes.</td></tr>
    <tr><th>chain</th><td>links to other capsules (<code>confirms</code> / <code>supersedes</code> / <code>escalates</code>) &mdash; present only when this capsule relates to another.</td></tr>
  </tbody>
</table>

<h2>Content-private by construction</h2>
<p>Each evidence layer is <strong>hashed, and only the digest is committed</strong> &mdash; the raw prompt, vendor, or amount is never inside the capsule. You can hand someone a capsule and they learn <em>what happened</em> and can verify the seal, without seeing your inputs or outputs. Reveal a raw value later only when you choose, and anyone can re-hash it against the committed digest.</p>

<h2>Chains: approved &rarr; executed &rarr; confirmed</h2>
<p>A confirmation is itself a capsule that points at its parent by digest. That turns a decision and its follow-through into one verifiable trail &mdash; the basis for human-in-the-loop confirmation and for selective disclosure (show a chain that proves authorization without exposing the underlying data).</p>
<p>A <code>confirmed</code> capsule is sealed only when the agent observes a reply or receipt back from the system or party it acted on &mdash; that returning confirmation is what closes the loop. It's why <code>confirmed</code> carries more weight than <code>dispatched</code>, which records only that the action was sent. When no confirmation comes back to observe, the capsule honestly stays <code>dispatched</code> or <code>executed</code>.</p>

<h2>Levels of assurance</h2>
<p>Tamper-evidence is always present (the <code>capsule_id</code> hash). An <em>existence proof</em> comes from anchoring &mdash; the receipt held beside the capsule. A producer <em>signature</em> binding to a key is the SCITT Signed-Statement level, a step up from the default. You adopt as much as your use case needs.</p>

<h2>What a capsule does not prove</h2>
<p>Honest claims matter. Know the limits before relying on this for audit or compliance:</p>
<ul>
  <li><strong>Attested, not verified.</strong> A capsule proves what the agent <em>attested</em> it did &mdash; not that the real-world effect occurred. A <code>dispatched</code> capsule does not mean the write landed; a <code>confirmed</code> one does.</li>
  <li><strong>No anti-omission property.</strong> A capsule proves <em>this</em> action was recorded. It does not prevent an operator from simply not emitting a capsule for an action they'd rather not surface.</li>
  <li><strong>Signer = key-holder.</strong> The signature proves who held the signing key at the moment of sealing &mdash; not that the named agent actually ran the action. Key-management discipline is outside the capsule.</li>
  <li><strong>Default may be signature-less.</strong> The base assurance level is a content hash (tamper-evident, content-private). A producer signature binding to a key requires the SCITT Signed-Statement level explicitly.</li>
  <li><strong>Single-operator log &rArr; non-equivocation is operational.</strong> The public Transparency Service prevents the log from quietly rewriting history &mdash; but if one operator controls both the agent and the log, equivocation is an operational question, not a cryptographic one. A witness or a second independently-operated log removes this.</li>
</ul>
<p>These limits are features of being honest, not gaps to hide. Stating them is what makes the record trustworthy to an outside auditor.</p>

<h2>Where it sits</h2>
<p>The capsule is a <em>statement-layer</em> profile. It says nothing about which verifiable data structure a log uses &mdash; that separation is what lets the same capsule verify against different transparency services. See <a class="ln" href="/docs/statement-vs-transparency-layer.html">the statement layer vs the transparency layer</a>.</p>
<p>It is one <strong>SCITT profile</strong> among others &mdash; specialized for agent actions, built on the general SCITT/COSE substrate, and interoperable with any SCITT transparency service. Adopting it means building on a shared profile, not forking your own.</p>

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
<p>Different operators run different ledger technologies. The same Agent Action Capsule was registered to both an RFC&nbsp;9162 log (<code>vds=1</code>) <em>and</em> a real CCF node (<code>vds=2</code>), and both receipts check out &mdash; proving the statement layer really is structure-independent. (The reference verifier <a class="ln" href="https://github.com/action-state-group/scitt-cose">scitt-cose</a> implements <code>vds=1</code>; the CCF receipt was cross-checked against a CCF node.)</p>

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
    desc="Seal an agent action as a verifiable capsule with one emit() call, anchor it to a transparency log, and verify the result. Copy-paste-runnable.",
    crumb="Guides",
    body="""
<h1>Quickstart: seal your first capsule</h1>
<p class="lede">From install to a verified, anchored record in a few minutes &mdash; using <code>emit()</code>, the canonical one-call API.</p>

<h2>1. Install</h2>
<pre class="code"><code>pip install "capsule-emit==0.1.1" agent-action-capsule</code></pre>

<h2>2. Seal an action</h2>
<p>Call <code>emit()</code> once at each consequential action. <code>operator</code>, <code>developer</code>, <code>action</code>, <code>agent_input</code>, <code>agent_output</code>, <code>verdict</code>, and <code>effect</code> are required; <code>model</code> is optional (adapters fill in what they can &mdash; the MCP adapter, for example, sees the tool boundary, not the LLM, so pass <code>model</code> explicitly there if you want it sealed).</p>
<pre class="code"><code><span class="k">from</span> capsule_emit <span class="k">import</span> emit

result = place(<span class="s">"Frobozz Supply"</span>, 4210.00, <span class="s">"PO-0047"</span>)  <span class="c"># your tool logic</span>

cap = emit(
    action=<span class="s">"submit_order"</span>,
    operator=<span class="s">"acme-co"</span>,                <span class="c"># accountable tenant (required)</span>
    developer=<span class="s">"po-agent@v1"</span>,           <span class="c"># agent identity + version (required)</span>
    agent_input={<span class="s">"vendor"</span>: <span class="s">"Frobozz Supply"</span>, <span class="s">"total"</span>: 4210.00},
    agent_output=result,
    model={<span class="s">"provider"</span>: <span class="s">"anthropic"</span>, <span class="s">"model_id"</span>: <span class="s">"claude-sonnet-4-6"</span>},
    verdict=<span class="s">"executed"</span>,               <span class="c"># executed | confirmed | denied | blocked</span>
    effect={<span class="s">"type"</span>: <span class="s">"submit_order"</span>, <span class="s">"status"</span>: <span class="s">"dispatched"</span>},
)
print(cap.capsule_id, cap.anchored)   <span class="c"># sealed; digest submitted to the log</span></code></pre>
<div class="callout"><strong>Adapter shortcut:</strong> if you use MCP, LangChain, CrewAI, or Goose, a thin adapter emits on every tool call &mdash; the fields above are what every adapter fills in automatically. See the <a class="ln" href="https://github.com/action-state-group/capsule-emit/tree/main/docs/adapters">capsule-emit adapter docs</a>.</div>

<h2>3. Where it anchors</h2>
<p>By default, the capsule's digest is submitted asynchronously to the neutral public log at <a class="ln" href="https://anchor.agentactioncapsule.org">anchor.agentactioncapsule.org</a> &mdash; no signup, no key. Set <code>AAC_ANCHOR_URL</code> or pass <code>anchor_url=&hellip;</code> to point at your own SCITT service, or <code>anchor=False</code> to seal locally.</p>

<h2>4. Verify</h2>
<p>Each <code>emit()</code> also appends the sealed capsule to a local <code>ledger.jsonl</code> by default &mdash; that&rsquo;s the file you verify, offline:</p>
<pre class="code"><code><span class="c"># verify a ledger of sealed capsules, offline &mdash; no keys or network needed</span>
agent-action-capsule verify --store ledger.jsonl

  <span class="s">capsule_id</span>  9f2a...c14  <span class="ok">ok</span>
  substrate.anchored: <span class="ok">True</span>          <span class="c"># digest on the public log</span>
  substrate.receipt_verified: <span class="ok">True</span>  <span class="c"># receipt present and validated</span></code></pre>
<div class="callout warn"><strong>Today vs roadmap:</strong> <code>emit()</code> submits the capsule&rsquo;s digest to the public log (<code>cap.anchored=True</code>). The log&rsquo;s inclusion <em>receipt</em> is verifiable against the log today; surfacing it back onto the <code>emit()</code> return value is on the near-term roadmap.</div>
<h2>Adapters: seal from your framework</h2>
<p>You don&rsquo;t have to call <code>emit()</code> by hand. Thin adapters seal one capsule per tool call across the framework you already use &mdash; MCP / any callable (a decorator), LangChain / LangGraph (a callback), CrewAI (a tool wrap), and <strong>Goose</strong> (companion MCP server or <code>@emitter.tool()</code> decorator, verified against Goose v1.39.0). A gateway integration (<strong>agentgateway</strong>) seals at the chokepoint every consequential action flows through &mdash; one policy point instead of N integrations (via the gateway's <code>mcpGuardrails</code> ExtMcp hook). Any custom loop works via one call at the tool boundary. Per-framework guides: <a class="ln" href="https://github.com/action-state-group/capsule-emit/tree/main/docs/adapters">docs/adapters/</a> &mdash; including the <a class="ln" href="https://github.com/action-state-group/capsule-emit/blob/main/docs/adapters/goose.md">Goose extension</a> and the <a class="ln" href="https://github.com/action-state-group/capsule-emit/blob/main/docs/adapters/agentgateway.md">agentgateway adapter</a>.</p>
<div class="callout">Next: <a class="ln" href="/docs/verify-a-capsule.html">verify a capsule</a> in detail &mdash; the hosted verifier, command line, and what each check proves.</div>
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

PAGES["whats-consequential"] = dict(
    title="What's consequential — what to seal",
    desc="A capsule is for consequential actions, not every log line. The two-signal rule: seal what changes the world, plus reads of sensitive data; everything else is observability. Built on the field's accepted vocabulary, not a private invention.",
    crumb="Concepts",
    body="""
<h1>What's consequential — what to seal</h1>
<p class="lede">A capsule is for <em>consequential</em> actions, not every log line. The rule, in one sentence: <strong>seal what changes the world, plus reads of sensitive data; everything else is observability.</strong></p>

<h2>Two signals</h2>
<table class="t">
  <thead><tr><th>Signal</th><th>Seal it when…</th></tr></thead>
  <tbody>
    <tr><th>1 · Command vs. query</th><td>the action <strong>changes state or has a side effect</strong> — places an order, moves money, sends a message, writes a record. Pure reads (list / get / search) are queries — not sealed by default.</td></tr>
    <tr><th>2 · Privileged read</th><td>the action <strong>reads sensitive data</strong> (PII/PHI/cardholder data) even though it's a "read." This signal is evaluated <em>engine-side</em>, where data is classified — not at the gateway.</td></tr>
  </tbody>
</table>

<h2>Fail-safe by default</h2>
<p>When a tool's nature is unknown, it is <strong>sealed</strong> — the safe default is to record, not to skip. An adapter only skips a call when it is explicitly marked a read (e.g. <code>action_type="fyi"</code>, or <code>seal_reads=False</code> for tools so annotated). You opt out of sealing deliberately; you never silently lose a consequential action.</p>

<h2>Grey areas</h2>
<p>Some reads matter (exporting a customer list); some "writes" are trivial (a cache warm). Signal 2 is exactly for the first case. For the rest, when in doubt, seal — a few extra capsules cost little; a missing one is the gap that matters.</p>

<h2>Why this isn't a private invention</h2>
<p>The command-vs-query distinction is decades-old accepted vocabulary. We stand on it deliberately:</p>
<table class="t">
  <thead><tr><th>Prior art</th><th>What we take from it</th></tr></thead>
  <tbody>
    <tr><th><a class="ln" href="https://en.wikipedia.org/wiki/Command%E2%80%93query_separation">Command–Query Separation</a> — Bertrand Meyer (1988)</th><td>the foundational command-vs-query split: commands change state, queries don't.</td></tr>
    <tr><th><a class="ln" href="https://www.rfc-editor.org/rfc/rfc9110.html#name-safe-methods">RFC 9110 — HTTP Semantics</a> (safe methods)</th><td>the web's codification of "safe" (read) vs. unsafe (state-changing) methods.</td></tr>
    <tr><th><a class="ln" href="https://modelcontextprotocol.io/">Model Context Protocol</a> tool annotations (Anthropic / AAIF)</th><td>tool-level read-only / destructive hints — the per-tool signal an adapter reads.</td></tr>
    <tr><th><a class="ln" href="https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.312">HIPAA §164.312(b)</a> + <a class="ln" href="https://www.pcisecuritystandards.org/">PCI DSS</a></th><td>why a privileged <em>read</em> of regulated data is itself an auditable event (Signal 2).</td></tr>
  </tbody>
</table>
<div class="callout">The canonical developer guide (the two-signal rule, the <code>seal_reads</code> knob, gateway vs. decorator patterns) lives in the producer's docs: <a class="ln" href="https://github.com/action-state-group/capsule-emit/tree/main/docs">capsule-emit/docs</a>.</div>
""",
)

PAGES["how-it-composes"] = dict(
    title="How it composes with your stack",
    desc="The Agent Action Capsule doesn't replace your identity, authorization, or anchoring layers — it composes with them by referencing their evidence by digest, and adds the one thing they don't: a record any third party can verify without trusting any single party.",
    crumb="Concepts",
    body="""
<h1>How it composes with your stack</h1>
<p class="lede">The capsule is one layer in a stack, not a replacement for the others. It sits alongside the layers you already use — identity, authorization, anchoring — and adds the piece none of them provide on their own: a record any third party can verify without trusting any single party.</p>

<h2>Composes, doesn't replace</h2>
<p>Most agent-trust layers answer a different question than the capsule does. Identity says <em>who</em> is acting; authorization says <em>whether</em> an action is allowed; an anchoring log says the record was <em>included</em>. The capsule answers <strong>what the agent did</strong>, in a record anyone can check — and it leans on those other layers for the rest rather than reabsorbing them. There's no need to fork your stack to adopt it.</p>

<h2>How composition works: reference by digest</h2>
<p>A capsule binds external evidence into its verifiable trail through <code>chain.relation</code>: it commits the <strong>digest</strong> of another artifact — an authorization grant, a policy decision, an upstream receipt — without copying or exposing it. The verifier checks the binding; the referenced data stays where it lives. (The same mechanism links a confirmation back to the action it confirms — see <a class="ln" href="/docs/what-is-a-capsule.html">what is a capsule</a>.)</p>
<pre class="code"><code>{
  "action": "submit_order",
  "operator": "acme-co",
  "chain": {
    "relation": "authorized-by",      // this action was permitted by …
    "ref": "sha-256:9f2a…c14"         // digest of the grant / credential
  }
}</code></pre>
<p>Illustrative: the capsule carries only the <em>digest</em> of the authorization grant, policy decision, or identity credential — never its contents. A verifier recomputes that digest from the artifact you (or a partner layer) present, and confirms the binding. The precise relation vocabulary is defined in the spec registry; to register a relation for your layer, <a class="ln" href="https://github.com/action-state-group/agent-action-capsule/issues">open an issue on the spec</a>.</p>
<table class="t">
  <thead><tr><th>Layer</th><th>It answers</th><th>How the capsule composes</th></tr></thead>
  <tbody>
    <tr><th>Identity / delegation</th><td>who the agent is acting for</td><td>reference the identity or delegation credential by digest</td></tr>
    <tr><th>Authorization / policy</th><td>whether the action was permitted</td><td>reference the grant or policy decision by digest</td></tr>
    <tr><th>Anchoring / transparency log</th><td>that the record was publicly included</td><td>the SCITT receipt — the capsule is <a class="ln" href="/docs/verifiable-data-structures.html">log-agnostic</a></td></tr>
    <tr><th>Input integrity / provenance</th><td>whether upstream inputs are authentic</td><td>reference the input-integrity evidence by digest</td></tr>
  </tbody>
</table>

<h2>What only the capsule adds</h2>
<p>A record of what the agent did that any third party can verify <strong>without trusting the operator, the model vendor, or the log</strong>. That neutrality is the point: it's the piece a single party's own system can't provide for itself, because a party vouching for its own actions is exactly what a verifier can't take on faith.</p>
<div class="callout">A capsule records the bytes it is given. Authenticating <em>upstream</em> inputs — that a tool response or grounding source is genuine — is a separate, composable layer; bind its evidence by digest and the verifier checks that too. Composition, not dependency.</div>
""",
)

PAGES["anchor-anywhere"] = dict(
    title="Anchor anywhere — what leaves your walls",
    desc="When you anchor a capsule, only a digest and a timestamp leave — never prompts, payloads, or PII. Anchor to the public log, run your own anchor in the region you choose, or self-host inside your VPC where the hash never leaves.",
    crumb="Concepts",
    body="""
<h1>Anchor anywhere — what leaves your walls</h1>
<p class="lede">Anchoring proves a capsule was included in a public, append-only log. The only thing that travels to the log is a <strong>digest (a hash) and a timestamp</strong> — never your prompts, payloads, reasoning, or PII.</p>

<h2>What leaves your walls</h2>
<p>A capsule is <a class="ln" href="/docs/what-is-a-capsule.html">content-private by construction</a>: it carries digests of inputs and outputs, not the raw values. When it's anchored, the log receives the statement's commitment — a hash — plus a timestamp. The raw content stays where you keep it, under your control. The public log stores <em>a commitment you can check</em>, not your data.</p>

<h2>Anchor anywhere — three options</h2>
<table class="t">
  <thead><tr><th>Where you anchor</th><th>What it gives you</th><th>What leaves your environment</th></tr></thead>
  <tbody>
    <tr><th>The public log</th><td>zero-setup existence proofs on a shared, open log (<code>anchor.agentactioncapsule.org</code>)</td><td>a digest + a timestamp</td></tr>
    <tr><th>Your own anchor, in the region you choose</th><td>residency / jurisdiction control (e.g. EU, Singapore) by running the open anchor where you need it</td><td>a digest + a timestamp, kept in your jurisdiction</td></tr>
    <tr><th>Your own anchor, inside your VPC</th><td>full control — self-host the container with your own storage</td><td>nothing — the hash never leaves your environment</td></tr>
  </tbody>
</table>
<p>The capsule is <strong>anchor-agnostic</strong> (it makes no claim about the log's <a class="ln" href="/docs/verifiable-data-structures.html">verifiable-data-structure</a>): the same statement verifies whichever log you choose, so you can move or mix anchors without changing the record.</p>

<h2>What a digest hides — and what it doesn't</h2>
<p>A digest hides a value only when that value is hard to guess. A high-entropy input (a full prompt, a document, a key) is safe. But a <em>low-entropy</em> value — a short dollar amount, a yes/no disposition, an ID from a known list — can be recovered by hashing candidate values until one matches. For those fields, <strong>salt before hashing</strong> (commit a per-tenant salt alongside the value) so the digest can't be brute-forced. And note the capsule commits some metadata in the clear — the action type and disposition — so &ldquo;content-private&rdquo; means your <em>payloads</em> stay private, not that the capsule reveals nothing about what kind of action occurred.</p>

<div class="callout">The privacy promise, in one line: <strong>we verify; we store nothing of yours but a commitment you can check</strong> — and, for guessable values, salt before you commit them.</div>
""",
)

PAGES["governance"] = dict(
    title="Governance — how the project is run, and where it's headed",
    desc="The Agent Action Capsule is open and built to be donated. Stewarded today by Action State Group with the explicit intent to transfer the profile, trademark, and reference services to a neutral foundation. Governance modeled on Linux Foundation practice; co-maintainers welcome.",
    crumb="Project",
    body="""
<h1>Governance</h1>
<p class="lede">This project exists to produce a <strong>neutral, openly governed</strong> record layer for agent actions — and to give it away. This page states how it's run today, the principles it holds to, and the concrete path to a neutral home.</p>

<h2>Why governed this way</h2>
<p>Verifiable records of what AI agents do are infrastructure the whole ecosystem depends on. We think AI safety and open standards matter far too much for that layer to be controlled by any single company — so the design goal from day one is to donate it. The maintainers have stewarded openly and neutrally governed software before (the Presto Foundation, under the Linux Foundation), and this project is modeled on that practice.</p>

<h2>Principles</h2>
<table class="t">
  <tbody>
    <tr><th>Open</th><td>Apache-2.0 tooling; the specification under the IETF Trust's terms (BCP 78/79, code components under the Revised BSD License). Developed in public.</td></tr>
    <tr><th>Vendor-neutral</th><td>No required product; the specification favors no vendor. Any party can implement, run, and anchor — including in their own environment.</td></tr>
    <tr><th>Verifiable</th><td>Decisions, like capsules, happen in the open: public issues, public PRs, public discussion.</td></tr>
    <tr><th>Donate by design</th><td>The profile, the trademark, and the reference services are intended to transfer to a neutral foundation as the ecosystem matures.</td></tr>
  </tbody>
</table>

<h2>Where it stands today</h2>
<p>The project is <strong>stewarded by Action State Group</strong>, which also operates the reference services (the public transparency log and the hosted verifier) for now. This is the honest current state: a single steward, structured to become neutral — not yet a multi-party foundation. We say so plainly rather than imply neutrality the structure doesn't yet have.</p>

<h2>Roles</h2>
<table class="t">
  <tbody>
    <tr><th>Contributors</th><td>Anyone who opens an issue or PR. Contributions are made under the DCO (sign-off); no CLA.</td></tr>
    <tr><th>Maintainers</th><td>Review and merge changes, cut releases, and steward each repo. Co-maintainers from other organizations are explicitly welcome — earning merge rights through sustained, quality contribution.</td></tr>
    <tr><th>Technical Steering (planned)</th><td>As independent maintainers join, a lightweight Technical Steering Committee will take over cross-repo decisions — the standard Linux-Foundation-style model.</td></tr>
  </tbody>
</table>

<h2>How decisions are made</h2>
<p>Changes happen by pull request and public discussion, with lazy consensus among maintainers; significant changes get an issue first. The <em>specification</em> evolves through the IETF process — it's an individual Internet-Draft (<a class="ln" href="https://datatracker.ietf.org/doc/draft-mih-scitt-agent-action-capsule/">draft-mih-scitt-agent-action-capsule</a>), and the goal is to bring it to the SCITT working group, where the WG — not this project — decides its standing.</p>

<h2>Conformance to the final standard</h2>
<p>SCITT and COSE are still being finalized at the IETF. This profile is built to <strong>track them</strong>: as those drafts advance and are published as RFCs, the profile and its reference implementations will be updated to conform to the final versions, and any breaking changes will be versioned and documented. Building on it today should not strand you when the standard lands.</p>

<h2>The path to a neutral foundation</h2>
<p>Donation is a commitment, not just a hope. The intended sequence:</p>
<table class="t">
  <thead><tr><th>Trigger</th><th>What transfers</th></tr></thead>
  <tbody>
    <tr><th>Independent implementers + a stable profile</th><td>governance moves to a Technical Steering Committee with multi-org maintainers</td></tr>
    <tr><th>Foundation home selected</th><td>the <code>agentactioncapsule.org</code> domain, the &ldquo;Agent Action Capsule&rdquo; trademark, and the reference services transfer to the neutral home</td></tr>
    <tr><th>Spec adoption</th><td>change control of the profile follows the IETF process on WG adoption / RFC publication</td></tr>
  </tbody>
</table>
<p>Candidate homes are neutral, foundation-style bodies in the open-source / standards world; the specific home will be chosen with the community rather than announced unilaterally.</p>

<h2>Scope &amp; boundaries</h2>
<p>The open project is the <strong>record layer</strong>: the profile, the producer (with example constraint manifests), the verifier, and the anchor. Acting on declared constraints at runtime — <em>enforcement</em> — is a separate concern that composes with a policy gateway. The capsule records what happened; it does not gate. We call that boundary out so the open/commercial line is transparent, not implied.</p>

<div class="callout">Want to help shape it? Open an issue or PR on <a class="ln" href="https://github.com/action-state-group">GitHub</a>, comment on the <a class="ln" href="https://datatracker.ietf.org/doc/draft-mih-scitt-agent-action-capsule/">draft</a>, or write <a class="ln" href="mailto:spec@actionstate.ai">spec@actionstate.ai</a>. A community chat (Discord/Slack) is coming soon.</div>
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
    <a class="dcard" href="/docs/quickstart.html"><div class="n">Quickstart</div><div class="d">Seal your first capsule with one <code>emit()</code> call, anchor it, and verify. Copy-paste-runnable.</div></a>
    <a class="dcard" href="/docs/verify-a-capsule.html"><div class="n">Verify a capsule</div><div class="d">Verify in the browser, on the command line, or as a library &mdash; same checks everywhere.</div></a>
  </div>
</div>

<div class="idx-group">
  <h2>Live &amp; interactive</h2>
  <div class="cards">
    <a class="dcard" href="/docs/explore.html"><div class="n">Explore a capsule</div><div class="d">Interactive: click each field, edit what goes into a digest, tamper one and watch the seal break, then verify a bundle as a skeptical auditor.</div></a>
    <a class="dcard" href="/docs/log.html"><div class="n">The public log, live</div><div class="d">Watch the transparency log in real time &mdash; total entries, latest checkpoint, operating-since, and the most recent records. Public, verifiable, nothing fabricated.</div></a>
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
        if slug not in PAGES:
            continue  # hand-written page (e.g. explore.html) — sidebar links to it but it is not generated
        p = PAGES[slug]
        body = p["body"] + go_deeper_html(slug)
        (OUT / f"{slug}.html").write_text(
            render(slug, p["title"], p["desc"], p["crumb"], body), encoding="utf-8")
        n += 1
    print(f"wrote {n} files to {OUT}")


if __name__ == "__main__":
    main()
