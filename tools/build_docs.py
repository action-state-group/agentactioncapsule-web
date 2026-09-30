#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate the agentactioncapsule.org docs layer as self-contained static HTML.

HashiCorp-style concept/docs pages in the neutral design family (ink/paper/indigo,
Inter + IBM Plex Mono). Each output file is single-file and self-contained — no
build step or framework is required to serve them; this generator only keeps the
shared chrome (tokens, nav, footer, sidebar) DRY at authoring time.

Run:  python3 tools/build_docs.py
Out:  docs/*.html  (one page per entry in PAGES, plus docs/index.html)

NEUTRALITY: these pages are neutral substrate only. No product or business content.
Standards status is stated honestly
(individual Internet-Draft; SCITT Architecture = RFC 9943; COSE Receipts = RFC 9942,
published; the CCF receipt profile is still an Internet-Draft).
"""
from __future__ import annotations

import pathlib
import re

OUT = pathlib.Path(__file__).resolve().parent.parent / "docs"

DRAFT_URL = "https://datatracker.ietf.org/doc/draft-mih-scitt-agent-action-capsule/"
CPB_DRAFT_URL = "https://datatracker.ietf.org/doc/draft-mih-sokolov-scitt-payload-binding/"
ORG_URL = "https://github.com/action-state-group"
ANCHOR_URL = "https://witness.agentactioncapsule.org"
VERIFY_URL = "https://verify.agentactioncapsule.org"
CPB_SITE_URL = "https://canonicalpayloadbinding.org/"
IP_URL = "/ip"

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
# NOTE: link text intentionally omits a hard-coded CPB revision number — CPB revises far more
# often than AAC (was -02, is -05 as of 2026-09), and a number here has gone stale twice. The
# href already points at the un-versioned Datatracker page, which always resolves to latest;
# keep the link text un-versioned too rather than re-adding a number that will rot again.
STATUS_NOTE = (
    "<strong>Status.</strong> The Agent Action Capsule profile "
    f'(<a class="ln" href="{DRAFT_URL}">draft-mih-scitt-agent-action-capsule</a>, latest revision on the Datatracker) '
    "is an individual IETF Internet-Draft — submitted for discussion, <em>not</em> "
    "adopted by a working group, and not a standard. A companion draft, the "
    "<strong>Canonical Payload Binding</strong> "
    f'(<a class="ln" href="{CPB_DRAFT_URL}">draft-mih-sokolov-scitt-payload-binding</a>, '
    "latest revision on the Datatracker; "
    f'<a class="ln" href="{CPB_SITE_URL}">site</a>), '
    "defines the shared canonicalization and digest-binding layer. Both build on the "
    'IETF SCITT Architecture (<a class="ln" href="https://www.rfc-editor.org/rfc/rfc9943">RFC&nbsp;9943</a>) '
    'and the COSE Receipts specification (<a class="ln" href="https://www.rfc-editor.org/rfc/rfc9942">RFC&nbsp;9942</a>, now published).'
)

# What is signed by default, stated once (2026-09-26 review: three pages disagreed). Settled from
# the spec (-05: capsule identity is independent of signing; Producer Envelopes are a MAY) and from
# capsule-emit's code (seal() always signs with a persisted per-ledger Ed25519 key; the only
# unsigned append is the separately named log() verb).
SIGNING_NOTE = (
    "A capsule's identity is its <code>capsule_id</code>, a SHA-256 over the canonical capsule, and it "
    "does not depend on any signature. The specification makes signing optional: a producer MAY add one "
    "or more <code>COSE_Sign1</code> Producer Envelopes over the <code>capsule_id</code>. The reference "
    'producer, <a class="ln" href="https://github.com/action-state-group/capsule-emit">capsule-emit</a>, '
    "signs every capsule it seals, by default, with a per-ledger Ed25519 key; its only unsigned path is "
    "the separately named <code>log()</code> call."
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

  /* DOCS SHELL */
  .docs{display:grid;grid-template-columns:236px 1fr;gap:52px;padding:40px 0 64px}

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
  code{font-family:var(--mono);font-size:.88em;background:var(--paper-2);border:1px solid var(--line);border-radius:5px;padding:1px 6px;overflow-wrap:anywhere}
  pre.code{background:var(--ink);color:#E8ECF4;border-radius:12px;padding:20px;overflow-x:auto;font-family:var(--mono);font-size:13px;line-height:1.7;border:1px solid var(--line-2);margin:6px 0 18px}
  pre.code code{background:none;border:none;padding:0;font-size:inherit;color:inherit}
  pre.code .c{color:#7E8AA0} pre.code .s{color:#9DE2B8} pre.code .k{color:#C58AF9}
  pre.code .fn{color:#7FB4FF} pre.code .ok{color:#54D08A;font-weight:600}
  .tw{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:6px 0 20px;border:1px solid var(--line);border-radius:10px}
  table.t{border-collapse:collapse;width:100%;font-size:13.5px}
  table.t th,table.t td{padding:11px 14px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
  table.t thead th{font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);background:var(--paper-2)}
  table.t tbody th{font-weight:600;white-space:nowrap}
  table.t tbody td{color:var(--muted)}
  table.t tr:last-child th,table.t tr:last-child td{border-bottom:none}
  .callout{background:var(--paper-2);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;padding:14px 18px;font-size:14px;margin:6px 0 20px}
  .callout.warn{border-left-color:var(--verify)}
  .callout.deeper{border-left-color:var(--verify);background:var(--verify-soft)}

  /* DOCS INDEX CARDS */
  .idx-group{margin-bottom:34px}
  .idx-group h2{font-size:15px;font-family:var(--mono);letter-spacing:1px;text-transform:uppercase;color:var(--muted-2);margin-bottom:14px;font-weight:500}
  .idx-group .note{font-size:14px;color:var(--muted);line-height:1.6;margin:-6px 0 14px}
  .cards{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
  .dcard{border:1px solid var(--line);border-radius:12px;padding:20px 22px;background:#fff;text-decoration:none;transition:border-color .15s,transform .15s;display:block}
  .dcard:hover{border-color:var(--ink);transform:translateY(-2px)}
  .dcard .n{font-size:16px;font-weight:600;letter-spacing:-0.2px;margin-bottom:6px}
  .dcard .d{font-size:13.5px;color:var(--muted)}


  @media(max-width:900px){ .cards{grid-template-columns:1fr} }
"""

# ---------------------------------------------------------------------------
# One table of contents. The docs sidebar, prev/next and the docs index are all built from it, so
# a page cannot be in one and missing from another (2026-09-26 review: the index was missing five
# pages, and hand-written pages carried their own, drifting copies of the sidebar and footer).
# (group, index heading, [(key, href, sidebar title, card title, card description)])
# ---------------------------------------------------------------------------
TOC = [
    ("Use cases", "Use cases", [
        ("use-cases", "/docs/use-cases.html", "Use cases", "Use cases",
         "Where the record layer applies today &mdash; decentralized inference, and composing with other logs."),
        ("case-study-mesh-llm", "/docs/case-study-mesh-llm.html", "Case study: Mesh-LLM", "Case study: Mesh-LLM",
         "Accountability for strangers' machines, with no central operator and no ranking of nodes."),
    ]),
    ("Interop", "Interop", [
        ("interop/trace-registry", "/docs/interop/trace-registry.html", "The TRACE Registry", "The TRACE Registry",
         "An independent public registry whose checkpoint layer uses CLL &mdash; what it records, which parts it uses, and how to check an entry yourself."),
    ]),
    ("Concepts", "Concepts", [
        ("witness-landing", "/docs/witness-landing.html", "You've reached a witness", "You've reached a witness",
         "Followed a link from a checkpoint or a receipt? Start here &mdash; what it shows, what it never does, and how to check it yourself."),
        ("what-is-a-capsule", "/docs/what-is-a-capsule.html", "What is a Capsule?", "What is an Agent Action Capsule?",
         "A signed, tamper-evident record of an agent action &mdash; and the three properties that make it verifiable."),
        ("how-it-works", "/docs/how-it-works.html", "How it works", "How it works",
         "Both sides: the organisation seals each action and registers a checkpoint with a Transparency Service, which fixes the date; later, a party entitled to ask requests a slice and recomputes the answer offline."),
        ("statement-vs-transparency-layer", "/docs/statement-vs-transparency-layer.html", "Statement vs transparency layer", "Statement vs transparency layer",
         "What happened vs where it is recorded &mdash; and why the statement is structure-independent."),
        ("what-is-a-transparency-service", "/docs/what-is-a-transparency-service.html", "What is a Transparency Service?", "What is a Transparency Service?",
         "Register, receipt, log &mdash; and the boundary between a transparency service and a verifier."),
        ("verifiable-data-structures", "/docs/verifiable-data-structures.html", "Verifiable Data Structures", "Verifiable Data Structures",
         "RFC9162_SHA256 (vds=1) vs CCF ccf.v1 (vds=2), and what stays constant across them."),
        ("how-verification-works", "/docs/how-verification-works.html", "How verification works", "How verification works",
         "Three independent checks: the capsule_id, the signature, then the inclusion proof &mdash; all from the bytes, offline."),
        ("trust-map", "/docs/trust-map.html", "Trust map", "Trust map: what each check shows",
         "Each check in plain words: what it shows, what it does not show, and what &ldquo;not checked here&rdquo; means."),
        ("whats-consequential", "/docs/whats-consequential.html", "What's consequential", "What's consequential",
         "Seal what changes the world, plus reads of sensitive data; everything else is observability."),
        ("how-it-composes", "/docs/how-it-composes.html", "How it composes", "How it composes with your stack",
         "Identity, authorization and transparency logs stay where they are; the capsule references their evidence by digest."),
        ("witness-anywhere", "/docs/witness-anywhere.html", "Witness anywhere", "Witness anywhere",
         "Only a digest and a timestamp leave: witness at the public log, run your own, or self-host where the hash never leaves."),
    ]),
    ("Guides", "Guides", [
        ("quickstart", "/docs/quickstart.html", "Quickstart", "Quickstart",
         "Seal your first capsule with one <code>seal()</code> call, witness it, and verify. Copy-paste-runnable."),
        ("verify-a-capsule", "/docs/verify-a-capsule.html", "Verify a capsule", "Verify a capsule",
         "Verify in the browser, on the command line, or as a library &mdash; same checks everywhere."),
        ("a2a-ap2-example", "/docs/a2a-ap2-example.html", "A2A + AP2 example", "A2A + AP2 example",
         "An A2A callee seals a capsule on every AP2 payment action: the mandate is the &lsquo;may&rsquo;, the capsule is the &lsquo;did&rsquo;."),
    ]),
    ("Live", "Live &amp; interactive", [
        ("explore", "/docs/explore.html", "Explore a capsule", "Explore a capsule",
         "Interactive: click each field, edit what goes into a digest, tamper one and watch the seal break, then verify a bundle as a skeptical auditor."),
        ("log", "/docs/log.html", "The public log, live", "The public log, live",
         "Watch the transparency log in real time &mdash; total entries, latest checkpoint, operating-since, and the most recent records."),
    ]),
    ("Reference", "Reference", [
        ("glossary", "/docs/glossary.html", "Glossary", "Glossary",
         "SCITT, COSE_Sign1, Receipt, VDS, inclusion &amp; consistency proofs, the disposition list, witness vs anchored."),
        ("translation", "/docs/translation.html", "Translation (dev/auditor/spec)", "Translation: dev / auditor / spec",
         "The same concepts and verbs in three registers &mdash; the word a developer, an auditor, or the spec text would use."),
    ]),
    ("Extensions", "Extensions", [
        ("bilateral", "/docs/bilateral.html", "Bilateral attestation", "Bilateral attestation",
         "When two organizations act together: each party holds proof of the other's commitment, checkable by a third party who trusts neither."),
    ]),
    ("Project", "Project", [
        ("governance", "/docs/governance.html", "Governance", "Governance",
         "Open and built to be donated to a neutral foundation; governance modeled on Linux Foundation practice."),
        ("ip", IP_URL, "Patent posture", "Patent posture",
         "The specifications are unencumbered: the provisional applications were expressly abandoned, and no license is required."),
    ]),
]
TOC_ENTRIES = [e for _, _, items in TOC for e in items]
ORDER = [e[0] for e in TOC_ENTRIES]
HREF = {e[0]: e[1] for e in TOC_ENTRIES}
SHORT = {e[0]: e[2] for e in TOC_ENTRIES}

# Hand-written pages that take the shared chrome at build time: path -> (active nav item, TOC key).
# The build rewrites only what sits between <!--chrome:NAME--> markers (added on first run), so the
# page bodies stay hand-written while the header, sidebar, prev/next and footer come from here.
HAND_PAGES = {
    "index.html": ("standard", None),
    "ip.html": ("docs", "ip"),
    "docs/explore.html": ("docs", "explore"),
    "docs/log.html": ("docs", "log"),
    "docs/use-cases.html": ("docs", "use-cases"),
    "docs/case-study-mesh-llm.html": ("docs", "case-study-mesh-llm"),
    "docs/witness-landing.html": ("docs", "witness-landing"),
    "docs/translation.html": ("docs", "translation"),
    "docs/bilateral.html": ("docs", "bilateral"),
    "docs/a2a-ap2-example.html": ("docs", "a2a-ap2-example"),
    "docs/interop/trace-registry.html": ("docs", "interop/trace-registry"),
    "extensions/a2a-task-evidence/v1/index.html": ("docs", None),
    "profiles/a2a-task-evidence/aac-cll-scitt/v1/index.html": ("docs", None),
}

# ---------------------------------------------------------------------------
# Shared chrome: header (with a mobile menu), sidebar, prev/next, footer
# ---------------------------------------------------------------------------
CHROME_CSS = """
  /* shared chrome (tools/build_docs.py) */
  nav{position:sticky;top:0;z-index:50;background:rgba(252,252,250,0.92);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
  .nav-in{max-width:1140px;margin:0 auto;padding:14px 32px;display:flex;align-items:center;justify-content:space-between;gap:18px}
  .brand{display:flex;align-items:center;gap:10px;font-weight:600;font-size:15px;letter-spacing:-0.2px;text-decoration:none;color:var(--ink);white-space:nowrap}
  .brand .glyph{width:22px;height:22px;border:1.5px solid var(--ink);border-radius:5px;position:relative;flex-shrink:0}
  .brand .glyph::after{content:'';position:absolute;inset:4px;border-left:1.5px solid var(--accent);border-bottom:1.5px solid var(--accent);transform:rotate(-45deg) translate(1px,-1px)}
  .nav-links{display:flex;gap:22px;align-items:center}
  .nav-links a{font-size:13.5px;color:var(--muted);text-decoration:none;transition:color .15s;white-space:nowrap}
  .nav-links a:hover{color:var(--ink)}
  .nav-links a.active{color:var(--ink);font-weight:600}
  .nav-ghost{font-family:var(--mono);font-size:13px;border:1px solid var(--line);padding:7px 14px;border-radius:7px;color:var(--ink)!important}
  .nav-ghost:hover{border-color:var(--ink)}
  .nav-toggle{display:none;align-items:center;gap:8px;font:inherit;font-size:13.5px;color:var(--ink);background:transparent;border:1px solid var(--line);border-radius:7px;padding:6px 12px;cursor:pointer}
  .nav-toggle .bars{width:14px;height:10px;border-top:1.5px solid currentColor;border-bottom:1.5px solid currentColor;position:relative}
  .nav-toggle .bars::after{content:'';position:absolute;left:0;right:0;top:3.5px;border-top:1.5px solid currentColor}
  .side-d{position:sticky;top:78px;align-self:start;max-height:calc(100vh - 96px);overflow-y:auto}
  .side-d>summary{display:none}
  .side-d .side{position:static;max-height:none;overflow:visible;background:none;border:none;backdrop-filter:none;padding:0}
  .side h5{font-family:var(--mono);font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted-2);margin:20px 0 10px}
  .side h5:first-child{margin-top:0}
  .side a{display:block;font-size:14px;color:var(--muted);text-decoration:none;padding:5px 0 5px 12px;border-left:2px solid var(--line);transition:all .12s}
  .side a:hover{color:var(--ink);border-left-color:var(--muted-2)}
  .side a.active{color:var(--accent);border-left-color:var(--accent);font-weight:600}
  .next{display:flex;justify-content:space-between;gap:16px;margin-top:48px;padding-top:24px;border-top:1px solid var(--line);flex-wrap:wrap}
  .next a{flex:1;min-width:200px;border:1px solid var(--line);border-radius:12px;padding:16px 18px;text-decoration:none;transition:border-color .15s}
  .next a:hover{border-color:var(--ink)}
  .next .dir{font-family:var(--mono);font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted-2);margin-bottom:5px}
  .next .ttl{font-size:15px;font-weight:600;color:var(--ink)}
  .next a.n{text-align:right}
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
    .docs{grid-template-columns:1fr;gap:20px}
    .side-d{position:static;max-height:none;overflow:visible;border:1px solid var(--line);border-radius:10px;padding:0 14px}
    .side-d>summary{display:block;cursor:pointer;padding:11px 0;font-family:var(--mono);font-size:12px;letter-spacing:1px;text-transform:uppercase;color:var(--muted)}
    .side-d .side{display:flex;flex-wrap:wrap;gap:6px 16px;padding-bottom:14px}
    .side-d .side h5{width:100%;margin:8px 0 2px}
    .side-d .side a{border-left:none;padding:3px 0}
  }
  @media(max-width:860px){
    .nav-in{padding:12px 16px;flex-wrap:wrap;gap:10px}
    .nav-links{flex-wrap:wrap;gap:6px 16px;overflow:visible}
    html.js .nav-toggle{display:inline-flex}
    html.js .nav-links{display:none;width:100%;flex-direction:column;align-items:stretch;gap:0;padding:4px 0 8px}
    html.js .nav-links.open{display:flex}
    html.js .nav-links a{display:block;padding:10px 0;font-size:15px}
    html.js .nav-links a:not(.nav-ghost){display:block}
    html.js .nav-ghost{border:none;padding:10px 0;font-family:inherit;font-size:15px}
  }
  @media(max-width:560px){ .wrap{padding-left:16px;padding-right:16px} footer{padding:36px 0 44px} .foot-cols{gap:28px} }
"""

CHROME_HEAD = (
    "<script>document.documentElement.className+=' js';</script>\n"
    f"<style>{CHROME_CSS}</style>"
)

CHROME_JS = """<script>
(function(){
  var t=document.querySelector('.nav-toggle'), l=document.getElementById('nav-links');
  if(t&&l){ t.addEventListener('click',function(){ var o=l.classList.toggle('open'); t.setAttribute('aria-expanded',o?'true':'false'); }); }
  if(window.matchMedia&&window.matchMedia('(max-width:900px)').matches){
    document.querySelectorAll('details.side-d').forEach(function(d){ d.open=false; });
  }
})();
</script>"""


def nav_html(active: str) -> str:
    def a(key, href, label, extra=""):
        cls = ' class="active"' if key == active else ""
        return f'      <a{cls}{extra} href="{href}">{label}</a>'
    return "\n".join([
        '<nav aria-label="Site">',
        '  <div class="nav-in">',
        '    <a class="brand" href="/"><span class="glyph"></span> Agent Action Capsule</a>',
        '    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="nav-links"><span class="bars" aria-hidden="true"></span>Menu</button>',
        '    <div class="nav-links" id="nav-links">',
        a("standard", "/", "Standard"),
        a("log", ANCHOR_URL, "Transparency Log"),
        a("verify", VERIFY_URL, "Verifier"),
        a("docs", "/docs/", "Docs"),
        f'      <a class="nav-ghost" href="{ORG_URL}">Source &#x2197;</a>',
        f'      <a href="{DRAFT_URL}">Draft (IETF) &#x2197;</a>',
        "    </div>",
        "  </div>",
        "</nav>",
    ])


# One footer for every page (2026-09-26 review: there were four variants).
FOOTER = f"""<footer>
  <div class="wrap">
    <div class="foot-in">
      <div class="foot-brand">
        <a class="brand" href="/"><span class="glyph"></span> Agent Action Capsule</a>
        <p>An open, individual profile (an IETF Internet-Draft; not WG-adopted) built on the SCITT Architecture (<a href="https://www.rfc-editor.org/rfc/rfc9943" style="color:inherit">RFC&nbsp;9943</a>), for verifiable records of agent actions. Stewarded today by Action State Group, built to be donated to a neutral home.</p>
      </div>
      <div class="foot-cols">
        <div class="foot-col">
          <h5>Standard</h5>
          <a href="/">Overview</a>
          <a href="/#compose">Composition</a>
          <a href="/docs/">Docs</a>
          <a href="{DRAFT_URL}">AAC draft (latest) &#x2197;</a>
          <a href="{CPB_DRAFT_URL}">CPB draft (latest) &#x2197;</a>
          <a href="https://datatracker.ietf.org/doc/draft-mih-sato-agent-accountability-composition/">Composition draft (latest) &#x2197;</a>
          <a href="{CPB_SITE_URL}">Canonical Payload Binding &#x2197;</a>
          <a href="/talks/lf-aaif-scitt-aac-cll-cpb-2026-09-02.pdf">Talk slides (LF AAIF WG, Sep 2026) &#x2197;</a>
        </div>
        <div class="foot-col">
          <h5>Services</h5>
          <a href="{ANCHOR_URL}">Transparency Log</a>
          <a href="{VERIFY_URL}">Verifier</a>
        </div>
        <div class="foot-col">
          <h5>Source</h5>
          <a href="{ORG_URL}">GitHub &#x2197;</a>
          <a href="https://github.com/action-state-group/capsule-emit/blob/main/ADOPT.md">Adopters guide &#x2197;</a>
          <a href="https://github.com/action-state-group/agent-action-capsule/tree/main/vectors">Capsule test vectors &#x2197;</a>
          <a href="https://github.com/ietf-wg-scitt/examples">SCITT receipt vectors (WG) &#x2197;</a>
        </div>
        <div class="foot-col">
          <h5>Project</h5>
          <a href="/docs/governance.html">Governance</a>
          <a href="{IP_URL}">Patent posture</a>
        </div>
      </div>
    </div>
    <div class="foot-note">Open source &middot; built to be donated &middot; agentactioncapsule.org</div>
  </div>
</footer>"""


def sidebar_html(active: str) -> str:
    ov_cls = ' class="active"' if active == "index" else ""
    out = ['<details class="side-d" open><summary>Docs menu</summary>', '<nav class="side" aria-label="Docs">',
           '<h5>Documentation</h5>', f'<a href="/docs/"{ov_cls}>Overview</a>']
    for label, _, items in TOC:
        out.append(f"<h5>{label}</h5>")
        for key, href, short, _, _ in items:
            cls = ' class="active"' if key == active else ""
            out.append(f'<a href="{href}"{cls}>{short}</a>')
    out += ["</nav>", "</details>"]
    return "\n".join(out)


def next_block(key: str) -> str:
    if key not in ORDER:
        return ""
    i = ORDER.index(key)
    if i > 0:
        p = ORDER[i - 1]
        prev_a = (f'<a class="p" href="{HREF[p]}"><div class="dir">&#8592; Previous</div>'
                  f'<div class="ttl">{SHORT[p]}</div></a>')
    else:
        prev_a = ('<a class="p" href="/docs/"><div class="dir">&#8592; Previous</div>'
                  '<div class="ttl">Overview</div></a>')
    nxt_a = ""
    if i < len(ORDER) - 1:
        n = ORDER[i + 1]
        nxt_a = (f'<a class="n" href="{HREF[n]}"><div class="dir">Next &#8594;</div>'
                 f'<div class="ttl">{SHORT[n]}</div></a>')
    return f'<div class="next">{prev_a}{nxt_a}</div>'


def index_groups_html() -> str:
    out = []
    for _, heading, items in TOC:
        out.append(f'<div class="idx-group">\n  <h2>{heading}</h2>\n  <div class="cards">')
        for _, href, _, title, desc in items:
            out.append(f'    <a class="dcard" href="{href}"><div class="n">{title}</div><div class="d">{desc}</div></a>')
        out.append("  </div>\n</div>\n")
    return "\n".join(out)


def _mark(name: str, content: str) -> str:
    return f"<!--chrome:{name}-->{content}<!--/chrome:{name}-->"


def _splice(html: str, name: str, content: str, legacy: str | None, insert_before: str | None = None) -> str:
    """Replace the marked region NAME; on first run, replace the legacy element or insert."""
    block = _mark(name, content)
    marked = re.compile(rf"<!--chrome:{name}-->.*?<!--/chrome:{name}-->", re.S)
    if marked.search(html):
        return marked.sub(lambda m: block, html, count=1)
    if legacy:
        m = re.search(legacy, html, re.S)
        if m:
            return html[:m.start()] + block + html[m.end():]
    if insert_before and insert_before in html:
        i = html.index(insert_before)
        return html[:i] + block + "\n" + html[i:]
    raise SystemExit(f"chrome: cannot place {name!r}")


def rechrome(rel: str, active: str, key: str | None) -> None:
    path = OUT.parent / rel
    html = path.read_text(encoding="utf-8")
    html = _splice(html, "head", CHROME_HEAD, None, insert_before="</head>")
    html = _splice(html, "nav", nav_html(active), r'<nav>\s*<div class="nav-in">.*?</nav>')
    has_side = 'class="side"' in html or "<!--chrome:side-->" in html
    if has_side:
        html = _splice(html, "side", sidebar_html(key or ""), r'<nav class="side"[^>]*>.*?</nav>')
        html = _splice(html, "next", next_block(key or ""), r'<div class="next">.*?</a></div>',
                       insert_before="</article>")
    html = _splice(html, "footer", FOOTER, r"<footer>.*?</footer>")
    html = _splice(html, "js", CHROME_JS, None, insert_before="</body>")
    path.write_text(html, encoding="utf-8")


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
{chrome_head}
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
{chrome_js}
</body>
</html>
"""


def wrap_tables(body: str) -> str:
    # Every table.t sits in a horizontal scroller so a wide table scrolls inside itself instead of
    # widening the page on a phone (2026-09-26 review: 12 pages overflowed at 375px).
    return re.sub(r'(<table class="t".*?</table>)', r'<div class="tw">\1</div>', body, flags=re.S)


def render(slug, title, desc, crumb, body, *, is_index=False, css=""):
    body = wrap_tables(body)
    url = "https://agentactioncapsule.org/docs/" if is_index else f"https://agentactioncapsule.org/docs/{slug}.html"
    return PAGE.format(
        title=title, desc=desc, css=CSS + css, url=url,
        chrome_head=_mark("head", CHROME_HEAD), nav=_mark("nav", nav_html("docs")),
        footer=_mark("footer", FOOTER), chrome_js=_mark("js", CHROME_JS),
        sidebar=_mark("side", sidebar_html("index" if is_index else slug)),
        crumb=crumb, body=body,
        nxt="" if is_index else _mark("next", next_block(slug)),
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
    <tr><th>Signed</th><td>The capsule is a statement committing to the action, its inputs and outputs (by digest), and the model/runtime that produced it. It is always content-addressed, and a producer signs that address with COSE; the reference producer signs every capsule by default. Change any byte and verification fails.</td></tr>
    <tr><th>Transparent</th><td>The statement is registered to a transparency service, which returns a receipt proving the record was included in an append-only log that cannot quietly drop or rewrite history.</td></tr>
    <tr><th>Third-party verifiable</th><td>An auditor, third party, or regulator checks the signature and the inclusion proof from the bytes alone &mdash; no access to the operator's systems. You trust the log's key, not the operator.</td></tr>
  </tbody>
</table>

<h2>What a capsule commits to</h2>
<p>A capsule is a JSON record of media type <code>application/agent-action-capsule+json</code>. A producer signs it with a <code>COSE_Sign1</code> Producer Envelope whose payload is the capsule's 32-byte <code>capsule_id</code>. The record commits to:</p>
<ul>
  <li>the <strong>action</strong> performed (an effect type and its identifying fields);</li>
  <li><strong>input and output digests</strong> &mdash; SHA-256 of what went in and what came out, so raw values stay local while the proof travels;</li>
  <li>the <strong>producing context</strong> &mdash; the model and runtime that generated the action.</li>
</ul>
<p>Because inputs and outputs are committed <em>by digest</em>, anyone can check a capsule's integrity without seeing the sensitive payloads.</p>

<h2>What gets sealed &mdash; the fields</h2>
<p>The seal is the <code>capsule_id</code>: the SHA-256 of the canonical capsule. Recompute it and it must match byte-for-byte &mdash; that hash <em>is</em> the seal. Around it, a capsule commits the parts an agent action needs to be accountable:</p>
<table class="t">
  <thead><tr><th>Field</th><th>What it commits</th></tr></thead>
  <tbody>
    <tr><th>capsule_id</th><td>SHA-256 of the canonical capsule &mdash; the seal / content address.</td></tr>
    <tr><th>action / operator / developer / timestamp</th><td>what was done, the accountable tenant, the agent identity@version, and when.</td></tr>
    <tr><th>disposition</th><td>the <strong>may/did</strong> verdict &mdash; a registered <code>verdict_class</code> such as <code>executed</code>, <code>blocked</code>, <code>denied</code>, <code>timeout</code> or <code>errored</code> (the <a class="ln" href="/docs/glossary.html#disposition">full list</a>), plus who disposed it and an honest human-in-the-loop flag.</td></tr>
    <tr><th>effect</th><td>what was committed, plus the <strong>confirmed-effect binding</strong> so the claim and the outcome can't drift apart.</td></tr>
    <tr><th>model_attestation</th><td>which model decided, with the <strong>full input</strong> it saw (system prompt, context, tool definitions, and the action's arguments) and the <strong>output</strong> each <strong>committed as a digest</strong> (fixed-size; raw values, however large or sensitive, are never stored) plus best-effort compute.</td></tr>
    <tr><th>assurance</th><td>how far to trust it: attestation / effect / ledger modes.</td></tr>
    <tr><th>chain</th><td>the link to this producer's own previous capsule: a <code>parent_capsule_id</code> plus a registered relation (<code>follows</code>, <code>confirms</code>, <code>supersedes</code>, <code>epoch_opens</code>, <code>duplicates</code>). Same stream only; a citation of anything else &mdash; another producer's record, a grant, a receipt &mdash; goes in <code>references</code>.</td></tr>
  </tbody>
</table>

<h2>Content-private by construction</h2>
<p>Each evidence layer is <strong>hashed, and only the digest is committed</strong> &mdash; the raw prompt, vendor, or amount is never inside the capsule. You can hand someone a capsule and they learn <em>what happened</em> and can verify the seal, without seeing your inputs or outputs. Reveal a raw value later only when you choose, and anyone can re-hash it against the committed digest.</p>

<h2>Chains: approved &rarr; executed &rarr; confirmed</h2>
<p>A confirmation is itself a capsule that points at its parent by digest. That turns a decision and its follow-through into one verifiable trail &mdash; the basis for human-in-the-loop confirmation and for selective disclosure (show a chain that records authorization without exposing the underlying data).</p>
<p>A <code>confirmed</code> capsule is sealed only when the agent observes a reply or receipt back from the system or party it acted on &mdash; that returning confirmation is what closes the loop. It's why <code>confirmed</code> carries more weight than <code>dispatched</code>, which records only that the action was sent. When no confirmation comes back to observe, the capsule honestly stays <code>dispatched</code> or <code>executed</code>.</p>

<h2 id="assurance">Levels of assurance</h2>
<p>Tamper-evidence is always present (the <code>capsule_id</code> hash). A producer <em>signature</em> binds that hash to a key. An <em>existence proof</em> comes from registering the <code>capsule_id</code> with a transparency service &mdash; the receipt held beside the capsule. You adopt as much as your use case needs.</p>
<div class="callout"><strong>What is signed by default.</strong> {SIGNING_NOTE}</div>

<h2>What a capsule does not establish</h2>
<p>Honest claims matter. Know the limits before relying on this for audit or compliance:</p>
<ul>
  <li><strong>Attested, not verified.</strong> A capsule records what the agent <em>attested</em> it did &mdash; not that the real-world effect occurred. A <code>dispatched</code> capsule does not mean the write landed; a <code>confirmed</code> one does.</li>
  <li><strong>No anti-omission property.</strong> A capsule shows <em>this</em> action was recorded. It does not prevent an operator from simply not emitting a capsule for an action they'd rather not surface.</li>
  <li><strong>Signer = key-holder.</strong> The signature proves who held the signing key at the moment of sealing &mdash; not that the named agent actually ran the action. Key-management discipline is outside the capsule.</li>
  <li><strong>A hash alone names no one.</strong> Without a Producer Envelope, a capsule is tamper-evident but says nothing about who sealed it. The specification allows that; the reference producer does not do it by default (see <em>What is signed by default</em>, above).</li>
  <li><strong>Single-operator log &rArr; non-equivocation is operational.</strong> The public Transparency Service prevents the log from quietly rewriting history &mdash; but if one operator controls both the agent and the log, equivocation is an operational question, not a cryptographic one. Registering with a Transparency Service the operator does not run removes this.</li>
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
<p>Keeping the statement independent of the log means a single capsule can be registered with more than one transparency service, and verified the same way regardless of how each log structures its proofs. The action layer never changes when the log changes &mdash; this is what we mean by <a class="ln" href="/docs/verifiable-data-structures.html">verifiable-data-structure agnostic</a>.</p>

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
    desc="A SCITT Transparency Service registers signed statements, issues receipts, and records them in an append-only log. It is high-trust infrastructure — and it is not a verifier.",
    crumb="Concepts",
    body="""
<h1>What is a Transparency Service?</h1>
<p class="lede">A Transparency Service (TS) registers signed statements in an append-only log and issues a receipt proving inclusion &mdash; so a record can be shown to exist and to never have been quietly dropped or rewritten.</p>
<p style="color:var(--muted);font-size:15px;margin-top:-10px;margin-bottom:24px">You don't call this service directly. <code>seal()</code> registers the digest for you and hands back a witnessed record &mdash; this page explains what's happening underneath.</p>

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
    <tr><th>Operation</th><td>verify only</td><td>register statements, issue receipts, keep the log</td></tr>
    <tr><th>State</th><td>none (stateless)</td><td>a durable, append-only log</td></tr>
    <tr><th>Trust commitment</th><td>none &mdash; verify it yourself</td><td>uptime, integrity, non-equivocation</td></tr>
    <tr><th>Risk class</th><td>low (read-only utility)</td><td>high (operational trust infrastructure)</td></tr>
    <tr><th>Who must trust whom</th><td>nobody trusts the operator</td><td>the ecosystem trusts the log operator</td></tr>
  </tbody>
</table>
<p>A verifier that begins storing submissions, issuing receipts, or keeping a log has silently become a transparency service with all of its obligations.</p>

<h2>The trust model</h2>
<p>What you verify yourself: each signature, each inclusion proof, and consistency between any two tree heads &mdash; all from the bytes, offline. What the log commits to operationally: durable append-only storage, non-equivocation (one consistent view for everyone), and a stable, published signing key.</p>
<div class="callout">A live, neutral implementation runs at <a class="ln" href="https://witness.agentactioncapsule.org">witness.agentactioncapsule.org</a>. To check a receipt without running anything, use the <a class="ln" href="https://verify.agentactioncapsule.org">hosted verifier</a>.</div>
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
    <tr><th>Basis</th><td>RFC&nbsp;9162 (Certificate Transparency 2.0) Merkle trees, SHA-256</td><td>CCF (Confidential Consortium Framework) ledger receipts</td></tr>
    <tr><th>Proof shape</th><td>Merkle inclusion path + signed tree head</td><td>CCF ledger inclusion proof signed by the service identity</td></tr>
    <tr><th>Verify with</th><td>the log's public key + the leaf digest</td><td>the CCF service certificate / identity</td></tr>
    <tr><th>Published status</th><td>RFC&nbsp;9162 is a published RFC; the SCITT Architecture is <a class="ln" href="https://www.rfc-editor.org/rfc/rfc9943">RFC&nbsp;9943</a></td><td>CCF is an open-source framework; the SCITT mapping is a draft</td></tr>
  </tbody>
</table>

<h2>Why two?</h2>
<p>Different operators run different ledger technologies. The same Agent Action Capsule was registered to both an RFC&nbsp;9162 log (<code>vds=1</code>) <em>and</em> a real CCF node (<code>vds=2</code>), and both receipts check out &mdash; evidence that the statement layer is structure-independent. (The reference verifier <a class="ln" href="https://github.com/action-state-group/scitt-cose">scitt-cose</a> verifies both: its Python <code>verify_receipt</code> and its Go verifier accept <code>vds=1</code> and <code>vds=2</code>; its Rust crate accepts <code>vds=1</code> only and rejects anything else. The CCF receipt came from a CCF development node, not a production service.)</p>

<h2>What stays constant</h2>
<p>The signed statement &mdash; the capsule itself &mdash; does not change between <code>vds=1</code> and <code>vds=2</code>. Only the receipt differs. That is the whole point of separating <a class="ln" href="/docs/statement-vs-transparency-layer.html">the statement layer from the transparency layer</a>.</p>
<div class="callout">Cross-implementation test vectors for <code>RFC9162_SHA256</code> are published in the SCITT working group's examples repository: <a class="ln" href="https://github.com/ietf-wg-scitt/examples">ietf-wg-scitt/examples</a>.</div>
""",
)

PAGES["how-verification-works"] = dict(
    title="How verification works: signature + inclusion proof",
    desc="Verifying a capsule is three independent checks: recompute its capsule_id, check each producer signature over that id, and check the receipt's inclusion proof. All run from the bytes, offline.",
    crumb="Concepts",
    body=f"""
<h1>How verification works</h1>
<p class="lede">Verifying a capsule is three independent checks, in order. The <code>capsule_id</code> shows <strong>the record is intact</strong>. The signature proves <strong>who sealed it</strong>. The receipt proves <strong>the log included it</strong>. None requires trusting the operator &mdash; all run from the bytes, offline.</p>

<h2>Check 1 &mdash; the capsule_id</h2>
<p>The verifier recomputes the <code>capsule_id</code>: the SHA-256 of the canonical capsule. A carried value is never trusted. If any field changed after sealing, the recomputed value differs and the check fails.</p>

<h2>Check 2 &mdash; the signature</h2>
<p>A Producer Envelope is a <code>COSE_Sign1</code> whose payload is the 32-byte <code>capsule_id</code>. Given the producer's public key, the verifier confirms the signature covers that id. This establishes <em>who</em> sealed the record. A capsule can carry more than one envelope, and each is checked on its own; one with none is intact but unattributed.</p>
<div class="callout">{SIGNING_NOTE}</div>

<h2>Check 3 &mdash; the inclusion proof</h2>
<p>The transparency service returns a receipt: a signed proof that the statement's leaf digest sits in the log's verifiable data structure (for an RFC&nbsp;9162 log, a Merkle tree) at a given size. Given the log's public key and the leaf digest, the verifier recomputes the path to the signed tree head. This establishes that the record was <em>recorded</em> and is discoverable &mdash; not held privately by the operator.</p>

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
<div class="callout">Try it without installing anything at the <a class="ln" href="https://verify.agentactioncapsule.org">hosted verifier</a>, or run the same library yourself &mdash; see <a class="ln" href="/docs/verify-a-capsule.html">Verify a capsule</a>.</div>
""",
)

# How it works: the producer side (creating capsules) and the counterparty side (using them).
# Diagrams are HTML/CSS in the site's palette, not slide images; below 760px each diagram stacks
# into one column so nothing is wider than a 375px phone. Obligation and judgment are shown as
# ordinary sealed records with a generic example duty, never a named law.
HOW_IT_WORKS_CSS = """
  .hw-cols{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:8px 0 22px}
  .hw-col{border:1px solid var(--line);border-radius:12px;padding:18px 20px;background:#fff}
  .hw-col.seal{border-color:var(--verify);background:var(--verify-soft)}
  .hw-col h3{margin:0 0 4px;font-family:var(--mono);font-size:15px}
  .hw-col .sub{font-size:13.5px;color:var(--muted);margin-bottom:10px}
  .hw-col ul{margin:0 0 0 18px;font-size:14.5px}
  .hw-col li{margin-bottom:5px}
  .hw-col .bottom{font-size:13.5px;color:var(--muted);margin-top:10px;margin-bottom:0}
  .hw-dia{display:grid;grid-template-columns:1.55fr 1fr 1fr;gap:12px;margin:10px 0 8px;font-size:13px;line-height:1.45}
  .hw-p{border-radius:12px;padding:14px;min-width:0}
  .hw-p .hd{font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:1.2px;text-transform:uppercase;margin-bottom:4px}
  .hw-p .who{font-size:12.5px;margin-bottom:10px}
  .hw-org{background:var(--ink);color:#E8ECF4;border:1px solid var(--line-2)}
  .hw-org .who{color:#9AA3B2}
  .hw-wit{background:var(--paper-2);border:1px solid var(--line)}
  .hw-wit .who,.hw-rp .who{color:var(--muted)}
  .hw-rp{background:var(--accent-soft);border:1px solid #C9D3F5}
  .hw-org-in{display:grid;grid-template-columns:auto 1fr;gap:10px}
  .hw-agents{display:flex;flex-direction:column;gap:6px;padding-right:10px;border-right:1.5px dashed #5C6573}
  .hw-agents .lb{font-family:var(--mono);font-size:10px;color:#9AA3B2;text-transform:uppercase;letter-spacing:1px}
  .hw-chip{font-family:var(--mono);font-size:11.5px;border-radius:999px;padding:2px 10px;background:#54D08A;color:var(--ink);font-weight:600;text-align:center}
  .hw-cll .lb{font-family:var(--mono);font-size:11px;color:#9DE2B8;margin-bottom:6px}
  .hw-row{font-family:var(--mono);font-size:11.5px;border:1px solid var(--line-2);background:var(--ink-2);border-radius:7px;padding:5px 9px;margin-bottom:5px;overflow-wrap:anywhere}
  .hw-row.ck,.hw-row.rc{border-color:#54D08A;color:#9DE2B8}
  .hw-row.rv{border-style:dashed}
  .hw-row .d{color:#7E8AA0}
  .hw-store{margin-top:10px;font-size:12px;color:#9AA3B2;border-top:1px solid var(--line-2);padding-top:8px}
  .hw-store strong{color:#E8ECF4}
  .hw-box{background:#fff;border:1px solid var(--line);border-radius:9px;padding:9px 11px;margin-bottom:8px;overflow-wrap:anywhere}
  .hw-box.ok{border-color:var(--verify)}
  .hw-box.ghost{border-style:dashed;color:var(--muted-2);background:transparent}
  .hw-box .t{font-family:var(--mono);font-size:11.5px;font-weight:600;margin-bottom:2px}
  .hw-box.ok .t{color:var(--verify)}
  .hw-note{font-style:italic;color:var(--muted);font-size:12.5px}
  .hw-bundle{border:1.5px solid #C9A227;border-radius:9px;padding:9px 11px;margin-bottom:10px;font-family:var(--mono);font-size:11.5px}
  .hw-bundle .t{color:#E8C766;font-weight:600;margin-bottom:3px}
  .hw-out{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
  .hw-out span{font-family:var(--mono);font-size:11px;background:var(--paper);color:var(--ink);border-radius:999px;padding:2px 10px}
  .hw-flow{font-family:var(--mono);font-size:12px;color:var(--verify);margin:4px 0 4px;overflow-wrap:anywhere}
  .hw-cap{font-weight:600;font-size:15.5px;margin:6px 0 10px}
  .hw-key{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin:0 0 22px}
  .hw-arrow{display:none}
  .hw-q{display:grid;grid-template-columns:3fr 1.25fr;gap:14px;margin:10px 0 22px}
  .hw-qg{display:grid;grid-template-columns:auto 1fr 1fr 1fr;gap:8px;align-items:stretch}
  .hw-qg .rl{font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:1px;text-transform:uppercase;color:var(--muted);align-self:center;padding-right:4px}
  .hw-qc{border:1px solid var(--ink);border-radius:9px;padding:9px 10px;background:#fff;min-width:0}
  .hw-qc .q{font-weight:600;font-size:13.5px;line-height:1.3;margin-bottom:4px}
  .hw-qc .a{font-size:12px;color:var(--muted);line-height:1.4}
  .hw-qc.ten{border:2px dashed var(--ink);background:var(--paper-2);padding:14px}
  .hw-qc.ten .q{font-size:15px}
  @media(max-width:760px){
    .hw-cols,.hw-dia,.hw-q{grid-template-columns:1fr}
    .hw-arrow{display:block;text-align:center;font-family:var(--mono);font-size:12px;color:var(--muted);margin:-4px 0}
    .hw-qg{grid-template-columns:1fr 1fr}
    .hw-qg .rl{grid-column:1/-1;padding-top:6px}
  }
"""

PAGES["how-it-works"] = dict(
    title="How it works: creating capsules, and using them",
    desc="The two sides of an Agent Action Capsule. The organisation seals each action at the boundary and registers a checkpoint with a Transparency Service, which fixes the date. Later, a party entitled to ask requests a slice, gets the records or a signed refusal, and recomputes everything offline.",
    crumb="Concepts",
    css=HOW_IT_WORKS_CSS,
    body="""
<h1>How it works</h1>
<p class="lede">A capsule has two sides. The organisation whose agent acts creates the record at the moment of the action. Later, someone who was not in the room asks for part of it and checks the answer for themselves. This page walks through both sides, in that order.</p>

<h2 id="diary">A diary is not a signed record</h2>
<p>Most agents already write logs. A log and a signed record answer different questions.</p>
<div class="hw-cols">
  <div class="hw-col">
    <h3>An ordinary log</h3>
    <div class="sub">The operator's diary</div>
    <ul>
      <li>Editable</li>
      <li>Deletable</li>
      <li>Reorderable</li>
      <li>Often collected late, after something went wrong</li>
      <li>Written by the system it describes</li>
    </ul>
  </div>
  <div class="hw-col seal">
    <h3>seal()</h3>
    <div class="sub">A signed record</div>
    <ul>
      <li>Content-addressed: the record carries digests, and the content stays with you</li>
      <li>Signed at the boundary, by a key the model never holds</li>
      <li>Chained locally and append-only; checkpoints are registered with a witness</li>
      <li>Checkable by anyone, offline, with published public keys</li>
    </ul>
  </div>
</div>
<div class="callout">A note on names: the reference producer, <a class="ln" href="https://github.com/action-state-group/capsule-emit">capsule-emit</a>, also has a <code>log()</code> call, and it is not the diary on the left. A <code>log()</code> entry is chained, checkpointed and witnessed like a sealed capsule. It only leaves out the producer's signature, so a verifier reports its authorship as <em>not claimed</em>. Use <code>seal()</code> when it matters who made the record.</div>

<h2 id="line">The line</h2>
<p><strong>A log is enough, until someone else has to believe it.</strong></p>
<table class="t">
  <thead><tr><th>A log is good for</th><th>A log is not enough when</th></tr></thead>
  <tbody>
    <tr><td>debugging</td><td><strong>money moves</strong> &mdash; a payment, a trade, a refund</td></tr>
    <tr><td>ops dashboards</td><td><strong>a duty applies</strong> &mdash; a regulator, a contract, a customer's right</td></tr>
    <tr><td>&ldquo;what happened last night&rdquo;</td><td><strong>someone else was harmed</strong> &mdash; a counterparty, an evaluator, a court</td></tr>
    <tr><td>the author's own memory</td><td></td></tr>
  </tbody>
</table>
<p>Each case on the right has a party who was not in the room and does not take your word for it. For the operator, a diary is fine. Once a second party is entitled to the truth, the diary is a claim, not evidence. The rest of this page is what it takes for that party to believe a record without trusting whoever wrote it.</p>

<h2 id="create">1 of 2 &middot; Creating capsules</h2>
<p>Everything in this half happens inside the organisation, before anyone asks a question.</p>
<div class="hw-dia" role="img" aria-label="Diagram: an organisation's agents seal actions at a boundary into an append-only local log whose content stays in a payload store; a signed checkpoint goes to a witness that sees no content and returns a receipt; the relying party has nothing to verify yet.">
  <div class="hw-p hw-org">
    <div class="hd">Organisation &middot; create</div>
    <div class="who">the party whose agents act</div>
    <div class="hw-org-in">
      <div class="hw-agents">
        <span class="lb">boundary</span>
        <span class="hw-chip">agent</span>
        <span class="hw-chip">agent</span>
        <span class="hw-chip">agent</span>
      </div>
      <div class="hw-cll">
        <div class="lb">CLL &middot; append-only</div>
        <div class="hw-row ck">&#9650; checkpoint &middot; size 1,240 &middot; peaks &middot; signed</div>
        <div class="hw-row rc">&#10003; receipt &middot; 09:41Z</div>
        <div class="hw-row">&#9679; action &times;4 <span class="d">ad212d&hellip; 9f0e1c&hellip; 4b7a90&hellip;</span></div>
        <div class="hw-row rv">&#9675; received <span class="d">71c2e5&hellip; theirs</span></div>
        <div class="hw-row">&#9679; obligation <span class="d">a disclosure duty</span></div>
        <div class="hw-row">&#9679; judgment</div>
      </div>
    </div>
    <div class="hw-store"><strong>payload store</strong> &middot; the content stays here and never leaves</div>
  </div>
  <div class="hw-arrow">&darr; only the checkpoint goes out</div>
  <div class="hw-p hw-wit">
    <div class="hd">Witness</div>
    <div class="who">sees no content &middot; not operated by the organisation</div>
    <div class="hw-box"><div class="t">&#9650; checkpoint</div>received 09:41Z</div>
    <div class="hw-box ok"><div class="t">&#10003; receipt</div>registered no later than 09:41Z &middot; consistent with the previous checkpoint</div>
    <div class="hw-box ghost">&#10003; another witness</div>
  </div>
  <div class="hw-arrow">&darr; nobody has asked yet</div>
  <div class="hw-p hw-rp">
    <div class="hd">Relying party</div>
    <div class="who">a regulator, counterparty, auditor or evaluator</div>
    <div class="hw-box"><div class="t">verifier</div>verify.agentactioncapsule.org, or the CLI &middot; offline &middot; published keys</div>
    <p class="hw-note">Nothing to verify yet. Nobody has asked.</p>
  </div>
</div>
<p class="hw-cap">Nothing has left the organisation but a checkpoint, and the date is already fixed.</p>
<p class="hw-key">&#9679; sealed by the organisation &middot; &#9675; received, signed by someone else &middot; &#9650; checkpoint &middot; &#10003; witness receipt</p>
<ol>
  <li><strong>Seal at the boundary.</strong> Each consequential action is sealed where it leaves the agent, by a key the model never holds. The capsule carries digests of the inputs and outputs. The content itself stays in your payload store.</li>
  <li><strong>Carry in the other side's half.</strong> When a counterparty sends its own signed record, <code>received()</code> commits those exact bytes as they arrived. It never re-signs them, so the record stays theirs.</li>
  <li><strong>Seal what applied, and what was decided.</strong> The same log can hold the obligation an action was under (here, a disclosure duty) and any judgment made against it. They are ordinary sealed records; the format has no special case for them.</li>
  <li><strong>Checkpoint.</strong> The <a class="ln" href="https://github.com/action-state-group/checkpointed-local-log">checkpointed local log</a> (CLL) chains every entry, append-only. At intervals it signs a checkpoint: one small value that commits to its whole history so far, with its size and the tree's peaks.</li>
  <li><strong>Witness.</strong> Only the checkpoint goes to a witness, a SCITT Transparency Service that registers checkpoints under a <a class="ln" href="https://github.com/action-state-group/capsule-anchor/blob/main/OPERATOR_GUIDE.md#registration-policy">published consistency policy</a>. It returns a Receipt saying the checkpoint was registered no later than a given time. Under that policy, a checkpoint that carries a consistency proof is registered only if it extends the previous one. The organisation does not operate the witness, and you can register with more than one. See <a class="ln" href="/docs/witness-anywhere.html">witness anywhere</a>.</li>
</ol>

<h2 id="use">2 of 2 &middot; Using capsules</h2>
<p>Months later, someone entitled to the truth asks. The organisation discloses the record, and only the part that was asked for.</p>
<div class="hw-dia" role="img" aria-label="Diagram: the relying party sends an evidence request for a slice; the organisation answers with a bundle of the requested records, checkpoint, receipt and inclusion proofs, or a signed refusal; the relying party's verifier checks signatures, inclusion and the witness receipt offline.">
  <div class="hw-p hw-org">
    <div class="hd">Organisation &middot; asked about</div>
    <div class="who">answers from the same log</div>
    <div class="hw-bundle">
      <div class="t">bundle</div>
      &#9679; the requested records<br>
      withheld: digest only<br>
      &#9650; checkpoint &middot; &#10003; receipt<br>
      inclusion proofs<br>
      judgments
    </div>
    <div class="hw-cll">
      <div class="lb">CLL &middot; append-only</div>
      <div class="hw-row ck">&#9650; checkpoint &middot; size 1,240</div>
      <div class="hw-row rc">&#10003; receipt &middot; 09:41Z</div>
      <div class="hw-row">&#9679; action &times;4</div>
      <div class="hw-row rv">&#9675; received</div>
      <div class="hw-row">&#9679; obligation &middot; &#9679; judgment</div>
    </div>
    <div class="hw-out"><span>records</span><span>signed refusal</span></div>
  </div>
  <div class="hw-p hw-wit">
    <div class="hd">Witness</div>
    <div class="who">sees no content &middot; not operated by the organisation</div>
    <div class="hw-box ok"><div class="t">&#10003; receipt &middot; 09:41Z</div>grade: consistency-verified</div>
    <p class="hw-note">The date was fixed before anyone asked.</p>
  </div>
  <div class="hw-p hw-rp">
    <div class="hd">Relying party</div>
    <div class="who">a regulator, counterparty, auditor or evaluator</div>
    <div class="hw-box"><div class="t">evidence request</div>show me: actions under a disclosure duty, September 2026<br>by: a party entitled to ask</div>
    <div class="hw-box ok"><div class="t">verifier &middot; offline</div>signatures &#10003;<br>inclusion in checkpoint 09:41Z &#10003;<br>receipt &#10003; consistency-verified<br>counts recomputed &#10003;</div>
    <div class="hw-box ghost"><div class="t">absence</div>if no answer comes in time, the asker records its own request and the empty window</div>
  </div>
</div>
<p class="hw-flow">sealed &rarr; chained &rarr; checkpointed &rarr; registered &rarr; asked &rarr; disclosed &rarr; recomputed</p>
<p class="hw-cap">The relying party recomputes everything offline. They trust the arithmetic and the published keys, not the organisation.</p>
<p>The exchange follows <a class="ln" href="https://datatracker.ietf.org/doc/draft-mih-agent-evidence-request/">draft-mih-agent-evidence-request</a>, an individual Internet-Draft. A request names a <em>slice</em> (what evidence is wanted) and the checkpoint the answer has to verify against. Every request ends in exactly one of three outcomes:</p>
<table class="t">
  <thead><tr><th>Outcome</th><th>What it is</th><th>Who signs it</th></tr></thead>
  <tbody>
    <tr><th>The records</th><td>A bundle with the requested capsules, the checkpoint and its witness receipt, and an inclusion proof for each record. Anything outside the slice appears only as a digest.</td><td>The organisation, plus the witness's receipt</td></tr>
    <tr><th>A signed refusal</th><td>A refusal with a machine-readable reason, such as <code>not_authorized</code> or <code>no_such_subject</code> (&ldquo;we hold no such record&rdquo;). It is an answer, and the asker can keep it and show it to others.</td><td>The organisation</td></tr>
    <tr><th>Absence</th><td>No answer arrived before the asker's deadline. Nobody sends an absence; the asker records its own request and the window in which nothing came.</td><td>The asker, about its own attempt</td></tr>
  </tbody>
</table>
<p>The three are never converted into one another. An asker cannot turn a timeout into a refusal, and an organisation that stays silent has not refused. Silence is recorded as silence. And because the records were checkpointed and witnessed when they were sealed, an answer given months later cannot be backdated: the date was fixed before anyone asked.</p>

<h2 id="ten">Nine on your copy, one on theirs</h2>
<p>These are ten questions an investigator asks about an agent's record. Nine can be answered from your own copy, by recomputation. The tenth needs the other party's copy.</p>
<div class="hw-q">
  <div class="hw-qg">
    <div class="rl">Receipt</div>
    <div class="hw-qc"><div class="q">Rewrote the record?</div><div class="a">The <code>capsule_id</code> is recomputed from the bytes; any change breaks it.</div></div>
    <div class="hw-qc"><div class="q">Faked who signed?</div><div class="a">The signature is checked against the producer's published key.</div></div>
    <div class="hw-qc"><div class="q">Swapped the task?</div><div class="a">The capsule commits its inputs by digest; a different task gives a different digest.</div></div>
    <div class="rl">Log</div>
    <div class="hw-qc"><div class="q">Left it out of the log?</div><div class="a">An inclusion proof ties the record to a checkpoint.</div></div>
    <div class="hw-qc"><div class="q">Faked the log's seal?</div><div class="a">The checkpoint's signature is checked, and the witness receipt names the same checkpoint.</div></div>
    <div class="hw-qc"><div class="q">Made it up later?</div><div class="a">The receipt bounds when the checkpoint existed; a later record is not in it.</div></div>
    <div class="rl">Fine print</div>
    <div class="hw-qc"><div class="q">Reordered history?</div><div class="a">A consistency proof between checkpoints shows the log only appended.</div></div>
    <div class="hw-qc"><div class="q">Used a key it shouldn't?</div><div class="a">A key that is not in the producer's published set fails the signature check.</div></div>
    <div class="hw-qc"><div class="q">Recorded only part?</div><div class="a">In a two-party exchange each half is signed, so a half with no match is counted, not estimated.</div></div>
  </div>
  <div class="hw-qc ten"><div class="q">10 &middot; Faked the outcome?</div><div class="a">Your copy shows what your side sealed. Whether it happened on the other side takes the other party's signed record: their half, carried in with <code>received()</code>, or their own copy. See <a class="ln" href="/docs/bilateral.html">bilateral attestation</a>.</div></div>
</div>
<div class="callout">A witnessed record is not a true record. Every check above is about integrity: who signed, what was included, and when. None of them says whether the agent did the right thing. See <a class="ln" href="/docs/how-verification-works.html">how verification works</a> for the checks themselves, and <a class="ln" href="/docs/verify-a-capsule.html">verify a capsule</a> to run them.</div>
""",
)

PAGES["quickstart"] = dict(
    title="Quickstart: seal your first capsule",
    desc="Seal an agent action as a verifiable capsule with one seal() call, witness it via a transparency log, and verify the result. Copy-paste-runnable.",
    crumb="Guides",
    body="""
<h1>Quickstart: seal your first capsule</h1>
<p class="lede">From install to a witnessed, verified record in a few minutes &mdash; using <code>seal()</code>, the canonical one-call API.</p>

<h2>1. Install</h2>
<pre class="code"><code>pip install capsule-emit</code></pre>

<div class="callout"><strong>Where you start matters.</strong> <code>seal()</code> is signed and witnessed by default, async and non-blocking &mdash; no signup, no key. If you want to try locally first with zero network egress, set <code>CAPSULE_WITNESS=off</code> (or pass <code>witness=False</code>): you get a signed, structured record and a local ledger file you can verify offline. One config change turns witnessing back on when you&rsquo;re ready. See <a class="ln" href="https://agentactioncapsule.org/#adopt-ladder">the adoption ladder</a>.</div>

<h2>2. Seal an action</h2>
<p>Call <code>seal()</code> once at each consequential action &mdash; the payload is the first positional argument, never a keyword. <code>action</code>, <code>operator</code>, <code>developer</code>, and <code>agent_output</code> are what you'll always pass; <code>model</code>, <code>verdict</code>, and <code>effect</code> are optional (adapters fill in what they can &mdash; the MCP adapter, for example, sees the tool boundary, not the LLM, so pass <code>model</code> explicitly there if you want it sealed).</p>
<pre class="code"><code><span class="k">from</span> capsule_emit <span class="k">import</span> seal

result = place(<span class="s">"Frobozz Supply"</span>, <span class="s">"4210.00"</span>, <span class="s">"PO-0047"</span>)  <span class="c"># your tool logic</span>

cap = seal(
    {<span class="s">"vendor"</span>: <span class="s">"Frobozz Supply"</span>, <span class="s">"total"</span>: <span class="s">"4210.00"</span>},  <span class="c"># payload &mdash; first arg; monetary values are strings, not floats</span>
    action=<span class="s">"submit_order"</span>,
    operator=<span class="s">"acme-co"</span>,                <span class="c"># accountable tenant</span>
    developer=<span class="s">"po-agent@v1"</span>,           <span class="c"># agent identity + version</span>
    agent_output=result,
    model={<span class="s">"provider"</span>: <span class="s">"example-provider"</span>, <span class="s">"model_id"</span>: <span class="s">"example-model"</span>},
    verdict=<span class="s">"executed"</span>,               <span class="c"># a verdict_class: executed | blocked | denied | …</span>
    effect={<span class="s">"type"</span>: <span class="s">"submit_order"</span>, <span class="s">"status"</span>: <span class="s">"dispatched"</span>},
)
print(cap.capsule_id, cap.signature)   <span class="c"># sealed, signed, and witnessed by default</span></code></pre>
<div class="callout"><strong>Adapter shortcut:</strong> if you use MCP, LangChain, CrewAI, or Goose, a thin adapter seals on every tool call &mdash; the fields above are what every adapter fills in automatically. See the <a class="ln" href="https://github.com/action-state-group/capsule-emit/tree/main/docs/adapters">capsule-emit adapter docs</a>.</div>

<h2>3. Where it's witnessed</h2>
<p>By default, every <code>seal()</code> folds the capsule into your ledger's checkpoint/witness stream: roughly every 100 entries (or 15 minutes), a signed checkpoint of the whole ledger &mdash; never capsule content &mdash; is registered with the public witness, a SCITT Transparency Service, at <a class="ln" href="https://witness.agentactioncapsule.org">witness.agentactioncapsule.org</a>, no signup, no key. Set <code>CAPSULE_WITNESS=off</code> (or pass <code>witness=False</code>) to seal fully offline; set <code>CAPSULE_WITNESS_URL</code> or pass <code>witness_url=&hellip;</code> to point at your own Transparency Service. The older per-capsule <em>anchor</em> channel (<code>cap.anchored</code>, <code>anchor=True</code> / <code>CAPSULE_ANCHOR=legacy-on</code>) is a legacy, explicit opt-in kept only as a rollback path &mdash; it has not been the default egress path since 0.5.0. See the <a class="ln" href="https://agentactioncapsule.org/#adopt-ladder">adoption ladder</a> for the full rung-by-rung path.</p>

<h2>4. Verify</h2>
<p>Each <code>seal()</code> also appends the sealed capsule to a local <code>ledger.jsonl</code> by default &mdash; that&rsquo;s the file you verify, offline:</p>
<pre class="code"><code><span class="c"># verify a ledger of sealed capsules, offline &mdash; no keys or network needed</span>
capsule-emit verify --store ledger.jsonl

  <span class="ok">VALID</span>

1/1 <span class="ok">VALID</span></code></pre>
<div class="callout warn"><strong>Two verify surfaces, not one:</strong> <code>agent-action-capsule verify</code> (the spec package's own CLI, bundled as a <code>capsule-emit</code> dependency) checks structural/digest conformance only. <code>capsule-emit verify</code> runs that same check <em>plus</em> the producer-envelope check: a capsule with an altered <code>signature</code> but an otherwise-untouched digest still reads <code>ok</code> under <code>agent-action-capsule verify</code> and fails <code>INVALID</code> under <code>capsule-emit verify</code>. Use <code>capsule-emit verify --store</code> for the full check.</div>
<h2>Adapters: seal from your framework</h2>
<p>You don&rsquo;t have to call <code>seal()</code> by hand. Thin adapters seal one capsule per tool call across the framework you already use &mdash; MCP / any callable (a decorator), LangChain / LangGraph (a callback), CrewAI (a tool wrap), and <strong>Goose</strong> (companion MCP server or <code>@emitter.tool()</code> decorator, verified against Goose v1.39.0). A gateway integration (<strong>agentgateway</strong>) seals at the chokepoint every consequential action flows through &mdash; one policy point instead of N integrations (via the gateway's <code>mcpGuardrails</code> ExtMcp hook). Any custom loop works via one call at the tool boundary. Per-framework guides: <a class="ln" href="https://github.com/action-state-group/capsule-emit/tree/main/docs/adapters">docs/adapters/</a> &mdash; including the <a class="ln" href="https://github.com/action-state-group/capsule-emit/blob/main/docs/adapters/goose.md">Goose extension</a> and the <a class="ln" href="https://github.com/action-state-group/capsule-emit/blob/main/docs/adapters/agentgateway.md">agentgateway adapter</a>.</p>
<div class="callout">Next: <a class="ln" href="/docs/verify-a-capsule.html">verify a capsule</a> in detail &mdash; the hosted verifier, command line, and what each check covers.</div>
""",
)

PAGES["verify-a-capsule"] = dict(
    title="Verify a capsule",
    desc="Verify an Agent Action Capsule three ways: in the browser with the hosted verifier, on the command line, or as a library — all running the same open-source checks.",
    crumb="Guides",
    body="""
<h1>Verify a capsule</h1>
<p class="lede">Anyone holding a capsule or receipt can verify it &mdash; in the browser, on the command line, or as a library. Every path runs the same open-source verifier. The command line checks a ledger &mdash; digests, chain links, and producer signatures; the browser and the library check a receipt &mdash; the signature and the inclusion proof.</p>

<h2>In the browser</h2>
<p>The fastest way to check a single receipt or signed statement is the hosted verifier. Paste a receipt or statement (and a key, if you want the signature checked) and read the verdict and reasons. It is stateless &mdash; nothing you submit is stored.</p>
<div class="callout">Open <a class="ln" href="https://verify.agentactioncapsule.org">verify.agentactioncapsule.org</a>. The page runs the identical library you can install locally; for maximal privacy, verify locally instead.</div>

<h2>On the command line</h2>
<pre class="code"><code>pip install capsule-emit
capsule-emit verify --store ledger.jsonl

  <span class="ok">VALID</span>
  <span class="ok">VALID</span>

2/2 <span class="ok">VALID</span></code></pre>
<p><code>capsule-emit verify</code> recomputes every capsule's digest and chain link with the reference verifier from <code>agent-action-capsule</code> (which ships as a dependency, and whose own <code>agent-action-capsule verify</code> runs that structural check alone) <em>and</em> checks each producer signature it finds. A tampered record prints <code>INVALID</code> and the command exits 1. Neither check needs the network.</p>

<h2>With the Go CLI: <code>capsulectl</code></h2>
<p>If you would rather not run Python, <code>capsulectl</code> is a standalone Go binary (built on <code>capsule-emit-go</code>) that seals and verifies its own artifact records &mdash; it does not read the Python <code>ledger.jsonl</code> above, so use it end to end. Install it with Go 1.27 or later, create a profile that pins the producer's public key, seal a request (format in the <a class="ln" href="https://github.com/action-state-group/capsule-cli#seal-request-and-stored-artifact">capsule-cli README</a>), and verify:</p>
<pre class="code"><code>go install github.com/action-state-group/capsule-cli/cmd/capsulectl@latest
capsulectl key generate --output producer.seed        <span class="c"># prints the public key</span>
capsulectl profile create --name local --type jsonl --jsonl-path ./capsules \\
  --signing-key-file producer.seed --trusted-key PRODUCER_PUBLIC_KEY_HEX
capsulectl seal --profile local --request request.json --output artifact.json
capsulectl verify --profile local --capsule artifact.json

{"capsule_identity":"<span class="ok">passed</span>","producer_signature_and_trust":"<span class="ok">passed</span>",
 "artifacts":{"payload":{"Verified":true},"agent_output":{"Verified":true}}, &hellip;}</code></pre>
<p><code>capsulectl verify</code> recomputes the capsule's identity, checks the producer signature against the key your profile pins, and checks each bound original. A changed byte, or a producer key the profile does not trust, fails the check and the command exits non-zero. No network is needed.</p>

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

TRUST_MAP_CSS = """
.t td:last-child{color:var(--muted,#5b6470);font-size:.95em}
.tm-terms{display:grid;grid-template-columns:max-content 1fr;gap:.35rem 1rem;margin:1rem 0}
.tm-terms dt{font-weight:600}
.tm-terms dd{margin:0}
@media (max-width:560px){.tm-terms{grid-template-columns:1fr;gap:.1rem}.tm-terms dd{margin-bottom:.5rem}}
@media (max-width:560px){
  .t thead{display:none}
  .t,.t tbody,.t tr,.t th,.t td{display:block;width:auto}
  .t tr{padding:10px 0;border-top:1px solid var(--line,#e3e6ea)}
  .t td::before{content:attr(data-label);display:block;font-family:var(--mono);font-size:11px;letter-spacing:.5px;text-transform:uppercase;color:var(--muted,#5b6470)}
}
"""

PAGES["trust-map"] = dict(
    title="Trust map: what each check shows",
    desc="A plain-words map of the checks behind a record: what each one shows, what it does not show, and what it means when a view says a thing is not checked here.",
    crumb="Concepts",
    css=TRUST_MAP_CSS,
    body=f"""
<h1>Trust map: what each check shows</h1>
<p class="lede">Each check answers one narrow question. A pass on one says nothing about the others. This page lists the checks behind a record, what each one shows, and what it does not show.</p>

<p>If you followed a link from an evidence view, such as a node's Evidence tab in the <a class="ln" href="/docs/case-study-mesh-llm.html">Mesh-LLM case study</a>, this is the key to it. The <em>In the Mesh-LLM view</em> column says where that view gets each answer: a check it runs on your machine, or a state it only reads and marks <em>not checked here</em>.</p>

<h2>The checks</h2>
<table class="t">
  <thead><tr><th>Check</th><th>What it shows</th><th>What it does not show</th><th>In the Mesh-LLM view</th></tr></thead>
  <tbody>
    <tr id="content-binding"><th>Content binding</th>
      <td data-label="What it shows">The record's fingerprint is recomputed from its bytes and matches the id it was sealed under. Change one byte and it no longer matches.</td>
      <td data-label="What it does not show">That what the record says is true. Who wrote it.</td>
      <td data-label="In the Mesh-LLM view">Checked on this machine, for your records and for theirs.</td></tr>
    <tr id="signature"><th>Signature</th>
      <td data-label="What it shows">Proves the holder of a key signed this record's id.</td>
      <td data-label="What it does not show">Who holds the key, or that the named machine did the work. For the other side's record, the key is the one they announce: their claim, not an identity anyone else vouched for.</td>
      <td data-label="In the Mesh-LLM view">Checked on this machine, or by your node when their record arrives.</td></tr>
    <tr id="inclusion"><th>Inclusion in a signed checkpoint</th>
      <td data-label="What it shows">Proves the record sits in the log under that checkpoint's root.</td>
      <td data-label="What it does not show">That the log holds nothing else, or that anyone outside the log's operator holds the checkpoint. A count of records a checkpoint covers is only a number the node reports.</td>
      <td data-label="In the Mesh-LLM view">Checked by your node for their record before it keeps a citation. For your own records, the view shows the node's coverage count.</td></tr>
    <tr id="checkpoint-signature"><th>Checkpoint signature</th>
      <td data-label="What it shows">Proves the log's key signed that checkpoint: that root, at that size.</td>
      <td data-label="What it does not show">That the operator showed everyone the same checkpoint. Only someone outside, such as a Transparency Service that registered the checkpoint, can catch two different versions.</td>
      <td data-label="In the Mesh-LLM view">Checked by your node, under the key on their record, together with inclusion.</td></tr>
    <tr id="continuity"><th>Continuity</th>
      <td data-label="What it shows">When checked with a consistency proof, it proves each checkpoint builds on the one before, so an earlier entry was not rewritten or dropped between them.</td>
      <td data-label="What it does not show">That every action was recorded. A log can stay consistent and still leave an action out.</td>
      <td data-label="In the Mesh-LLM view">Not checked here. The view reads the node's status.</td></tr>
    <tr id="witness-receipt"><th>Witness receipt (a SCITT Receipt)</th>
      <td data-label="What it shows">A Transparency Service you don't run registered your checkpoint in its own log, so a later rewrite would show to others. The Receipt proves the checkpoint is in that log, not that the service agrees with it. The service sees checkpoints, never records or text.</td>
      <td data-label="What it does not show">That the records are true, or that they are all there. It says nothing about the content of any record.</td>
      <td data-label="In the Mesh-LLM view">Not checked here. The view reads whether a receipt exists; it does not check the receipt, or the witnesses a checkpoint lists.</td></tr>
    <tr id="matching-record"><th>The other side's matching record</th>
      <td data-label="What it shows">Both sides sealed their own record of one exchange, and the two agree: the same request and answer fingerprints, the same serving machine, the same model weights fingerprint. Two signed records that disagree are a signed disagreement.</td>
      <td data-label="What it does not show">That the answer is right. That the weights named are the ones that ran; the check compares fingerprints each side states. A model name alone never counts as a match.</td>
      <td data-label="In the Mesh-LLM view">Checked on this machine. The view marks the serving-machine comparison as provisional.</td></tr>
    <tr id="twin-referee"><th>Twin plus referee</th>
      <td data-label="What it shows">The same request went to two machines and both answers were kept, with the settings each was asked to use, so they can be compared side by side. A referee can compare the two and seal a verdict.</td>
      <td data-label="What it does not show">Which answer is right. A verdict that is not signed is a statement, not something you can check.</td>
      <td data-label="In the Mesh-LLM view">The two answers are shown side by side. Verdicts: not checked here.</td></tr>
  </tbody>
</table>

<h2 id="not-checked-here">What &ldquo;not checked here&rdquo; means</h2>
<p><em>Not checked here</em> means the view displays a state it read from somewhere else and did not verify itself. It is not a failure and not a pass. It tells you where the trust sits: with whoever reported that state.</p>
<p>In the Mesh-LLM view, these are read and not checked:</p>
<ul>
  <li>witness receipts, and the witnesses a checkpoint lists;</li>
  <li>continuity;</li>
  <li>twin verdicts;</li>
  <li>the link between a node and its owner, which the node reports about itself;</li>
  <li>peer names, which each peer chooses.</li>
</ul>
<p>To check a record yourself, use a verifier you choose: <a class="ln" href="/docs/verify-a-capsule.html">Verify a capsule</a> runs the same checks in the browser, on the command line, or as a library. A view that cannot run a check should say so rather than show a pass.</p>

<h2 id="terms">Terms, one line each</h2>
<dl class="tm-terms">
  <dt>Record</dt><dd>One sealed entry: a capsule.</dd>
  <dt>Fingerprint</dt><dd>A SHA-256 digest of some bytes; any change gives a different one.</dd>
  <dt>Signature</dt><dd>A COSE signature over a record's id, made with one key.</dd>
  <dt>Log</dt><dd>A node's records, in order, append-only.</dd>
  <dt>Checkpoint</dt><dd>A signed snapshot of a log: its root and size.</dd>
  <dt>Inclusion proof</dt><dd>The path that places one record under a checkpoint's root.</dd>
  <dt>Consistency proof</dt><dd>The path that shows a later checkpoint extends an earlier one.</dd>
  <dt>Witness</dt><dd>A SCITT Transparency Service you don't run that registers your checkpoints under a <a class="ln" href="https://github.com/action-state-group/capsule-anchor/blob/main/OPERATOR_GUIDE.md#registration-policy">published consistency policy</a>; you can register with several.</dd>
  <dt>The other side</dt><dd>The machine you dealt with in an exchange, which keeps its own record of it.</dd>
  <dt>Referee</dt><dd>A third party that compares two answers to the same request and seals a verdict.</dd>
  <dt>Checked on this machine</dt><dd>Recomputed where you are reading it, from the bytes.</dd>
  <dt>Not checked here</dt><dd>Read from elsewhere and shown as reported, not verified by this view.</dd>
</dl>
<p>Fuller definitions are in the <a class="ln" href="/docs/glossary.html">glossary</a>. The threat model behind the Mesh-LLM checks is in <a class="ln" href="https://github.com/action-state-group/capsule-emit-mesh/blob/main/docs/TRUST-MODEL.md">A trust model for strangers on a mesh &#x2197;</a>.</p>
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
    <tr><th>2 · Privileged read</th><td>the action <strong>reads sensitive data</strong> (PII/PHI/cardholder data) even though it's a "read." This signal is evaluated <em>by the producer</em>, where data is classified — not at the gateway.</td></tr>
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
<p>A capsule binds external evidence into its verifiable trail through its <code>references</code> array: each entry commits the <strong>digest</strong> of another artifact — an authorization grant, a policy decision, an upstream receipt — without copying or exposing it, and says why it is cited. The verifier checks the binding; the referenced data stays where it lives. <code>chain</code> is a different field: it links a capsule only to the same producer's previous capsule, such as a confirmation to the action it confirms (see <a class="ln" href="/docs/what-is-a-capsule.html">what is a capsule</a>).</p>
<pre class="code"><code>{
  "action_id": "po-0047-submit",
  "operator": "acme-co",
  "chain": {                            // same producer, same stream only
    "parent_capsule_id": "3c1e…a07b",
    "relation": "follows"
  },
  "references": [{                      // anything outside the stream
    "type": "…",                        // a registered artifact type
    "digest_alg": "sha-256",
    "digest": "9f2a…c14",               // digest of the grant
    "citation_purpose": "ran_under"     // the authority it ran under
  }]
}</code></pre>
<p>Illustrative: the capsule carries only the <em>digest</em> of the authorization grant, policy decision, or identity credential — never its contents. A verifier recomputes that digest from the artifact you (or a partner layer) present, and confirms the binding. Both vocabularies &mdash; <code>chain.relation</code> and <code>citation_purpose</code> &mdash; are registries defined in the spec; to register a value for your layer, <a class="ln" href="https://github.com/action-state-group/agent-action-capsule/issues">open an issue on the spec</a>.</p>
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

<h2>The four-leg accountability picture</h2>
<p>A fuller framing of agent accountability splits into four questions: <strong>CAN</strong> (was the action permitted? — authorization), <strong>WHO</strong> (which accountable human authorized this exact action? — named-human authorization), <strong>WHAT</strong> (what did the agent do? — the Agent Action Capsule), and <strong>AUDIT</strong> (did the runtime enforce correctly? — observability and gating). Each leg answers its own slice; together they span the accountability gap.</p>
<p><strong>The capsule is the WHAT leg.</strong> The four legs compose by a shared action digest: <code>subject_digest&nbsp;=&nbsp;SHA-256(JCS(action))</code> — any layer that commits to the same action digest binds itself to the same event, so the capsule's anchored record ties to the authorization grant (CAN), the named human's authorization receipt (WHO), and the runtime gate's decision (AUDIT) without any layer absorbing the others.</p>
<div class="callout deeper">The <strong>CAN/WHO/WHAT/AUDIT composition model</strong> — how independently-verifiable records join on a shared action digest — is laid out on the <a class="ln" href="/#compose">Standard's Composition section</a>. Underneath it, the <strong>Canonical Payload Binding (CPB)</strong> is the small companion spec that lets every record compute the same digest: it defines how a payload binds to a SCITT receipt and how a payload class declares and resolves its canonical form, so any conforming profile composes with a capsule without a custom adapter. CPB has its own site and registry: <a class="ln" href="https://canonicalpayloadbinding.org/">canonicalpayloadbinding.org &#x2197;</a>.</div>
""",
)

PAGES["witness-anywhere"] = dict(
    title="Witness anywhere — what leaves your walls",
    desc="When you witness a capsule, only a digest and a timestamp leave — never prompts, payloads, or PII. Witness at the public log, run your own witness in the region you choose, or self-host inside your VPC where the hash never leaves.",
    crumb="Concepts",
    body="""
<h1>Witness anywhere — what leaves your walls</h1>
<p class="lede">Witnessing means registering with a SCITT Transparency Service: its Receipt proves a capsule was included in an append-only log. The only thing that travels to the log is a <strong>digest (a hash) and a timestamp</strong> — never your prompts, payloads, reasoning, or PII.</p>

<h2>What leaves your walls</h2>
<p>A capsule is <a class="ln" href="/docs/what-is-a-capsule.html">content-private by construction</a>: it carries digests of inputs and outputs, not the raw values. When it's witnessed, the log receives the statement's commitment — a hash — plus a timestamp. The raw content stays where you keep it, under your control. The public log stores <em>a commitment you can check</em>, not your data.</p>

<h2>Witness anywhere — three options</h2>
<table class="t">
  <thead><tr><th>Where you witness</th><th>What it gives you</th><th>What leaves your environment</th></tr></thead>
  <tbody>
    <tr><th>The public log</th><td>zero-setup existence proofs on a shared, open log (<code>witness.agentactioncapsule.org</code>)</td><td>a digest + a timestamp</td></tr>
    <tr><th>Your own witness, in the region you choose</th><td>residency / jurisdiction control (e.g. EU, Singapore) by running the open witness log where you need it</td><td>a digest + a timestamp, kept in your jurisdiction</td></tr>
    <tr><th>Your own witness, inside your VPC</th><td>full control — self-host the container with your own storage</td><td>nothing — the hash never leaves your environment</td></tr>
  </tbody>
</table>
<p>The capsule <strong>does not depend on any one Transparency Service</strong> (it makes no claim about the log's <a class="ln" href="/docs/verifiable-data-structures.html">verifiable-data-structure</a>): the same statement verifies whichever log you choose, so you can move, or register with more than one, without changing the record. This is also true of vendor lock-in more broadly: no vendor, including us, controls where your capsules get registered.</p>

<h2>What a digest hides — and what it doesn't</h2>
<p>A digest hides a value only when that value is hard to guess. A high-entropy input (a full prompt, a document, a key) is safe. But a <em>low-entropy</em> value — a short dollar amount, a yes/no disposition, an ID from a known list — can be recovered by hashing candidate values until one matches. For those fields, <strong>salt before hashing</strong> with a random salt that stays secret, and disclose it only together with the value when you choose to reveal it. A published salt does not help: anyone can hash the candidates with it. And note the capsule commits some metadata in the clear — the action type and disposition — so &ldquo;content-private&rdquo; means your <em>payloads</em> stay private, not that the capsule reveals nothing about what kind of action occurred.</p>

<div class="callout">The privacy promise, in one line: <strong>we verify; we store nothing of yours but a commitment you can check</strong> — and, for guessable values, salt before you commit them.</div>

<div class="callout deeper">Vocabulary check: <a class="ln" href="/docs/translation.html">see the word-for-word translation</a> across dev / auditor / spec registers — including why the service is a &ldquo;witness&rdquo; while the spec's assurance tier is still called <code>anchored</code> (see the <a class="ln" href="/docs/glossary.html">glossary</a>).</div>
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
    <tr><th>Vendor-neutral</th><td>No required product; the specification favors no vendor. Any party can implement, run, and witness — including in their own environment.</td></tr>
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
<p>The SCITT Architecture is published as <a class="ln" href="https://www.rfc-editor.org/rfc/rfc9943">RFC&nbsp;9943</a> and COSE Receipts as <a class="ln" href="https://www.rfc-editor.org/rfc/rfc9942">RFC&nbsp;9942</a>; related specifications, such as the CCF receipt profile and SCRAPI, are still Internet-Drafts. This profile is built to <strong>track them</strong>: as those specifications advance, the profile and its reference implementations will be updated to conform to the final versions, and any breaking changes will be versioned and documented. Building on it today should not strand you when the standard lands.</p>

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
<p>The open project is the <strong>record layer</strong>: the profile, the producer (with example constraint manifests), the verifier, and the witness. Acting on declared constraints at runtime — <em>enforcement</em> — is a separate concern that composes with a policy gateway. The capsule records what happened; it does not gate. We call that boundary out so the boundary between the open record layer and runtime enforcement is explicit, not implied.</p>

<div class="callout">Want to help shape it? Open an issue or PR on <a class="ln" href="https://github.com/action-state-group">GitHub</a>, comment on the <a class="ln" href="https://datatracker.ietf.org/doc/draft-mih-scitt-agent-action-capsule/">draft</a>, or write <a class="ln" href="mailto:spec@actionstate.ai">spec@actionstate.ai</a>. Join the conversation on <a class="ln" href="https://github.com/action-state-group">GitHub</a>.</div>
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
    <tr><th>SCITT</th><td>Supply Chain Integrity, Transparency, and Trust &mdash; the IETF working group and architecture for registering signed statements in transparency services. Its Architecture is published as <a class="ln" href="https://www.rfc-editor.org/rfc/rfc9943">RFC&nbsp;9943</a> and COSE Receipts as <a class="ln" href="https://www.rfc-editor.org/rfc/rfc9942">RFC&nbsp;9942</a>; some related specifications, such as the CCF receipt profile, are still Internet-Drafts.</td></tr>
    <tr><th>SCITT profile</th><td>A specialization of the general SCITT signed-statement format for a domain. The Agent Action Capsule is the profile for <em>agent actions</em> &mdash; it builds on SCITT/COSE and interoperates with any SCITT transparency service, rather than being a separate standard.</td></tr>
    <tr><th>COSE</th><td>CBOR Object Signing and Encryption &mdash; the signature format used for statements and receipts.</td></tr>
    <tr><th>COSE_Sign1</th><td>A single-signer COSE structure: one signature over a protected header and payload. The envelope an Agent Action Capsule uses.</td></tr>
    <tr><th>Signed Statement</th><td>A COSE_Sign1 claim about something &mdash; here, an agent action. The capsule is a profiled Signed Statement.</td></tr>
    <tr><th>Agent Action Capsule</th><td>The profile in this project: a Signed Statement over <code>application/agent-action-capsule+json</code> committing to an action and its input/output digests.</td></tr>
    <tr><th>Transparency Service</th><td>A service that registers Signed Statements into an append-only log, issues receipts, and publishes tree heads and proofs.</td></tr>
    <tr><th>Transparency log</th><td>The public, append-only log a Transparency Service maintains. It is publicly readable &mdash; anyone can fetch its entries and verify any one of them; nothing is taken on trust.</td></tr>
    <tr><th>Ledger</th><td>Your <em>local</em> append-only trail of capsules (e.g. <code>ledger.jsonl</code>) &mdash; distinct from the public transparency log. The ledger is yours; the transparency log is the shared, witnessed record.</td></tr>
    <tr><th>Receipt</th><td>A signed proof, returned by a transparency service, that a statement was included in its log. Verifiable offline against the log key.</td></tr>
    <tr><th>VDS</th><td>Verifiable Data Structure &mdash; how a log proves inclusion and consistency. <code>vds=1</code> is RFC9162_SHA256; <code>vds=2</code> is CCF (ccf.v1).</td></tr>
    <tr><th>Inclusion proof</th><td>Evidence that a specific leaf is part of the log at a given size &mdash; answers &ldquo;is my record in the log?&rdquo;</td></tr>
    <tr><th>Consistency proof</th><td>Evidence that one tree head is an append-only extension of an earlier one &mdash; answers &ldquo;did the log stay honest?&rdquo;</td></tr>
    <tr><th>STH</th><td>Signed Tree Head &mdash; the log's current Merkle root and size, signed, so verifiers and auditors can pin its state.</td></tr>
    <tr><th>Merkle tree</th><td>A hash tree whose root commits to every leaf; the structure behind RFC&nbsp;9162 inclusion and consistency proofs.</td></tr>
    <tr><th>RFC 9162</th><td>Certificate Transparency 2.0 &mdash; the published RFC whose SHA-256 Merkle proofs back <code>vds=1</code>.</td></tr>
    <tr><th>CCF</th><td>Confidential Consortium Framework &mdash; an open-source confidential ledger framework whose receipts back <code>vds=2</code>.</td></tr>
    <tr id="disposition"><th>Disposition</th><td>How an action was disposed, recorded in every capsule &mdash; refusals included. Its <code>verdict_class</code> is one of the spec's registered values: <code>executed</code>, <code>blocked</code>, <code>hitl_dispatched</code>, <code>denied</code>, <code>timeout</code>, <code>errored</code>, <code>engine_failure</code>, <code>deferred</code>, <code>needs_decision</code>, <code>expired</code>, <code>escalated</code>, <code>resolved</code>, <code>epoch_boundary</code>. Its <code>decision</code> is <code>accept</code>, <code>reject</code>, <code>needs_input</code> or <code>deferred</code>, and its <code>approver</code> is <code>human</code>, <code>policy</code> or <code>counterparty</code>. <em>Confirmed</em> is not a verdict: it is an effect status (the result was observed), and <code>confirms</code> is a chain relation. This is the one list the site uses.</td></tr>
    <tr><th>Witness vs <code>anchored</code></th><td>On this site a <strong>witness</strong> is a SCITT Transparency Service that registers checkpoints under a <a class="ln" href="https://github.com/action-state-group/capsule-anchor/blob/main/OPERATOR_GUIDE.md#registration-policy">published consistency policy</a>: when a new checkpoint carries a consistency proof, it registers it only if the proof shows it extends the last checkpoint it registered for the same log, and it returns a Receipt. The Receipt proves the checkpoint is in the service's log. It does not mean the service agrees with the records. RFC 9943 has no role called &ldquo;witness&rdquo;; the word is this site's name for the service, and &ldquo;witnessed&rdquo; means registered with one. <code>anchored</code> is the specification's name for an assurance tier: a record whose chain has been registered with a transparency log, backed by a receipt a verifier has checked. Same event, two vocabularies. The site avoids &ldquo;anchor&rdquo; as a verb because it collides with &ldquo;trust anchor&rdquo;. The service's source is still named <code>capsule-anchor</code>.</td></tr>
  </tbody>
</table>
""",
)

# Docs index (overview)
INDEX_BODY = f"""
<h1>Documentation</h1>
<p class="lede">Concepts and short guides for the Agent Action Capsule &mdash; the open profile for verifiable records of what an AI agent did, and the transparency layer it builds on.</p>

<div class="idx-group">
  <h2>Start here</h2>
  <p class="note">Read a ledger before you write one. Steps 1 and 2 install nothing &mdash; you read two real ledgers and check them yourself; step 3 is where you produce one.</p>
  <div class="cards">
    <a class="dcard" href="{CE_DOCS}/tutorials/see-a-ledger.md"><div class="n">1 &middot; See a ledger &#x2197;</div><div class="d">Two real agent runs shown beside the capsules that record them &mdash; the run you hold vs. the ledger anyone can check. Nothing to install.</div></a>
    <a class="dcard" href="/docs/verify-a-capsule.html"><div class="n">2 &middot; Verify one yourself</div><div class="d">Signature, then inclusion proof &mdash; from the bytes alone, in the browser, on the command line, or as a library.</div></a>
    <a class="dcard" href="/docs/quickstart.html"><div class="n">3 &middot; Produce your own</div><div class="d">Now seal a capsule with one <code>seal()</code> call, witness it, and verify it. Copy-paste-runnable.</div></a>
  </div>
</div>

{index_groups_html()}
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
            render(slug, p["title"], p["desc"], p["crumb"], body, css=p.get("css", "")), encoding="utf-8")
        n += 1
    # hand-written pages: splice in the same header, sidebar, prev/next and footer
    for rel, (active, key) in HAND_PAGES.items():
        rechrome(rel, active, key)
    print(f"wrote {n} files to {OUT}; re-chromed {len(HAND_PAGES)} hand-written pages")


if __name__ == "__main__":
    main()
